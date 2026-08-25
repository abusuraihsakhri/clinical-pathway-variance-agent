#!/usr/bin/env python3
"""
Command-Line Interface for Clinical Pathway Variance Agent
==========================================================
Provides interactive analysis, single-case evaluation, batch processing,
benchmark testing, and JSON output formatting for ERAS pathway adherence.
"""

import sys
import os
import json
import argparse
from typing import Dict, Any

# Ensure project path is accessible
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from pathway_variance import (
    ClinicalPathwayVarianceEngine,
    PatientPathwayRecord,
    ClinicalMilestoneRecord,
    SurgicalSpecialty,
    PathwayPhase,
    VarianceSeverity,
    VarianceRootCause,
    analyze_patient_dict,
    ERAS_PROTOCOLS,
)


def get_sample_colorectal_case() -> Dict[str, Any]:
    return {
        "patient_id": "PT-COLORECTAL-101",
        "specialty": "COLORECTAL",
        "procedure_name": "Laparoscopic Sigmoid Colectomy",
        "expected_los_days": 3.0,
        "actual_los_days": None,
        "daily_bed_rate_usd": 2400.0,
        "milestones": [
            {"milestone_id": "PRE_FASTING", "status": True, "notes": "Drank carbohydrate beverage 2h pre-op"},
            {"milestone_id": "PRE_EDUCATION", "status": True, "notes": "Attended pre-op clinic"},
            {"milestone_id": "PRE_ANTIBIOTIC", "status": True, "notes": "Cefazolin + Metronidazole given at 07:15"},
            {"milestone_id": "INTRA_GDFT", "status": False, "variance_reason": "Excess fluid administered (42 mL/kg/day)", "severity": "MAJOR", "root_cause": "CLINICIAN_PRACTICE"},
            {"milestone_id": "INTRA_NORMOTHERMIA", "status": True, "notes": "Core temp 36.6 C at closure"},
            {"milestone_id": "INTRA_MULTIMODAL_ANALGESIA", "status": True, "notes": "Bilateral TAP block + scheduled IV acetaminophen"},
            {"milestone_id": "INTRA_NO_ROUTINE_DRAIN", "status": True, "notes": "No pelvic drain placed"},
            {"milestone_id": "POD0_EARLY_FLUIDS", "status": True, "notes": "Clear liquids tolerated POD 0 evening"},
            {"milestone_id": "POD0_MOBILIZATION", "status": False, "variance_reason": "Patient experienced postural hypotension; ambulation delayed", "severity": "MINOR", "root_cause": "PATIENT_FACTOR"},
            {"milestone_id": "POD0_OPIOID_MINIMIZATION", "status": True, "notes": "Only oral acetaminophen + tramadol rescue"},
            {"milestone_id": "POD1_SOLID_DIET", "status": False, "variance_reason": "Mild nausea; low solid food intake", "severity": "MINOR", "root_cause": "PATIENT_FACTOR"},
            {"milestone_id": "POD1_AMBULATION_6H", "status": True, "notes": "Mobilized 6.5 hours in chair and hall"},
            {"milestone_id": "POD1_FOLEY_REMOVAL", "status": False, "variance_reason": "Foley kept in place due to clinician preference", "severity": "MODERATE", "root_cause": "CLINICIAN_PRACTICE"},
            {"milestone_id": "POD1_IVF_DISCONTINUATION", "status": True, "notes": "IV bag heplocked at 10:00"},
            {"milestone_id": "POD2_BOWEL_RECOVERY", "status": True, "notes": "Flatus passed POD 2 morning"},
            {"milestone_id": "DISCHARGE_CRITERIA", "status": True, "notes": "Meets criteria on POD 3"},
        ],
        "complications": []
    }


def format_text_report(result: Dict[str, Any]) -> str:
    lines = []
    lines.append("=" * 78)
    lines.append(f" CLINICAL PATHWAY VARIANCE REPORT - {result['patient_id']}")
    lines.append("=" * 78)
    lines.append(f"Specialty:               {result['specialty']}")
    lines.append(f"Cumulative Compliance:   {result['cumulative_compliance_index']:.1f}%")
    lines.append(f"Milestones Achieved:     {result['compliant_milestones']} / {result['total_milestones']} ({result['compliance_rate_pct']:.1f}%)")
    lines.append(f"Variance Burden Score:   {result['total_variance_burden_score']:.1f}")
    lines.append(f"Clinical Risk Tier:      {result['clinical_risk_tier']}")
    lines.append(f"Expected LOS:            {result['expected_los_days']:.1f} days")
    lines.append(f"Predicted Total LOS:     {result['predicted_los_days']:.1f} days (+{result['predicted_excess_los_days']:.2f} days excess)")
    lines.append(f"Estimated Excess Cost:   ${result['estimated_excess_cost_usd']:,.2f} USD")
    lines.append("-" * 78)
    lines.append("ROOT CAUSE ATTRIBUTION:")
    for rc, count in result['root_cause_breakdown'].items():
        lines.append(f"  * {rc:<25}: {count} occurrences")
    lines.append("-" * 78)
    lines.append(f"DETECTED PATHWAY VARIANCES ({len(result['variances'])} Total):")
    if not result['variances']:
        lines.append("  None detected - Full ERAS Protocol Adherence!")
    else:
        for idx, v in enumerate(result['variances'], start=1):
            lines.append(f"  [{idx}] {v['milestone_name']} ({v['milestone_id']})")
            lines.append(f"      Phase: {v['phase']} | Severity: {v['severity']} | Cause: {v['root_cause']}")
            lines.append(f"      Details: {v['description']}")
            lines.append(f"      Remediation: {v['remediation_plan']}")
            lines.append(f"      Impact: +{v['los_impact_days']:.2f} days LOS | +${v['cost_impact_usd']:,.2f} Direct Cost")
    lines.append("-" * 78)
    lines.append("CLINICAL RECOMMENDATIONS:")
    for idx, rec in enumerate(result['recommendations'], start=1):
        lines.append(f"  {idx}. {rec}")
    lines.append("=" * 78)
    return "\n".join(lines)


