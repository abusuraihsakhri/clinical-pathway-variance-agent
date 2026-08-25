"""
Unit and Integration Test Suite for Clinical Pathway Variance Agent
===================================================================
Tests all specialty protocols, compliance metrics, variance scoring,
cost/LOS impact regression models, and edge cases.
"""

import unittest
import json
import os
import sys
import subprocess

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pathway_variance import (
    PathwayPhase,
    VarianceSeverity,
    VarianceRootCause,
    SurgicalSpecialty,
    MilestoneDefinition,
    ClinicalMilestoneRecord,
    PatientPathwayRecord,
    VarianceItem,
    PathwayAnalysisResult,
    ERAS_PROTOCOLS,
    ClinicalPathwayVarianceEngine,
    analyze_patient_dict,
)


class TestERASProtocols(unittest.TestCase):
    """Test standard clinical protocol definitions."""

    def test_all_specialties_defined(self):
        for spec in SurgicalSpecialty:
            self.assertIn(spec, ERAS_PROTOCOLS)
            milestones = ERAS_PROTOCOLS[spec]
            self.assertGreater(len(milestones), 4)

    def test_milestone_weights_positive(self):
        for spec, milestones in ERAS_PROTOCOLS.items():
            for m in milestones:
                self.assertGreater(m.weight, 0.0)
                self.assertTrue(len(m.milestone_id) > 2)
                self.assertTrue(len(m.name) > 3)

    def test_unique_milestone_ids_per_specialty(self):
        for spec, milestones in ERAS_PROTOCOLS.items():
            ids = [m.milestone_id for m in milestones]
            self.assertEqual(len(ids), len(set(ids)), f"Duplicate milestone ID in {spec}")


