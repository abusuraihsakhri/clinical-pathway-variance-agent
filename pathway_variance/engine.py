"""
Algorithmic Engine & Clinical Logic for Pathway Variance & ERAS Adherence.
Domain: Clinical Operations & Evidence-Based Surgical Care
Standard: ERAS® (Enhanced Recovery After Surgery) Society Guidelines
"""

import math
from typing import Dict, List, Optional, Any
from .models import (
    PathwayPhase,
    VarianceSeverity,
    VarianceRootCause,
    SurgicalSpecialty,
    MilestoneDefinition,
    ClinicalMilestoneRecord,
    PatientPathwayRecord,
    VarianceItem,
    PathwayAnalysisResult,
)

# Standard ERAS Protocols by Specialty
ERAS_PROTOCOLS: Dict[SurgicalSpecialty, List[MilestoneDefinition]] = {
    SurgicalSpecialty.COLORECTAL: [
        # Preoperative
        MilestoneDefinition("PRE_FASTING", PathwayPhase.PREOPERATIVE, "Carbohydrate Loading & Clear Fluids", "Carbohydrate drink 2-3h prior; clear fluids until 2h", weight=1.5),
        MilestoneDefinition("PRE_EDUCATION", PathwayPhase.PREOPERATIVE, "Preoperative ERAS Counseling", "Structured patient education & goal setting", weight=1.0),
        MilestoneDefinition("PRE_ANTIBIOTIC", PathwayPhase.PREOPERATIVE, "Prophylactic Antibiotics <=60m", "Targeted IV antibiotic administered within 60 min of incision", weight=2.0),
        # Intraoperative
        MilestoneDefinition("INTRA_GDFT", PathwayPhase.INTRAOPERATIVE, "Goal-Directed Fluid Therapy", "Fluid restrictive strategy (<30 mL/kg/day or SVV <=13%)", weight=2.5),
        MilestoneDefinition("INTRA_NORMOTHERMIA", PathwayPhase.INTRAOPERATIVE, "Normothermia Maintenance", "Core body temperature >= 36.0°C at emergence", weight=2.0),
        MilestoneDefinition("INTRA_MULTIMODAL_ANALGESIA", PathwayPhase.INTRAOPERATIVE, "Opioid-Sparing Multimodal Analgesia", "TAP block/epidural + acetaminophen + NSAIDs/gabapentinoids", weight=2.5),
        MilestoneDefinition("INTRA_NO_ROUTINE_DRAIN", PathwayPhase.INTRAOPERATIVE, "Avoidance of Routine Peritoneal Drains", "No prophylactic abdominal drains unless high risk", weight=1.5),
        # POD 0
        MilestoneDefinition("POD0_EARLY_FLUIDS", PathwayPhase.POD_0, "Early Oral Fluid Intake", "Oral liquids resumed within 4 hours post-extubation", weight=2.0),
        MilestoneDefinition("POD0_MOBILIZATION", PathwayPhase.POD_0, "Early Ambulation (POD 0)", "Out of bed / seated in chair >= 2 hours on day of surgery", weight=2.5),
        MilestoneDefinition("POD0_OPIOID_MINIMIZATION", PathwayPhase.POD_0, "Minimization of IV Opioids", "Oral non-opioid baseline with IV rescue only", weight=2.0),
        # POD 1
        MilestoneDefinition("POD1_SOLID_DIET", PathwayPhase.POD_1, "Solid Diet Initiation", "Regular or light solid diet tolerated on POD 1", weight=2.0),
        MilestoneDefinition("POD1_AMBULATION_6H", PathwayPhase.POD_1, "Sustained Mobilization (>=6h)", "Ambulation and chair sitting >= 6 hours on POD 1", weight=2.5),
        MilestoneDefinition("POD1_FOLEY_REMOVAL", PathwayPhase.POD_1, "Early Foley Catheter Removal", "Urinary catheter removed within 24h post-op (or <=48h for low pelvis)", weight=2.5),
        MilestoneDefinition("POD1_IVF_DISCONTINUATION", PathwayPhase.POD_1, "Cessation of Maintenance IV Fluids", "IV fluids discontinued once oral intake > 1200 mL/day", weight=2.0),
        # POD 2+
        MilestoneDefinition("POD2_BOWEL_RECOVERY", PathwayPhase.POD_2, "Return of Gastrointestinal Function", "Passage of flatus or bowel movement with no PONV/ileus", weight=2.5),
        MilestoneDefinition("DISCHARGE_CRITERIA", PathwayPhase.DISCHARGE, "Discharge Readiness Concordance", "Pain on oral meds, independent ambulation, tolerating diet", weight=3.0),
    ],
    SurgicalSpecialty.ORTHOPEDIC: [
        MilestoneDefinition("PRE_EDUCATION", PathwayPhase.PREOPERATIVE, "Preoperative Joint Class", "Patient education and mobility expectations", weight=1.0),
        MilestoneDefinition("PRE_TXA", PathwayPhase.PREOPERATIVE, "Tranexamic Acid (TXA) Administration", "Pre-incision TXA for blood conservation", weight=2.5),
        MilestoneDefinition("INTRA_REGIONAL_BLOCK", PathwayPhase.INTRAOPERATIVE, "Regional / Neuraxial Anesthesia", "Spinal/Adductor canal block avoiding general opioid overload", weight=2.5),
        MilestoneDefinition("INTRA_NORMOTHERMIA", PathwayPhase.INTRAOPERATIVE, "Normothermia Maintenance", "Active warming maintain temp >=36°C", weight=1.5),
        MilestoneDefinition("POD0_PHYSICAL_THERAPY", PathwayPhase.POD_0, "Same-Day Physical Therapy", "PT evaluation and ambulation within 4-6 hours post-op", weight=3.0),
        MilestoneDefinition("POD0_CRYO_COMPRESSION", PathwayPhase.POD_0, "Cryotherapy and Limb Elevation", "Cold therapy applied for swelling control", weight=1.5),
        MilestoneDefinition("POD1_INDEPENDENT_TRANSFER", PathwayPhase.POD_1, "Independent Transfer & Gait", "Safe transfer and ambulation >=100 ft", weight=2.5),
        MilestoneDefinition("POD1_MULTIMODAL_PAIN", PathwayPhase.POD_1, "Oral Multimodal Pain Regimen", "Oral NSAIDs + acetaminophen + nerve membrane stabilizers", weight=2.0),
        MilestoneDefinition("DISCHARGE_CRITERIA", PathwayPhase.DISCHARGE, "Discharge Milestone Attained", "Safe stair climbing, home readiness verified", weight=2.5),
    ],
    SurgicalSpecialty.BARIATRIC: [
        MilestoneDefinition("PRE_FASTING", PathwayPhase.PREOPERATIVE, "Carbohydrate Loading", "Clear liquids up to 2 hours prior", weight=1.5),
        MilestoneDefinition("INTRA_MINIMAL_OPIOID", PathwayPhase.INTRAOPERATIVE, "Opioid-Free / Sparing Anesthesia", "Ketamine, lidocaine, dexmedetomidine infusion", weight=2.5),
        MilestoneDefinition("POD0_EARLY_AMBULATION", PathwayPhase.POD_0, "Ambulation within 2 hours", "Prevent VTE with immediate post-op ambulation", weight=3.0),
        MilestoneDefinition("POD0_SIP_PROTOCOL", PathwayPhase.POD_0, "Graduated Fluid Protocol", "30-50 mL/h clear sips protocol initiated", weight=2.0),
        MilestoneDefinition("POD1_ADEQUATE_HYDRATION", PathwayPhase.POD_1, "Target Oral Intake >=1.5L", "No nausea, tolerating clear liquid progression", weight=2.0),
        MilestoneDefinition("POD1_PAIN_ORAL", PathwayPhase.POD_1, "Oral Analgesia Conversion", "Liquid or crushed oral analgesics", weight=2.0),
        MilestoneDefinition("DISCHARGE_CRITERIA", PathwayPhase.DISCHARGE, "Discharge Readiness", "Vitals stable, ambulating, good hydration", weight=2.5),
    ],
    SurgicalSpecialty.GYNECOLOGIC: [
        MilestoneDefinition("PRE_FASTING", PathwayPhase.PREOPERATIVE, "Carbohydrate Loading", "Pre-op CHO loading 2-3h before surgery", weight=1.5),
        MilestoneDefinition("INTRA_MULTIMODAL", PathwayPhase.INTRAOPERATIVE, "Multimodal Analgesia & TAP Block", "Local/regional infiltration + non-opioid medications", weight=2.5),
        MilestoneDefinition("INTRA_GDFT", PathwayPhase.INTRAOPERATIVE, "Goal-Directed Fluid Balance", "Zero-balance / euvolemic fluid strategy", weight=2.0),
        MilestoneDefinition("POD0_EARLY_FEEDING", PathwayPhase.POD_0, "Early Oral Intake", "Oral liquids within 4 hours", weight=2.0),
        MilestoneDefinition("POD0_AMBULATION", PathwayPhase.POD_0, "Early Mobilization", "Out of bed on POD 0", weight=2.0),
        MilestoneDefinition("POD1_FOLEY_OUT", PathwayPhase.POD_1, "Foley Removal <=24h", "Early bladder catheter removal", weight=2.5),
        MilestoneDefinition("DISCHARGE_CRITERIA", PathwayPhase.DISCHARGE, "Discharge Criteria Met", "Normal voiding trial, pain controlled, tolerating food", weight=2.5),
    ],
    SurgicalSpecialty.THORACIC: [
        MilestoneDefinition("PRE_PULM_REHAB", PathwayPhase.PREOPERATIVE, "Inspiratory Muscle Training", "Pre-op incentive spirometry & smoking cessation", weight=1.5),
        MilestoneDefinition("INTRA_PARA_VERTEBRAL", PathwayPhase.INTRAOPERATIVE, "Thoracic Paravertebral / ESP Block", "Targeted regional block over systemic opioids", weight=2.5),
        MilestoneDefinition("INTRA_PROTECTIVE_VENT", PathwayPhase.INTRAOPERATIVE, "Lung-Protective Ventilation", "Low tidal volume (4-6 mL/kg) + PEEP", weight=2.5),
        MilestoneDefinition("POD0_CHAIR_SITTING", PathwayPhase.POD_0, "Out of Bed to Chair", "Mobilization on POD 0 within 4h", weight=2.5),
        MilestoneDefinition("POD1_CHEST_TUBE_MGMT", PathwayPhase.POD_1, "Digital Air Leak Monitoring", "Early chest tube removal when drainage <200ml and air leak 0", weight=3.0),
        MilestoneDefinition("POD1_AGGRESSIVE_PT", PathwayPhase.POD_1, "Chest Physiotherapy", "Early ambulation + frequent spirometry", weight=2.0),
        MilestoneDefinition("DISCHARGE_CRITERIA", PathwayPhase.DISCHARGE, "Discharge Readiness", "Room air SpO2 >92%, pain managed orally", weight=2.5),
    ],
}


