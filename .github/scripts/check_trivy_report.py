#!/usr/bin/env python3
"""Fail on HIGH/CRITICAL Trivy findings without printing secret matches."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

BLOCKING_SEVERITIES = {"HIGH", "CRITICAL"}


def policy_findings(report: dict[str, Any]) -> list[str]:
    """Return sanitized blocking finding summaries from a Trivy JSON report."""
    blocking: list[str] = []
    for result in report.get("Results") or []:
        target = str(result.get("Target") or "unknown target")
        for key, label, identifier_key in (
            ("Vulnerabilities", "vulnerability", "VulnerabilityID"),
            ("Misconfigurations", "misconfiguration", "ID"),
            ("Secrets", "secret", "RuleID"),
        ):
            for finding in result.get(key) or []:
                severity = str(finding.get("Severity", "")).upper()
                if severity not in BLOCKING_SEVERITIES:
                    continue
                identifier = str(finding.get(identifier_key) or "unknown")
                start_line = finding.get("StartLine")
                location = f"{target}:{start_line}" if start_line else target
                blocking.append(f"{severity} {label} {identifier} at {location}")
    return blocking


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: check_trivy_report.py REPORT.json", file=sys.stderr)
        return 2
    try:
        report = json.loads(Path(sys.argv[1]).read_text())
    except (OSError, json.JSONDecodeError) as error:
        print(f"Unable to read Trivy report ({type(error).__name__}).", file=sys.stderr)
        return 2
    findings = policy_findings(report)
    if findings:
        print(f"Trivy policy failed: {len(findings)} HIGH/CRITICAL finding(s).")
        for finding in findings:
            print(f"- {finding}")
        return 1
    print("Trivy policy passed: no HIGH/CRITICAL findings.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