def interactive_mode():
    print("\n--- Interactive ERAS Clinical Pathway Variance Agent ---")
    patient_id = input("Enter Patient ID [e.g. PT-2026-001]: ").strip() or "PT-2026-001"
    
    print("\nAvailable Specialties:")
    for s in SurgicalSpecialty:
        print(f"  - {s.value}")
    spec_input = input("Select Specialty [default COLORECTAL]: ").strip().upper() or "COLORECTAL"
    try:
        specialty = SurgicalSpecialty(spec_input)
    except ValueError:
        specialty = SurgicalSpecialty.COLORECTAL

    expected_los = input("Expected Baseline LOS (days) [default 3.0]: ").strip()
    expected_los_val = float(expected_los) if expected_los else 3.0

    protocol = ClinicalPathwayVarianceEngine.get_protocol_milestones(specialty)
    print(f"\nEvaluating {len(protocol)} standard ERAS milestones for {specialty.value}:")
    
    milestone_records = []
    for m in protocol:
        resp = input(f"  -> Was [{m.name}] ({m.phase.value}) achieved? (y/n) [default y]: ").strip().lower()
        if resp in ("n", "no", "false", "0"):
            reason = input("     Variance reason / explanation: ").strip() or f"Delayed or omitted {m.name}"
            print("     Root causes: 1) PATIENT_FACTOR  2) CLINICIAN_PRACTICE  3) HOSPITAL_SYSTEM  4) SURGICAL_COMPLICATION")
            rc_choice = input("     Select root cause [1-4, default 2]: ").strip()
            rc_map = {
                "1": VarianceRootCause.PATIENT_FACTOR,
                "2": VarianceRootCause.CLINICIAN_PRACTICE,
                "3": VarianceRootCause.HOSPITAL_SYSTEM,
                "4": VarianceRootCause.SURGICAL_COMPLICATION
            }
            root_cause = rc_map.get(rc_choice, VarianceRootCause.CLINICIAN_PRACTICE)
            milestone_records.append(
                ClinicalMilestoneRecord(
                    milestone_id=m.milestone_id,
                    phase=m.phase,
                    status=False,
                    observed_value=None,
                    variance_reason=reason,
                    root_cause=root_cause,
                    severity=VarianceSeverity.MODERATE,
                )
            )
        else:
            milestone_records.append(
                ClinicalMilestoneRecord(
                    milestone_id=m.milestone_id,
                    phase=m.phase,
                    status=True,
                    observed_value="Compliant",
                )
            )

    patient_rec = PatientPathwayRecord(
        patient_id=patient_id,
        specialty=specialty,
        procedure_name=f"Standard {specialty.value} Procedure",
        expected_los_days=expected_los_val,
        milestones=milestone_records,
    )
    result = ClinicalPathwayVarianceEngine.evaluate_patient_pathway(patient_rec)
    print("\n" + format_text_report(result.to_dict()))


def main():
    parser = argparse.ArgumentParser(
        description="Clinical Pathway Variance Agent - ERAS Adherence, Variance Analytics & LOS Impact"
    )
    parser.add_argument("--demo", action="store_true", help="Run with a realistic sample colorectal surgery case")
    parser.add_argument("--file", type=str, help="Path to patient pathway JSON file to evaluate")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    parser.add_argument("--interactive", action="store_true", help="Start interactive pathway evaluation prompt")
    parser.add_argument("--specialty", type=str, default="COLORECTAL", help="Specialty protocol (COLORECTAL, ORTHOPEDIC, BARIATRIC, GYNECOLOGIC, THORACIC)")
    parser.add_argument("--list-protocols", action="store_true", help="List all standard ERAS milestones by specialty")

    args = parser.parse_args()

    if args.list_protocols:
        for spec, m_list in ERAS_PROTOCOLS.items():
            print(f"\n=== Specialty: {spec.value} ({len(m_list)} milestones) ===")
            for m in m_list:
                print(f"  [{m.milestone_id}] ({m.phase.value}) {m.name} - Weight: {m.weight}")
        return

    if args.interactive:
        interactive_mode()
        return

    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            data = json.load(f)
        result = analyze_patient_dict(data)
    elif args.demo or len(sys.argv) == 1:
        data = get_sample_colorectal_case()
        result = analyze_patient_dict(data)
    else:
        parser.print_help()
        return

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(format_text_report(result))


if __name__ == "__main__":
    main()