class ClinicalPathwayVarianceEngine:
    """
    Core Domain Analytics Engine for ERAS Adherence and Variance Analysis.
    """

    SEVERITY_WEIGHTS: Dict[VarianceSeverity, float] = {
        VarianceSeverity.MINOR: 1.0,
        VarianceSeverity.MODERATE: 2.5,
        VarianceSeverity.MAJOR: 5.0,
        VarianceSeverity.CRITICAL: 10.0,
    }

    # Clinical regression coefficients for excess length of stay (days) by variance type
    LOS_COEFFICIENTS: Dict[VarianceSeverity, float] = {
        VarianceSeverity.MINOR: 0.15,
        VarianceSeverity.MODERATE: 0.65,
        VarianceSeverity.MAJOR: 1.85,
        VarianceSeverity.CRITICAL: 4.20,
    }

    # Direct excess intervention and remediation cost multipliers (USD)
    COST_COEFFICIENTS: Dict[VarianceSeverity, float] = {
        VarianceSeverity.MINOR: 150.0,
        VarianceSeverity.MODERATE: 650.0,
        VarianceSeverity.MAJOR: 2200.0,
        VarianceSeverity.CRITICAL: 7500.0,
    }

    @classmethod
    def get_protocol_milestones(cls, specialty: SurgicalSpecialty) -> List[MilestoneDefinition]:
        """Retrieve standard ERAS milestone catalog for a surgical specialty."""
        return ERAS_PROTOCOLS.get(specialty, ERAS_PROTOCOLS[SurgicalSpecialty.COLORECTAL])

    @classmethod
    def evaluate_patient_pathway(cls, patient: PatientPathwayRecord) -> PathwayAnalysisResult:
        """
        Perform a comprehensive pathway variance analysis for a surgical patient.
        Calculates compliance, variance burden, root-cause distribution, LOS predictions, and cost deviations.
        """
        protocol = cls.get_protocol_milestones(patient.specialty)
        total_milestone_count = len(protocol)
        observed_map = {m.milestone_id: m for m in patient.milestones}

        compliant_count = 0
        non_compliant_count = 0
        total_weighted_points = 0.0
        achieved_weighted_points = 0.0

        variances: List[VarianceItem] = []
        root_cause_counts: Dict[str, int] = {
            VarianceRootCause.PATIENT_FACTOR.value: 0,
            VarianceRootCause.CLINICIAN_PRACTICE.value: 0,
            VarianceRootCause.HOSPITAL_SYSTEM.value: 0,
            VarianceRootCause.SURGICAL_COMPLICATION.value: 0,
        }

        total_variance_burden = 0.0
        predicted_excess_los = 0.0
        total_direct_excess_cost = 0.0

        for proto_m in protocol:
            m_id = proto_m.milestone_id
            m_weight = proto_m.weight
            total_weighted_points += m_weight

            record = observed_map.get(m_id)
            if record is not None and record.status is True:
                compliant_count += 1
                achieved_weighted_points += m_weight
            else:
                non_compliant_count += 1
                if record is not None:
                    severity = record.severity or cls._default_severity(m_id, proto_m.phase)
                    root_cause = record.root_cause or VarianceRootCause.CLINICIAN_PRACTICE
                    reason = record.variance_reason or f"Failed milestone: {proto_m.name}"
                else:
                    severity = cls._default_severity(m_id, proto_m.phase)
                    root_cause = VarianceRootCause.HOSPITAL_SYSTEM
                    reason = f"Omission / Missing documentation for milestone: {proto_m.name}"

                sev_weight = cls.SEVERITY_WEIGHTS[severity]
                total_variance_burden += sev_weight * m_weight
                root_cause_counts[root_cause.value] += 1

                los_impact = cls.LOS_COEFFICIENTS[severity] * (m_weight / 2.0)
                predicted_excess_los += los_impact

                direct_cost = cls.COST_COEFFICIENTS[severity]
                total_direct_excess_cost += direct_cost

                remediation = cls._generate_remediation_plan(m_id, severity, root_cause)

                variances.append(
                    VarianceItem(
                        milestone_id=m_id,
                        milestone_name=proto_m.name,
                        phase=proto_m.phase,
                        severity=severity,
                        root_cause=root_cause,
                        severity_weight=sev_weight,
                        description=reason,
                        remediation_plan=remediation,
                        cost_impact_usd=direct_cost,
                        los_impact_days=los_impact,
                    )
                )

        for comp in patient.complications:
            total_variance_burden += 10.0
            predicted_excess_los += 2.5
            total_direct_excess_cost += 3500.0
            root_cause_counts[VarianceRootCause.SURGICAL_COMPLICATION.value] += 1

        compliance_rate_pct = (compliant_count / total_milestone_count * 100.0) if total_milestone_count > 0 else 0.0
        cci = (achieved_weighted_points / total_weighted_points * 100.0) if total_weighted_points > 0 else 0.0

        predicted_los = patient.expected_los_days + predicted_excess_los
        total_excess_cost = total_direct_excess_cost + (predicted_excess_los * patient.daily_bed_rate_usd)

        if total_variance_burden <= 2.5 and cci >= 85.0:
            risk_tier = "LOW"
        elif total_variance_burden <= 8.0 and cci >= 70.0:
            risk_tier = "MODERATE"
        elif total_variance_burden <= 18.0 or cci >= 50.0:
            risk_tier = "HIGH"
        else:
            risk_tier = "CRITICAL"

        recommendations = cls._generate_global_recommendations(variances, cci, risk_tier)

        return PathwayAnalysisResult(
            patient_id=patient.patient_id,
            specialty=patient.specialty,
            total_milestones=total_milestone_count,
            compliant_milestones=compliant_count,
            non_compliant_milestones=non_compliant_count,
            compliance_rate_pct=compliance_rate_pct,
            cumulative_compliance_index=cci,
            total_variance_burden_score=total_variance_burden,
            variances=variances,
            root_cause_breakdown=root_cause_counts,
            expected_los_days=patient.expected_los_days,
            predicted_los_days=predicted_los,
            actual_los_days=patient.actual_los_days,
            predicted_excess_los_days=predicted_excess_los,
            estimated_excess_cost_usd=total_excess_cost,
            clinical_risk_tier=risk_tier,
            recommendations=recommendations,
        )

    @classmethod
    def _default_severity(cls, milestone_id: str, phase: PathwayPhase) -> VarianceSeverity:
        if "COMPLICATION" in milestone_id or phase == PathwayPhase.DISCHARGE:
            return VarianceSeverity.MAJOR
        if phase in (PathwayPhase.POD_0, PathwayPhase.POD_1):
            return VarianceSeverity.MODERATE
        return VarianceSeverity.MINOR

    @classmethod
    def _generate_remediation_plan(
        cls, milestone_id: str, severity: VarianceSeverity, root_cause: VarianceRootCause
    ) -> str:
        plans = {
            "INTRA_GDFT": "Re-calibrate intraoperative fluid algorithm; utilize dynamic stroke volume variation (SVV) monitoring.",
            "POD1_FOLEY_REMOVAL": "Implement nurse-driven Foley catheter removal protocol on POD 1 morning; evaluate for ultrasound bladder scan if post-void retention occurs.",
            "POD0_MOBILIZATION": "Schedule designated nursing or physical therapy assist within 2-4 hours post-extubation.",
            "POD1_SOLID_DIET": "Initiate gut motility stimulation (e.g. gum chewing, alvimopan for bowel surgery) and anti-emetic regimen.",
            "INTRA_MULTIMODAL_ANALGESIA": "Consult acute pain service for regional block rescue (TAP/ESP) and convert IV patient-controlled analgesia (PCA) to scheduled oral non-opioids.",
            "PRE_FASTING": "Provide standardized carbohydrate loading drinks and patient education in preoperative clinic.",
            "POD1_CHEST_TUBE_MGMT": "Utilize digital pleural drainage system to objectively measure air leak and trigger removal when <20 mL/min for 6 hours.",
        }
        if milestone_id in plans:
            return plans[milestone_id]
        if root_cause == VarianceRootCause.CLINICIAN_PRACTICE:
            return "Conduct clinical peer audit and align with departmental ERAS order sets."
        elif root_cause == VarianceRootCause.HOSPITAL_SYSTEM:
            return "Escalate resource bottleneck to clinical unit coordinator and perioperative committee."
        elif root_cause == VarianceRootCause.PATIENT_FACTOR:
            return "Initiate tailored symptom management (PONV prophylaxis, pre-op optimization)."
        else:
            return "Execute multi-disciplinary team evaluation and complication management pathway."

    @classmethod
    def _generate_global_recommendations(
        cls, variances: List[VarianceItem], cci: float, risk_tier: str
    ) -> List[str]:
        recs = []
        if cci < 75.0:
            recs.append(f"Cumulative Compliance Index is {cci:.1f}% (Below 75% target threshold). Multidisciplinary clinical review required.")
        
        has_foley_var = any("FOLEY" in v.milestone_id for v in variances)
        if has_foley_var:
            recs.append("Trigger CAUTI prevention pathway: verify strict criteria for delayed catheter removal.")

        has_opioid_var = any("ANALGESIA" in v.milestone_id or "OPIOID" in v.milestone_id for v in variances)
        if has_opioid_var:
            recs.append("Initiate Acute Pain Service consult for multimodal non-opioid regimen transition.")

        has_fluid_var = any("GDFT" in v.milestone_id or "FLUID" in v.milestone_id for v in variances)
        if has_fluid_var:
            recs.append("Audit intraoperative fluid administration volumes to prevent tissue edema and delayed gastrointestinal recovery.")

        if risk_tier in ("HIGH", "CRITICAL"):
            recs.append("Flag for daily perioperative variance rounds and expedited discharge planning conference.")

        if not recs:
            recs.append("Patient is progressing within optimal ERAS trajectory. Maintain routine post-op recovery protocol.")
        return recs


