from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from check_trivy_report import PolicyError, evaluate_policy, policy_findings


class TrivyPolicyTests(unittest.TestCase):
    def test_blocks_high_and_critical_categories_without_printing_secret_matches(self) -> None:
        report = {
            "Results": [
                {
                    "Target": "backend/uv.lock",
                    "Vulnerabilities": [
                        {
                            "Severity": "HIGH",
                            "VulnerabilityID": "CVE-EXAMPLE-1",
                            "FixedVersion": "2.0",
                        },
                        {"Severity": "MEDIUM", "VulnerabilityID": "CVE-EXAMPLE-2"},
                    ],
                    "Misconfigurations": [{"Severity": "CRITICAL", "ID": "DS-EXAMPLE-1"}],
                    "Secrets": [
                        {
                            "Severity": "HIGH",
                            "RuleID": "generic-api-key",
                            "StartLine": 42,
                            "Match": "must-not-appear-in-output",
                        }
                    ],
                }
            ]
        }

        findings = policy_findings(report)

        self.assertEqual(len(findings), 3)
        self.assertTrue(any("CVE-EXAMPLE-1" in finding for finding in findings))
        self.assertTrue(any("DS-EXAMPLE-1" in finding for finding in findings))
        self.assertTrue(any("generic-api-key" in finding for finding in findings))
        self.assertTrue(any(":42" in finding for finding in findings))
        self.assertFalse(any("must-not-appear-in-output" in finding for finding in findings))

    def test_empty_report_passes(self) -> None:
        self.assertEqual(policy_findings({"Results": []}), [])

    def test_missing_results_field_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            evaluate_policy({})

    def test_missing_or_invalid_severity_fails_closed(self) -> None:
        for collection in ("Vulnerabilities", "Misconfigurations", "Secrets"):
            for severity in (None, "", "SEVERE", 5):
                with self.subTest(collection=collection, severity=severity):
                    finding = {"Severity": severity}
                    if severity is None:
                        finding.pop("Severity")
                    with self.assertRaises(ValueError):
                        evaluate_policy({"Results": [{collection: [finding]}]})

    def test_non_list_finding_collection_fails_closed(self) -> None:
        for value in (None, {}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                evaluate_policy({"Results": [{"Vulnerabilities": value}]})

    def test_only_exact_os_package_tuple_is_temporarily_accepted(self) -> None:
        finding = {
            "Severity": "HIGH",
            "VulnerabilityID": "CVE-2026-54369",
            "PkgName": "libacl1",
            "InstalledVersion": "2.3.2-2+b1",
            "PkgIdentifier": {
                "PURL": "pkg:deb/debian/libacl1@2.3.2-2%2Bb1?arch=arm64&distro=debian-13.7"
            },
        }
        report = {
            "Results": [
                {
                    "Target": "blast-ecom-api:production",
                    "Type": "debian",
                    "Class": "os-pkgs",
                    "Vulnerabilities": [finding],
                }
            ]
        }
        policy = self.acceptance_policy()

        evaluation = evaluate_policy(report, policy, today="2026-10-04")

        self.assertEqual(evaluation.blocking_findings, [])
        self.assertEqual(
            evaluation.accepted_findings,
            ["CVE-2026-54369 libacl1 2.3.2-2+b1 (owner: platform, expires: 2026-11-03)"],
        )

    def test_new_package_version_remains_blocking_and_marks_exception_stale(self) -> None:
        report = self.os_report("CVE-2026-54369", "libacl1", "2.3.2-2+b2", "debian-13.7")

        evaluation = evaluate_policy(report, self.acceptance_policy(), today="2026-10-04")

        self.assertEqual(len(evaluation.blocking_findings), 2)
        self.assertIn("CVE-2026-54369", evaluation.blocking_findings[0])
        self.assertIn("unused accepted-risk tuple", evaluation.blocking_findings[1])

    def test_other_distribution_or_result_class_remains_blocking(self) -> None:
        for distro, result_class in (("debian-14.0", "os-pkgs"), ("debian-13.7", "lang-pkgs")):
            with self.subTest(distro=distro, result_class=result_class):
                report = self.os_report(
                    "CVE-2026-54369", "libacl1", "2.3.2-2+b1", distro, result_class
                )
                evaluation = evaluate_policy(report, self.acceptance_policy(), today="2026-10-04")
                self.assertEqual(len(evaluation.blocking_findings), 2)

    def test_package_name_must_match_the_package_url(self) -> None:
        report = self.os_report("CVE-2026-54369", "libacl1", "2.3.2-2+b1", "debian-13.7")
        report["Results"][0]["Vulnerabilities"][0]["PkgIdentifier"]["PURL"] = (
            "pkg:deb/debian/libuuid1@2.3.2-2%2Bb1?arch=arm64&distro=debian-13.7"
        )

        evaluation = evaluate_policy(report, self.acceptance_policy(), today="2026-10-04")

        self.assertEqual(len(evaluation.blocking_findings), 2)

    def test_extra_package_url_path_components_remain_blocking(self) -> None:
        report = self.os_report("CVE-2026-54369", "libacl1", "2.3.2-2+b1", "debian-13.7")
        report["Results"][0]["Vulnerabilities"][0]["PkgIdentifier"]["PURL"] = (
            "pkg:deb/debian/unexpected/libacl1@2.3.2-2%2Bb1?arch=arm64&distro=debian-13.7"
        )

        evaluation = evaluate_policy(report, self.acceptance_policy(), today="2026-10-04")

        self.assertEqual(len(evaluation.blocking_findings), 2)

    def test_package_version_must_match_the_package_url(self) -> None:
        report = self.os_report("CVE-2026-54369", "libacl1", "2.3.2-2+b1", "debian-13.7")
        report["Results"][0]["Vulnerabilities"][0]["PkgIdentifier"]["PURL"] = (
            "pkg:deb/debian/libacl1@2.3.2-2%2Bb0?arch=arm64&distro=debian-13.7"
        )

        evaluation = evaluate_policy(report, self.acceptance_policy(), today="2026-10-04")

        self.assertEqual(len(evaluation.blocking_findings), 2)

    def test_debian_epoch_is_reconstructed_from_purl_query(self) -> None:
        report = self.os_report("CVE-2026-76642", "bsdutils", "1:2.41.5-0+deb13u1", "debian-13.7")
        report["Results"][0]["Vulnerabilities"][0]["PkgIdentifier"]["PURL"] = (
            "pkg:deb/debian/bsdutils@2.41.5-0%2Bdeb13u1?arch=arm64&distro=debian-13.7&epoch=1"
        )
        policy = {
            "schema_version": 1,
            "exceptions": [
                {
                    "id": "CVE-2026-76642",
                    "packages": {"bsdutils": "1:2.41.5-0+deb13u1"},
                    "distro_prefix": "debian-13.",
                    "owner": "platform",
                    "reviewed_on": "2026-10-04",
                    "expires_on": "2026-11-03",
                    "rationale": "Debian tracker exception test for an epoch-bearing package.",
                    "source": "https://security-tracker.debian.org/tracker/CVE-2026-76642",
                }
            ],
        }

        evaluation = evaluate_policy(report, policy, today="2026-10-04")

        self.assertEqual(evaluation.blocking_findings, [])
        self.assertEqual(len(evaluation.accepted_findings), 1)

    def test_expired_or_broad_policy_fails_closed(self) -> None:
        with self.assertRaises(PolicyError):
            evaluate_policy({"Results": []}, self.acceptance_policy(), today="2026-11-04")

        policy = self.acceptance_policy()
        policy["exceptions"][0]["packages"]["*"] = "*"
        with self.assertRaises(PolicyError):
            evaluate_policy({"Results": []}, policy, today="2026-10-04")

        policy = self.acceptance_policy()
        policy["schema_version"] = True
        with self.assertRaises(PolicyError):
            evaluate_policy({"Results": []}, policy, today="2026-10-04")

    def test_empty_exception_list_restores_strict_default(self) -> None:
        evaluation = evaluate_policy(
            {"Results": []}, {"schema_version": 1, "exceptions": []}, today="2026-10-04"
        )

        self.assertEqual(evaluation.blocking_findings, [])
        self.assertEqual(evaluation.accepted_findings, [])

    def test_policy_never_accepts_secrets(self) -> None:
        report = {
            "Results": [
                {
                    "Target": ".env",
                    "Secrets": [
                        {
                            "Severity": "CRITICAL",
                            "RuleID": "generic-api-key",
                            "Match": "do-not-print-or-suppress-this-secret",
                        }
                    ],
                }
            ]
        }

        evaluation = evaluate_policy(report, self.acceptance_policy(), today="2026-10-04")

        self.assertEqual(len(evaluation.blocking_findings), 2)
        self.assertNotIn(
            "do-not-print-or-suppress-this-secret",
            " ".join(evaluation.blocking_findings),
        )

    @staticmethod
    def acceptance_policy() -> dict[str, object]:
        return {
            "schema_version": 1,
            "exceptions": [
                {
                    "id": "CVE-2026-54369",
                    "packages": {"libacl1": "2.3.2-2+b1"},
                    "distro_prefix": "debian-13.",
                    "owner": "platform",
                    "reviewed_on": "2026-10-04",
                    "expires_on": "2026-11-03",
                    "rationale": (
                        "Debian tracker reports no DSA for stable; review again at expiry."
                    ),
                    "source": "https://security-tracker.debian.org/tracker/CVE-2026-54369",
                }
            ],
        }

    @staticmethod
    def os_report(
        cve: str,
        package: str,
        version: str,
        distro: str,
        result_class: str = "os-pkgs",
    ) -> dict[str, object]:
        return {
            "Results": [
                {
                    "Target": "blast-ecom-api:production",
                    "Type": "debian",
                    "Class": result_class,
                    "Vulnerabilities": [
                        {
                            "Severity": "HIGH",
                            "VulnerabilityID": cve,
                            "PkgName": package,
                            "InstalledVersion": version,
                            "PkgIdentifier": {
                                "PURL": (
                                    f"pkg:deb/debian/{package}@{version}?arch=arm64&distro={distro}"
                                )
                            },
                        }
                    ],
                }
            ]
        }


if __name__ == "__main__":
    unittest.main()
