"""
Data Models & Definitions for Pathway Variance & ERAS Adherence.
Domain: Clinical Operations & Evidence-Based Surgical Care
Standard: ERAS® (Enhanced Recovery After Surgery) Society Guidelines
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any


class PathwayPhase(str, Enum):
    PREOPERATIVE = "PREOPERATIVE"
    INTRAOPERATIVE = "INTRAOPERATIVE"
    POD_0 = "POD_0"
    POD_1 = "POD_1"
    POD_2 = "POD_2"
    POD_3_PLUS = "POD_3_PLUS"
    DISCHARGE = "DISCHARGE"


class VarianceSeverity(str, Enum):
    MINOR = "MINOR"          # Weight: 1.0 (Minor timing delay)
    MODERATE = "MODERATE"    # Weight: 2.5 (Protocol deviation requiring intervention)
    MAJOR = "MAJOR"          # Weight: 5.0 (Clinical risk, delayed milestone)
    CRITICAL = "CRITICAL"    # Weight: 10.0 (Safety event, complication, ICU/OR return)


class VarianceRootCause(str, Enum):
    PATIENT_FACTOR = "PATIENT_FACTOR"        # Comorbidity, PONV, pain threshold, anatomy
    CLINICIAN_PRACTICE = "CLINICIAN_PRACTICE"# Non-standard ordering, delayed drain removal
    HOSPITAL_SYSTEM = "HOSPITAL_SYSTEM"      # PT unavailable, delayed bed, pharmacy delay
    SURGICAL_COMPLICATION = "SURGICAL_COMPLICATION" # Anastomotic leak, SSI, bleeding, ileus


class SurgicalSpecialty(str, Enum):
    COLORECTAL = "COLORECTAL"
    ORTHOPEDIC = "ORTHOPEDIC"
    BARIATRIC = "BARIATRIC"
    GYNECOLOGIC = "GYNECOLOGIC"
    THORACIC = "THORACIC"


@dataclass
class MilestoneDefinition:
    milestone_id: str
    phase: PathwayPhase
    name: str
    description: str
    weight: float = 1.0
    mandatory: bool = True
    target_metric: Optional[str] = None
    target_threshold: Optional[float] = None
    operator: str = "=="  # '==', '<=', '>=', 'in'


@dataclass
class ClinicalMilestoneRecord:
    milestone_id: str
    phase: PathwayPhase
    status: bool  # True = Achieved / Compliant, False = Variance / Non-compliant
    observed_value: Any
    variance_reason: Optional[str] = None
    root_cause: Optional[VarianceRootCause] = None
    severity: Optional[VarianceSeverity] = None
    notes: str = ""


@dataclass
class PatientPathwayRecord:
    patient_id: str
    specialty: SurgicalSpecialty
    procedure_name: str
    expected_los_days: float
    actual_los_days: Optional[float] = None
    daily_bed_rate_usd: float = 2400.0
    milestones: List[ClinicalMilestoneRecord] = field(default_factory=list)
    patient_risk_factors: Dict[str, Any] = field(default_factory=dict)
    complications: List[str] = field(default_factory=list)


@dataclass
class VarianceItem:
    milestone_id: str
    milestone_name: str
    phase: PathwayPhase
    severity: VarianceSeverity
    root_cause: VarianceRootCause
    severity_weight: float
    description: str
    remediation_plan: str
    cost_impact_usd: float
    los_impact_days: float


@dataclass
class PathwayAnalysisResult:
    patient_id: str
    specialty: SurgicalSpecialty
    total_milestones: int
    compliant_milestones: int
    non_compliant_milestones: int
    compliance_rate_pct: float
    cumulative_compliance_index: float  # Weighted compliance
    total_variance_burden_score: float
    variances: List[VarianceItem]
    root_cause_breakdown: Dict[str, int]
    expected_los_days: float
    predicted_los_days: float
    actual_los_days: Optional[float]
    predicted_excess_los_days: float
    estimated_excess_cost_usd: float
    clinical_risk_tier: str  # LOW, MODERATE, HIGH, CRITICAL
    recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "patient_id": self.patient_id,
            "specialty": self.specialty.value,
            "total_milestones": self.total_milestones,
            "compliant_milestones": self.compliant_milestones,
            "non_compliant_milestones": self.non_compliant_milestones,
            "compliance_rate_pct": round(self.compliance_rate_pct, 2),
            "cumulative_compliance_index": round(self.cumulative_compliance_index, 2),
            "total_variance_burden_score": round(self.total_variance_burden_score, 2),
            "root_cause_breakdown": self.root_cause_breakdown,
            "expected_los_days": self.expected_los_days,
            "predicted_los_days": round(self.predicted_los_days, 2),
            "actual_los_days": self.actual_los_days,
            "predicted_excess_los_days": round(self.predicted_excess_los_days, 2),
            "estimated_excess_cost_usd": round(self.estimated_excess_cost_usd, 2),
            "clinical_risk_tier": self.clinical_risk_tier,
            "variances": [
                {
                    "milestone_id": v.milestone_id,
                    "milestone_name": v.milestone_name,
                    "phase": v.phase.value,
                    "severity": v.severity.value,
                    "root_cause": v.root_cause.value,
                    "severity_weight": v.severity_weight,
                    "description": v.description,
                    "remediation_plan": v.remediation_plan,
                    "cost_impact_usd": round(v.cost_impact_usd, 2),
                    "los_impact_days": round(v.los_impact_days, 2),
                }
                for v in self.variances
            ],
            "recommendations": self.recommendations,
        }