def analyze_patient_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Helper entry point to evaluate patient data dictionary and return serializable results."""
    specialty_str = str(data.get("specialty", "COLORECTAL")).upper()
    try:
        specialty = SurgicalSpecialty(specialty_str)
    except ValueError:
        specialty = SurgicalSpecialty.COLORECTAL

    milestone_records = []
    for m in data.get("milestones", []):
        m_id = m.get("milestone_id", "")
        status = bool(m.get("status", False))
        obs_val = m.get("observed_value")
        v_reason = m.get("variance_reason")
        
        rc_str = m.get("root_cause")
        root_cause = None
        if rc_str:
            try:
                root_cause = VarianceRootCause(str(rc_str))
            except ValueError:
                root_cause = VarianceRootCause.PATIENT_FACTOR

        sev_str = m.get("severity")
        severity = None
        if sev_str:
            try:
                severity = VarianceSeverity(str(sev_str))
            except ValueError:
                severity = VarianceSeverity.MODERATE

        notes = m.get("notes", "")
        phase_str = m.get("phase", "POD_1")
        try:
            phase = PathwayPhase(str(phase_str))
        except ValueError:
            phase = PathwayPhase.POD_1

        milestone_records.append(
            ClinicalMilestoneRecord(
                milestone_id=m_id,
                phase=phase,
                status=status,
                observed_value=obs_val,
                variance_reason=v_reason,
                root_cause=root_cause,
                severity=severity,
                notes=notes,
            )
        )

    patient_rec = PatientPathwayRecord(
        patient_id=str(data.get("patient_id", "PT-UNKNOWN")),
        specialty=specialty,
        procedure_name=str(data.get("procedure_name", "Elective Surgery")),
        expected_los_days=float(data.get("expected_los_days", 3.0)),
        actual_los_days=float(data["actual_los_days"]) if "actual_los_days" in data and data["actual_los_days"] is not None else None,
        daily_bed_rate_usd=float(data.get("daily_bed_rate_usd", 2400.0)),
        milestones=milestone_records,
        patient_risk_factors=data.get("patient_risk_factors", {}),
        complications=data.get("complications", []),
    )

    engine_res = ClinicalPathwayVarianceEngine.evaluate_patient_pathway(patient_rec)
    return engine_res.to_dict()
