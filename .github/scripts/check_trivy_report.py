#!/usr/bin/env python3
"""Fail closed on HIGH/CRITICAL Trivy findings, with opt-in exact image risks."""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlsplit

BLOCKING_SEVERITIES = {"HIGH", "CRITICAL"}
KNOWN_SEVERITIES = {"UNKNOWN", "LOW", "MEDIUM", *BLOCKING_SEVERITIES}
ALLOWED_DISTRO_PREFIX = "debian-13."
MAX_ACCEPTANCE_DAYS = 30
EXCEPTION_KEYS = {
    "id",
    "packages",
    "distro_prefix",
    "owner",
    "reviewed_on",
    "expires_on",
    "rationale",
    "source",
}


class PolicyError(ValueError):
    """The optional accepted-risk policy is invalid or expired."""


@dataclass(frozen=True)
class AcceptedRisk:
    vulnerability_id: str
    package: str
    installed_version: str
    distro_prefix: str
    owner: str
    expires_on: str

    @property
    def key(self) -> tuple[str, str, str, str]:
        return (
            self.vulnerability_id,
            self.package,
            self.installed_version,
            self.distro_prefix,
        )


@dataclass(frozen=True)
class Evaluation:
    blocking_findings: list[str]
    accepted_findings: list[str]


def _parse_date(value: object, label: str) -> date:
    if not isinstance(value, str):
        raise PolicyError(f"Accepted-risk {label} must be an ISO date.")
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise PolicyError(f"Accepted-risk {label} must be an ISO date.") from error


def validate_accepted_risks(policy: object, today: date | None = None) -> list[AcceptedRisk]:
    """Validate a strict, short-lived policy and flatten it to exact tuples."""
    if not isinstance(policy, dict) or set(policy) != {"schema_version", "exceptions"}:
        raise PolicyError("Accepted-risk policy has an invalid top-level schema.")
    if type(policy.get("schema_version")) is not int or policy.get("schema_version") != 1:
        raise PolicyError("Accepted-risk policy schema_version must be 1.")
    entries = policy.get("exceptions")
    if not isinstance(entries, list):
        raise PolicyError("Accepted-risk policy exceptions must be a list.")

    current_date = today or date.today()
    flattened: list[AcceptedRisk] = []
    seen: set[tuple[str, str, str, str]] = set()
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != EXCEPTION_KEYS:
            raise PolicyError("Accepted-risk exception has an invalid schema.")
        vulnerability_id = entry.get("id")
        if not isinstance(vulnerability_id, str) or not re.fullmatch(
            r"CVE-\d{4}-\d{4,}", vulnerability_id
        ):
            raise PolicyError("Accepted-risk exception must name one exact CVE ID.")
        distro_prefix = entry.get("distro_prefix")
        if distro_prefix != ALLOWED_DISTRO_PREFIX:
            raise PolicyError("Accepted-risk exception has an unsupported distro scope.")
        owner = entry.get("owner")
        rationale = entry.get("rationale")
        source = entry.get("source")
        if not isinstance(owner, str) or not owner.strip() or len(owner) > 100:
            raise PolicyError("Accepted-risk exception must name an owner.")
        if not isinstance(rationale, str) or len(rationale.strip()) < 20 or len(rationale) > 1000:
            raise PolicyError("Accepted-risk exception must include a specific rationale.")
        if not isinstance(source, str):
            raise PolicyError("Accepted-risk exception must link to an HTTPS advisory.")
        parsed_source = urlsplit(source)
        if (
            parsed_source.scheme != "https"
            or parsed_source.hostname != "security-tracker.debian.org"
            or parsed_source.path != f"/tracker/{vulnerability_id}"
        ):
            raise PolicyError("Accepted-risk exception must link to its exact Debian advisory.")
        reviewed_on = _parse_date(entry.get("reviewed_on"), "reviewed_on")
        expires_on = _parse_date(entry.get("expires_on"), "expires_on")
        if reviewed_on > current_date:
            raise PolicyError("Accepted-risk review date cannot be in the future.")
        if expires_on < current_date:
            raise PolicyError("Accepted-risk exception has expired.")
        if not 1 <= (expires_on - reviewed_on).days <= MAX_ACCEPTANCE_DAYS:
            raise PolicyError("Accepted-risk exception must expire within 30 days of review.")

        packages = entry.get("packages")
        if not isinstance(packages, dict) or not packages:
            raise PolicyError("Accepted-risk exception must list exact package versions.")
        for package, version in packages.items():
            if (
                not isinstance(package, str)
                or not re.fullmatch(r"[a-z0-9][a-z0-9+.-]*", package)
                or not isinstance(version, str)
                or not re.fullmatch(r"[A-Za-z0-9.+:~_-]+", version)
            ):
                raise PolicyError("Accepted-risk package names and versions must be exact.")
            risk = AcceptedRisk(
                vulnerability_id=vulnerability_id,
                package=package,
                installed_version=version,
                distro_prefix=distro_prefix,
                owner=owner.strip(),
                expires_on=expires_on.isoformat(),
            )
            if risk.key in seen:
                raise PolicyError("Accepted-risk policy contains a duplicate tuple.")
            seen.add(risk.key)
            flattened.append(risk)
    return flattened


