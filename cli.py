#!/usr/bin/env python3
"""
Command-Line Interface for Clinical Pathway Variance Agent
==========================================================
Provides interactive analysis, single-case evaluation, batch processing,
benchmark testing, and JSON output formatting for ERAS pathway adherence.
"""

import csv
import sys
import os
import json
import argparse
from typing import Dict, Any, List

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


def process_csv_batch(input_csv: str, output_csv: str) -> int:
    """Batch process surgical cases from a CSV file and output evaluation metrics."""
    with open(input_csv, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    generated_fields = [
        "total_milestones",
        "compliant_milestones",
        "compliance_rate_pct",
        "cumulative_compliance_index",
        "total_variance_burden_score",
        "clinical_risk_tier",
        "predicted_total_los_days",
        "predicted_excess_los_days",
        "estimated_excess_cost_usd",
        "variance_count",
    ]
    out_fields = fieldnames + [name for name in generated_fields if name not in fieldnames]

    out_rows = []
    for row_number, r in enumerate(rows, start=2):
        patient_id = (r.get("patient_id") or "PT-UNKNOWN").strip() or "PT-UNKNOWN"
        spec_str = (r.get("specialty") or "COLORECTAL").strip().upper()
        try:
            specialty = SurgicalSpecialty(spec_str)
        except ValueError as exc:
            raise ValueError(
                f"Row {row_number} ({patient_id}): unsupported specialty '{spec_str}'."
            ) from exc

        protocol = ClinicalPathwayVarianceEngine.get_protocol_milestones(specialty)
        protocol_ids = {m.milestone_id for m in protocol}

        # Parse variance milestones if provided
        # Format: "MILESTONE_ID:SEVERITY:ROOT_CAUSE:REASON;..."
        var_milestones_str = r.get("variances_milestones", "").strip()
        custom_variances: Dict[str, Dict[str, Any]] = {}
        if var_milestones_str:
            for item in var_milestones_str.split(";"):
                parts = item.strip().split(":", 3)
                if parts and parts[0]:
                    m_id = parts[0].strip()
                    if m_id not in protocol_ids:
                        raise ValueError(
                            f"Row {row_number} ({patient_id}): unknown milestone '{m_id}' "
                            f"for specialty {specialty.value}."
                        )
                    sev = parts[1].strip() if len(parts) > 1 else "MODERATE"
                    rc = parts[2].strip() if len(parts) > 2 else "PATIENT_FACTOR"
                    reason = parts[3].strip() if len(parts) > 3 else f"Variance in {m_id}"
                    custom_variances[m_id] = {
                        "severity": sev,
                        "root_cause": rc,
                        "reason": reason,
                    }

        milestone_records: List[ClinicalMilestoneRecord] = []
        for m in protocol:
            if m.milestone_id in custom_variances:
                c_info = custom_variances[m.milestone_id]
                try:
                    sev = VarianceSeverity(c_info["severity"].upper())
                except ValueError as exc:
                    raise ValueError(
                        f"Row {row_number} ({patient_id}): invalid severity "
                        f"'{c_info['severity']}' for milestone {m.milestone_id}."
                    ) from exc
                try:
                    rc = VarianceRootCause(c_info["root_cause"].upper())
                except ValueError as exc:
                    raise ValueError(
                        f"Row {row_number} ({patient_id}): invalid root cause "
                        f"'{c_info['root_cause']}' for milestone {m.milestone_id}."
                    ) from exc

                milestone_records.append(
                    ClinicalMilestoneRecord(
                        milestone_id=m.milestone_id,
                        phase=m.phase,
                        status=False,
                        observed_value="Non-compliant",
                        variance_reason=c_info["reason"],
                        root_cause=rc,
                        severity=sev,
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

        complications = []
        comp_str = r.get("complications", "").strip()
        if comp_str:
            complications = [c.strip() for c in comp_str.split(";") if c.strip()]

        try:
            expected_los = float(r.get("expected_los_days", 3.0) or 3.0)
            actual_los_str = (r.get("actual_los_days") or "").strip()
            actual_los = float(actual_los_str) if actual_los_str else None
            daily_rate = float(r.get("daily_bed_rate_usd", 2400.0) or 2400.0)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Row {row_number} ({patient_id}): LOS and daily bed-rate fields must be numeric."
            ) from exc
        if expected_los < 0 or daily_rate < 0 or (actual_los is not None and actual_los < 0):
            raise ValueError(
                f"Row {row_number} ({patient_id}): LOS and daily bed-rate values must be non-negative."
            )

        patient_rec = PatientPathwayRecord(
            patient_id=patient_id,
            specialty=specialty,
            procedure_name=r.get("procedure_name", f"Standard {specialty.value} Procedure"),
            expected_los_days=expected_los,
            actual_los_days=actual_los,
            daily_bed_rate_usd=daily_rate,
            milestones=milestone_records,
            complications=complications,
        )

        analysis = ClinicalPathwayVarianceEngine.evaluate_patient_pathway(patient_rec)
        row_dict = {
            key: ("'" + value if isinstance(value, str) and value.startswith(("=", "+", "-", "@")) else value)
            for key, value in r.items()
        }
        row_dict["total_milestones"] = analysis.total_milestones
        row_dict["compliant_milestones"] = analysis.compliant_milestones
        row_dict["compliance_rate_pct"] = f"{analysis.compliance_rate_pct:.1f}"
        row_dict["cumulative_compliance_index"] = f"{analysis.cumulative_compliance_index:.1f}"
        row_dict["total_variance_burden_score"] = f"{analysis.total_variance_burden_score:.1f}"
        row_dict["clinical_risk_tier"] = analysis.clinical_risk_tier
        row_dict["predicted_total_los_days"] = f"{analysis.predicted_los_days:.2f}"
        row_dict["predicted_excess_los_days"] = f"{analysis.predicted_excess_los_days:.2f}"
        row_dict["estimated_excess_cost_usd"] = f"{analysis.estimated_excess_cost_usd:.2f}"
        row_dict["variance_count"] = len(analysis.variances)
        out_rows.append(row_dict)

    with open(output_csv, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Successfully processed {len(out_rows)} records from '{input_csv}' -> '{output_csv}'.")
    return len(out_rows)


def main():
    parser = argparse.ArgumentParser(
        prog="cli.py",
        description="Clinical Pathway Variance Agent - ERAS Adherence, Variance Analytics & LOS Impact",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Batch subcommand
    batch_parser = subparsers.add_parser("batch", help="Batch process clinical pathway records from CSV")
    batch_parser.add_argument("-i", "--input", required=True, help="Path to input CSV file")
    batch_parser.add_argument("-o", "--output", default="results.csv", help="Path to output results CSV file")

    # Root options
    parser.add_argument("--batch", type=str, metavar="INPUT_CSV", help="Shortcut to batch process CSV file")
    parser.add_argument("-i", "--input", type=str, help="Input CSV file path for batch mode")
    parser.add_argument("-o", "--output", type=str, default="results.csv", help="Output CSV file path for batch mode")
    parser.add_argument("--demo", action="store_true", help="Run with a realistic sample colorectal surgery case")
    parser.add_argument("--file", type=str, help="Path to patient pathway JSON file to evaluate")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    parser.add_argument("--interactive", action="store_true", help="Start interactive pathway evaluation prompt")
    parser.add_argument("--specialty", type=str, default="COLORECTAL", help="Specialty protocol (COLORECTAL, ORTHOPEDIC, BARIATRIC, GYNECOLOGIC, THORACIC)")
    parser.add_argument("--list-protocols", action="store_true", help="List all standard ERAS milestones by specialty")

    args = parser.parse_args()

    if args.command == "batch":
        process_csv_batch(args.input, args.output)
        return

    if args.batch:
        out = args.output if args.output else "results.csv"
        process_csv_batch(args.batch, out)
        return

    if args.input:
        out = args.output if args.output else "results.csv"
        process_csv_batch(args.input, out)
        return

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