class TestPathwayAdherenceScoring(unittest.TestCase):
    """Test quantitative scoring, CCI, and variance detection."""

    def test_perfect_colorectal_adherence(self):
        protocol = ERAS_PROTOCOLS[SurgicalSpecialty.COLORECTAL]
        records = [
            ClinicalMilestoneRecord(
                milestone_id=m.milestone_id,
                phase=m.phase,
                status=True,
                observed_value="Achieved",
            )
            for m in protocol
        ]
        patient = PatientPathwayRecord(
            patient_id="PT-PERFECT-01",
            specialty=SurgicalSpecialty.COLORECTAL,
            procedure_name="Elective Right Hemicolectomy",
            expected_los_days=3.0,
            milestones=records,
        )
        res = ClinicalPathwayVarianceEngine.evaluate_patient_pathway(patient)

        self.assertEqual(res.compliant_milestones, len(protocol))
        self.assertEqual(res.non_compliant_milestones, 0)
        self.assertAlmostEqual(res.compliance_rate_pct, 100.0, places=2)
        self.assertAlmostEqual(res.cumulative_compliance_index, 100.0, places=2)
        self.assertEqual(res.total_variance_burden_score, 0.0)
        self.assertEqual(res.clinical_risk_tier, "LOW")
        self.assertEqual(len(res.variances), 0)
        self.assertAlmostEqual(res.predicted_excess_los_days, 0.0)

    def test_single_minor_variance(self):
        protocol = ERAS_PROTOCOLS[SurgicalSpecialty.COLORECTAL]
        records = []
        for m in protocol:
            if m.milestone_id == "POD0_MOBILIZATION":
                records.append(
                    ClinicalMilestoneRecord(
                        milestone_id=m.milestone_id,
                        phase=m.phase,
                        status=False,
                        observed_value=0,
                        variance_reason="Patient drowsy; mobilization delayed",
                        severity=VarianceSeverity.MINOR,
                        root_cause=VarianceRootCause.PATIENT_FACTOR,
                    )
                )
            else:
                records.append(
                    ClinicalMilestoneRecord(
                        milestone_id=m.milestone_id,
                        phase=m.phase,
                        status=True,
                        observed_value="OK",
                    )
                )
        patient = PatientPathwayRecord(
            patient_id="PT-MINOR-01",
            specialty=SurgicalSpecialty.COLORECTAL,
            procedure_name="Sigmoid Resection",
            expected_los_days=3.0,
            milestones=records,
        )
        res = ClinicalPathwayVarianceEngine.evaluate_patient_pathway(patient)
        self.assertEqual(res.non_compliant_milestones, 1)
        self.assertEqual(len(res.variances), 1)
        self.assertEqual(res.variances[0].severity, VarianceSeverity.MINOR)
        self.assertEqual(res.variances[0].root_cause, VarianceRootCause.PATIENT_FACTOR)
        self.assertEqual(res.clinical_risk_tier, "LOW")
        self.assertGreater(res.predicted_excess_los_days, 0.0)

    def test_major_and_critical_variances(self):
        protocol = ERAS_PROTOCOLS[SurgicalSpecialty.BARIATRIC]
        records = [
            ClinicalMilestoneRecord(
                milestone_id="INTRA_MINIMAL_OPIOID",
                phase=PathwayPhase.INTRAOPERATIVE,
                status=False,
                observed_value="High dose fentanyl",
                severity=VarianceSeverity.MAJOR,
                root_cause=VarianceRootCause.CLINICIAN_PRACTICE,
            ),
            ClinicalMilestoneRecord(
                milestone_id="POD0_EARLY_AMBULATION",
                phase=PathwayPhase.POD_0,
                status=False,
                observed_value="Bedbound",
                severity=VarianceSeverity.CRITICAL,
                root_cause=VarianceRootCause.PATIENT_FACTOR,
            ),
        ]
        patient = PatientPathwayRecord(
            patient_id="PT-BARIATRIC-SEV",
            specialty=SurgicalSpecialty.BARIATRIC,
            procedure_name="Roux-en-Y Gastric Bypass",
            expected_los_days=2.0,
            milestones=records,
        )
        res = ClinicalPathwayVarianceEngine.evaluate_patient_pathway(patient)
        self.assertIn(res.clinical_risk_tier, ["HIGH", "CRITICAL"])
        self.assertGreater(res.total_variance_burden_score, 15.0)
        self.assertGreater(res.estimated_excess_cost_usd, 5000.0)

    def test_orthopedic_pathway_evaluation(self):
        protocol = ERAS_PROTOCOLS[SurgicalSpecialty.ORTHOPEDIC]
        records = [
            ClinicalMilestoneRecord(
                milestone_id=m.milestone_id,
                phase=m.phase,
                status=True if m.milestone_id != "POD0_PHYSICAL_THERAPY" else False,
                observed_value="PT unavailable",
                severity=VarianceSeverity.MODERATE if m.milestone_id == "POD0_PHYSICAL_THERAPY" else None,
                root_cause=VarianceRootCause.HOSPITAL_SYSTEM if m.milestone_id == "POD0_PHYSICAL_THERAPY" else None,
            )
            for m in protocol
        ]
        patient = PatientPathwayRecord(
            patient_id="PT-ORTHO-01",
            specialty=SurgicalSpecialty.ORTHOPEDIC,
            procedure_name="Total Knee Arthroplasty",
            expected_los_days=2.0,
            milestones=records,
        )
        res = ClinicalPathwayVarianceEngine.evaluate_patient_pathway(patient)
        self.assertEqual(res.specialty, SurgicalSpecialty.ORTHOPEDIC)
        self.assertEqual(res.root_cause_breakdown[VarianceRootCause.HOSPITAL_SYSTEM.value], 1)

    def test_thoracic_pathway_evaluation(self):
        protocol = ERAS_PROTOCOLS[SurgicalSpecialty.THORACIC]
        records = [
            ClinicalMilestoneRecord(
                milestone_id=m.milestone_id,
                phase=m.phase,
                status=True,
                observed_value="Standard care",
            )
            for m in protocol
        ]
        patient = PatientPathwayRecord(
            patient_id="PT-THORACIC-01",
            specialty=SurgicalSpecialty.THORACIC,
            procedure_name="VATS Lobectomy",
            expected_los_days=3.0,
            milestones=records,
        )
        res = ClinicalPathwayVarianceEngine.evaluate_patient_pathway(patient)
        self.assertEqual(res.compliance_rate_pct, 100.0)

    def test_gynecologic_pathway_evaluation(self):
        protocol = ERAS_PROTOCOLS[SurgicalSpecialty.GYNECOLOGIC]
        patient = PatientPathwayRecord(
            patient_id="PT-GYN-01",
            specialty=SurgicalSpecialty.GYNECOLOGIC,
            procedure_name="Total Laparoscopic Hysterectomy",
            expected_los_days=1.0,
            milestones=[],
        )
        res = ClinicalPathwayVarianceEngine.evaluate_patient_pathway(patient)
        self.assertEqual(res.compliant_milestones, 0)
        self.assertEqual(res.non_compliant_milestones, len(protocol))
        self.assertEqual(res.compliance_rate_pct, 0.0)
        self.assertEqual(res.clinical_risk_tier, "CRITICAL")


class TestComplicationsAndFinancialImpact(unittest.TestCase):
    """Test complications, financial modeling, and LOS prediction."""

    def test_complication_additive_impact(self):
        patient = PatientPathwayRecord(
            patient_id="PT-COMPLICATION-01",
            specialty=SurgicalSpecialty.COLORECTAL,
            procedure_name="Low Anterior Resection",
            expected_los_days=4.0,
            milestones=[],
            complications=["Anastomotic Leak Clavien-Dindo IIIb", "Intra-abdominal abscess"],
        )
        res = ClinicalPathwayVarianceEngine.evaluate_patient_pathway(patient)
        self.assertEqual(res.root_cause_breakdown[VarianceRootCause.SURGICAL_COMPLICATION.value], 2)
        self.assertGreater(res.predicted_excess_los_days, 5.0)
        self.assertGreater(res.estimated_excess_cost_usd, 15000.0)

    def test_bed_rate_scaling(self):
        patient_std_rate = PatientPathwayRecord(
            patient_id="PT-BED-1",
            specialty=SurgicalSpecialty.COLORECTAL,
            procedure_name="Colectomy",
            expected_los_days=3.0,
            daily_bed_rate_usd=2000.0,
            milestones=[
                ClinicalMilestoneRecord("INTRA_GDFT", PathwayPhase.INTRAOPERATIVE, False, "Excess fluids", severity=VarianceSeverity.MAJOR)
            ]
        )
        patient_high_rate = PatientPathwayRecord(
            patient_id="PT-BED-2",
            specialty=SurgicalSpecialty.COLORECTAL,
            procedure_name="Colectomy",
            expected_los_days=3.0,
            daily_bed_rate_usd=4000.0,
            milestones=[
                ClinicalMilestoneRecord("INTRA_GDFT", PathwayPhase.INTRAOPERATIVE, False, "Excess fluids", severity=VarianceSeverity.MAJOR)
            ]
        )
        res_std = ClinicalPathwayVarianceEngine.evaluate_patient_pathway(patient_std_rate)
        res_high = ClinicalPathwayVarianceEngine.evaluate_patient_pathway(patient_high_rate)

        self.assertAlmostEqual(res_std.predicted_excess_los_days, res_high.predicted_excess_los_days)
        self.assertGreater(res_high.estimated_excess_cost_usd, res_std.estimated_excess_cost_usd)