def evaluate_policy(
    report: object,
    accepted_policy: object | None = None,
    today: str | date | None = None,
) -> Evaluation:
    """Return sanitized blockers and explicit records for exact accepted findings."""
    if (
        not isinstance(report, dict)
        or "Results" not in report
        or not isinstance(report.get("Results"), list)
    ):
        raise ValueError("Trivy report has an invalid schema.")
    if isinstance(today, str):
        try:
            today = date.fromisoformat(today)
        except ValueError as error:
            raise ValueError("Evaluation date must be an ISO date.") from error
    risks = validate_accepted_risks(accepted_policy, today) if accepted_policy is not None else []
    by_key = {risk.key: risk for risk in risks}
    matched: set[tuple[str, str, str, str]] = set()
    blocking: list[str] = []
    accepted: list[str] = []

    for result in report.get("Results") or []:
        if not isinstance(result, dict):
            raise ValueError("Trivy report contains an invalid result entry.")
        target = str(result.get("Target") or "unknown target")
        for key, label, identifier_key in (
            ("Vulnerabilities", "vulnerability", "VulnerabilityID"),
            ("Misconfigurations", "misconfiguration", "ID"),
            ("Secrets", "secret", "RuleID"),
        ):
            findings = result.get(key, [])
            if not isinstance(findings, list):
                raise ValueError("Trivy report contains an invalid finding list.")
            for finding in findings:
                if not isinstance(finding, dict):
                    raise ValueError("Trivy report contains an invalid finding entry.")
                raw_severity = finding.get("Severity")
                if not isinstance(raw_severity, str):
                    raise ValueError("Trivy report finding has no valid severity.")
                severity = raw_severity.upper()
                if severity not in KNOWN_SEVERITIES:
                    raise ValueError("Trivy report finding has no valid severity.")
                if severity not in BLOCKING_SEVERITIES:
                    continue
                identifier = str(finding.get(identifier_key) or "unknown")
                accepted_risk = (
                    _matching_risk(result, finding, by_key) if key == "Vulnerabilities" else None
                )
                if accepted_risk:
                    matched.add(accepted_risk.key)
                    accepted.append(
                        f"{accepted_risk.vulnerability_id} {accepted_risk.package} "
                        f"{accepted_risk.installed_version} (owner: {accepted_risk.owner}, "
                        f"expires: {accepted_risk.expires_on})"
                    )
                    continue
                start_line = finding.get("StartLine")
                location = f"{target}:{start_line}" if start_line else target
                blocking.append(f"{severity} {label} {identifier} at {location}")

    for risk in risks:
        if risk.key not in matched:
            blocking.append(
                f"policy error: unused accepted-risk tuple {risk.vulnerability_id} {risk.package}"
            )
    return Evaluation(blocking, accepted)


def _matching_risk(
    result: dict[str, Any],
    finding: dict[str, Any],
    by_key: dict[tuple[str, str, str, str], AcceptedRisk],
) -> AcceptedRisk | None:
    if result.get("Type") != "debian" or result.get("Class") != "os-pkgs":
        return None
    identifier = finding.get("PkgIdentifier")
    if not isinstance(identifier, dict):
        return None
    purl = identifier.get("PURL")
    if not isinstance(purl, str):
        return None
    parsed_purl = urlsplit(purl)
    path_parts = parsed_purl.path.split("/")
    if len(path_parts) != 3 or path_parts[:2] != ["deb", "debian"]:
        return None
    package_reference = path_parts[2]
    package_from_purl, separator, encoded_version = package_reference.partition("@")
    query = parse_qs(parsed_purl.query)
    distro_values = query.get("distro", [])
    epoch_values = query.get("epoch", [])
    purl_version = unquote(encoded_version) if separator else ""
    if epoch_values:
        if len(epoch_values) != 1 or not re.fullmatch(r"\d+", epoch_values[0]):
            return None
        epoch = int(epoch_values[0])
        if epoch:
            purl_version = f"{epoch}:{purl_version}"
    if len(distro_values) != 1 or not distro_values[0].startswith(ALLOWED_DISTRO_PREFIX):
        return None
    package = finding.get("PkgName")
    version = finding.get("InstalledVersion")
    vulnerability_id = finding.get("VulnerabilityID")
    if (
        not all(isinstance(value, str) for value in (package, version, vulnerability_id))
        or parsed_purl.scheme != "pkg"
        or parsed_purl.netloc
        or package_from_purl != package
        or purl_version != version
    ):
        return None
    return by_key.get((vulnerability_id, package, version, ALLOWED_DISTRO_PREFIX))


def policy_findings(report: dict[str, Any]) -> list[str]:
    """Backward-compatible strict evaluation used by simple callers and tests."""
    return evaluate_policy(report).blocking_findings


def main() -> int:
    if len(sys.argv) == 2:
        policy_path: Path | None = None
        report_path = Path(sys.argv[1])
    elif len(sys.argv) == 4 and sys.argv[1] == "--accepted-image-risks":
        policy_path = Path(sys.argv[2])
        report_path = Path(sys.argv[3])
    else:
        print(
            "Usage: check_trivy_report.py [--accepted-image-risks POLICY.json] REPORT.json",
            file=sys.stderr,
        )
        return 2
    try:
        report = json.loads(report_path.read_text())
        accepted_policy = json.loads(policy_path.read_text()) if policy_path else None
        evaluation = evaluate_policy(report, accepted_policy)
    except (OSError, json.JSONDecodeError, PolicyError, ValueError) as error:
        print(f"Trivy policy could not be evaluated ({type(error).__name__}).", file=sys.stderr)
        return 2
    if evaluation.blocking_findings:
        print(f"Trivy policy failed: {len(evaluation.blocking_findings)} blocking finding(s).")
        for finding in evaluation.blocking_findings:
            print(f"- {finding}")
        return 1
    if evaluation.accepted_findings:
        print(
            f"Trivy policy passed with {len(evaluation.accepted_findings)} exact, "
            "temporary accepted-risk finding(s):"
        )
        for finding in evaluation.accepted_findings:
            print(f"- {finding}")
    else:
        print("Trivy policy passed: no HIGH/CRITICAL findings.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
