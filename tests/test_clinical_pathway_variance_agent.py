"""
End-to-End and Security/Integrity Tests for Clinical Pathway Variance Agent
"""

import unittest
import os
import sys

# Ensure root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pathway_variance import (
    PathwayPhase,
    VarianceSeverity,
    VarianceRootCause,
    SurgicalSpecialty,
    PatientPathwayRecord,
    ClinicalMilestoneRecord,
    ClinicalPathwayVarianceEngine,
    analyze_patient_dict,
    ERAS_PROTOCOLS,
)


class TestClinicalPathwayVarianceAgentFull(unittest.TestCase):

    def test_full_pipeline_colorectal(self):
        payload = {
            "patient_id": "PT-COLO-999",
            "specialty": "COLORECTAL",
            "expected_los_days": 3.0,
            "milestones": [
                {"milestone_id": "PRE_FASTING", "status": True},
                {"milestone_id": "PRE_EDUCATION", "status": True},
                {"milestone_id": "PRE_ANTIBIOTIC", "status": True},
                {"milestone_id": "INTRA_GDFT", "status": False, "severity": "MAJOR", "root_cause": "CLINICIAN_PRACTICE"},
                {"milestone_id": "INTRA_NORMOTHERMIA", "status": True},
                {"milestone_id": "INTRA_MULTIMODAL_ANALGESIA", "status": True},
                {"milestone_id": "INTRA_NO_ROUTINE_DRAIN", "status": True},
                {"milestone_id": "POD0_EARLY_FLUIDS", "status": True},
                {"milestone_id": "POD0_MOBILIZATION", "status": True},
                {"milestone_id": "POD0_OPIOID_MINIMIZATION", "status": True},
                {"milestone_id": "POD1_SOLID_DIET", "status": True},
                {"milestone_id": "POD1_AMBULATION_6H", "status": True},
                {"milestone_id": "POD1_FOLEY_REMOVAL", "status": False, "severity": "MODERATE", "root_cause": "CLINICIAN_PRACTICE"},
                {"milestone_id": "POD1_IVF_DISCONTINUATION", "status": True},
                {"milestone_id": "POD2_BOWEL_RECOVERY", "status": True},
                {"milestone_id": "DISCHARGE_CRITERIA", "status": True},
            ]
        }
        result = analyze_patient_dict(payload)
        self.assertEqual(result["patient_id"], "PT-COLO-999")
        self.assertEqual(result["compliant_milestones"], 14)
        self.assertEqual(result["non_compliant_milestones"], 2)
        self.assertGreater(result["compliance_rate_pct"], 80.0)
        self.assertEqual(len(result["variances"]), 2)

    def test_empty_milestones_defaults(self):
        payload = {
            "patient_id": "PT-EMPTY",
            "specialty": "ORTHOPEDIC"
        }
        result = analyze_patient_dict(payload)
        self.assertEqual(result["compliant_milestones"], 0)
        self.assertEqual(result["clinical_risk_tier"], "CRITICAL")

    def test_high_complication_burden(self):
        payload = {
            "patient_id": "PT-HIGH-COMP",
            "specialty": "THORACIC",
            "expected_los_days": 3.0,
            "milestones": [
                {"milestone_id": "PRE_PULM_REHAB", "status": True},
                {"milestone_id": "INTRA_PARA_VERTEBRAL", "status": False, "severity": "MAJOR", "root_cause": "CLINICIAN_PRACTICE"},
            ],
            "complications": ["Pneumonia", "Prolonged Air Leak > 5 days", "Atrial Fibrillation"]
        }
        result = analyze_patient_dict(payload)
        self.assertEqual(result["root_cause_breakdown"]["SURGICAL_COMPLICATION"], 3)
        self.assertGreater(result["estimated_excess_cost_usd"], 20000.0)

    def test_root_cause_categorization(self):
        protocol = ERAS_PROTOCOLS[SurgicalSpecialty.BARIATRIC]
        for rc in [VarianceRootCause.PATIENT_FACTOR, VarianceRootCause.CLINICIAN_PRACTICE, VarianceRootCause.HOSPITAL_SYSTEM]:
            milestones = []
            for m in protocol:
                if m.milestone_id == "POD0_EARLY_AMBULATION":
                    milestones.append({"milestone_id": m.milestone_id, "status": False, "root_cause": rc.value, "severity": "MODERATE"})
                else:
                    milestones.append({"milestone_id": m.milestone_id, "status": True})
            
            payload = {
                "patient_id": f"PT-RC-{rc.value}",
                "specialty": "BARIATRIC",
                "milestones": milestones,
            }
            res = analyze_patient_dict(payload)
            self.assertEqual(res["root_cause_breakdown"][rc.value], 1)

    def test_cli_batch_processing(self):
        from cli import process_csv_batch
        sample_csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sample.csv"))
        out_csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "test_batch_out.csv"))
        try:
            count = process_csv_batch(sample_csv_path, out_csv_path)
            self.assertEqual(count, 5)
            self.assertTrue(os.path.exists(out_csv_path))
        finally:
            if os.path.exists(out_csv_path):
                os.remove(out_csv_path)


    def test_cli_batch_rejects_unknown_specialty(self):
        import csv
        import tempfile
        from cli import process_csv_batch

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.csv")
            output_path = os.path.join(tmpdir, "output.csv")
            with open(input_path, "w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=[
                    "patient_id", "specialty", "expected_los_days", "daily_bed_rate_usd"
                ])
                writer.writeheader()
                writer.writerow({
                    "patient_id": "PT-BAD-SPEC",
                    "specialty": "UNKNOWN",
                    "expected_los_days": "3",
                    "daily_bed_rate_usd": "2400",
                })
            with self.assertRaises(ValueError):
                process_csv_batch(input_path, output_path)

    def test_cli_batch_sanitizes_spreadsheet_formula_fields(self):
        import csv
        import tempfile
        from cli import process_csv_batch

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.csv")
            output_path = os.path.join(tmpdir, "output.csv")
            with open(input_path, "w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=[
                    "patient_id", "specialty", "procedure_name",
                    "expected_los_days", "daily_bed_rate_usd",
                    "variances_milestones", "complications",
                ])
                writer.writeheader()
                writer.writerow({
                    "patient_id": "=2+2",
                    "specialty": "COLORECTAL",
                    "procedure_name": "@SUM(1,1)",
                    "expected_los_days": "3",
                    "daily_bed_rate_usd": "2400",
                    "variances_milestones": "",
                    "complications": "",
                })
            process_csv_batch(input_path, output_path)
            with open(output_path, "r", encoding="utf-8", newline="") as handle:
                row = next(csv.DictReader(handle))
            self.assertEqual(row["patient_id"], "'=2+2")
            self.assertEqual(row["procedure_name"], "'@SUM(1,1)")


if __name__ == "__main__":
    unittest.main()

