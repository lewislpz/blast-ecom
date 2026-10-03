from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from check_trivy_report import policy_findings


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
                    "Misconfigurations": [
                        {"Severity": "CRITICAL", "ID": "DS-EXAMPLE-1"}
                    ],
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


if __name__ == "__main__":
    unittest.main()