class TestDictParserAndEdgeCases(unittest.TestCase):
    """Test helper parser and edge case handling."""

    def test_analyze_patient_dict_valid(self):
        data = {
            "patient_id": "PT-JSON-100",
            "specialty": "COLORECTAL",
            "expected_los_days": 3.0,
            "milestones": [
                {"milestone_id": "PRE_FASTING", "status": True},
                {"milestone_id": "INTRA_GDFT", "status": False, "severity": "MAJOR", "root_cause": "CLINICIAN_PRACTICE"}
            ]
        }
        res_dict = analyze_patient_dict(data)
        self.assertEqual(res_dict["patient_id"], "PT-JSON-100")
        self.assertEqual(res_dict["specialty"], "COLORECTAL")
        self.assertIn("variances", res_dict)
        self.assertIn("cumulative_compliance_index", res_dict)

    def test_analyze_patient_dict_unknown_specialty(self):
        data = {
            "patient_id": "PT-JSON-101",
            "specialty": "NEUROSURGERY_UNKNOWN",
            "expected_los_days": 5.0,
            "milestones": []
        }
        res_dict = analyze_patient_dict(data)
        self.assertEqual(res_dict["specialty"], "COLORECTAL")

    def test_analyze_patient_dict_invalid_severity(self):
        data = {
            "patient_id": "PT-JSON-102",
            "specialty": "ORTHOPEDIC",
            "milestones": [
                {"milestone_id": "PRE_TXA", "status": False, "severity": "SUPER_CRITICAL_INVALID"}
            ]
        }
        res_dict = analyze_patient_dict(data)
        self.assertEqual(res_dict["patient_id"], "PT-JSON-102")

    def test_recommendations_generation(self):
        data = {
            "patient_id": "PT-RECS-01",
            "specialty": "COLORECTAL",
            "milestones": [
                {"milestone_id": "POD1_FOLEY_REMOVAL", "status": False, "severity": "MODERATE", "root_cause": "CLINICIAN_PRACTICE"},
                {"milestone_id": "INTRA_MULTIMODAL_ANALGESIA", "status": False, "severity": "MAJOR", "root_cause": "CLINICIAN_PRACTICE"},
            ]
        }
        res = analyze_patient_dict(data)
        recs = " ".join(res["recommendations"])
        self.assertIn("CAUTI", recs)
        self.assertIn("Acute Pain Service", recs)

    def test_json_serializability(self):
        data = {
            "patient_id": "PT-SERIALIZE-01",
            "specialty": "BARIATRIC",
            "expected_los_days": 2.0,
            "milestones": [
                {"milestone_id": "POD0_EARLY_AMBULATION", "status": True}
            ]
        }
        res = analyze_patient_dict(data)
        dumped = json.dumps(res)
        self.assertTrue(len(dumped) > 100)

    def test_phase_coverage(self):
        for phase in PathwayPhase:
            self.assertTrue(len(phase.value) > 0)

    def test_remediation_generation_coverage(self):
        for m_id in ["INTRA_GDFT", "POD1_FOLEY_REMOVAL", "POD0_MOBILIZATION", "POD1_SOLID_DIET", "INTRA_MULTIMODAL_ANALGESIA", "PRE_FASTING", "POD1_CHEST_TUBE_MGMT"]:
            plan = ClinicalPathwayVarianceEngine._generate_remediation_plan(
                m_id, VarianceSeverity.MODERATE, VarianceRootCause.CLINICIAN_PRACTICE
            )
            self.assertTrue(len(plan) > 10)

    def test_actual_los_passthrough(self):
        data = {
            "patient_id": "PT-ACTUAL-LOS",
            "specialty": "COLORECTAL",
            "expected_los_days": 3.0,
            "actual_los_days": 4.5,
            "milestones": []
        }
        res = analyze_patient_dict(data)
        self.assertEqual(res["actual_los_days"], 4.5)


if __name__ == "__main__":
    unittest.main()
