# Clinical Pathway Variance Agent

> **Perioperative Operations & ERAS® Care Protocol Adherence Engine**  
> Reference Standard: **ERAS® Society Guidelines for Perioperative Care (Colorectal, Orthopedic, Bariatric, Gynecologic, Thoracic)**

---

## Overview

The **Clinical Pathway Variance Agent** is a clinical operations analytics engine designed to detect, track, and remediate clinical variances across multi-phase Enhanced Recovery After Surgery (ERAS®) pathways.

By continuously auditing patient milestones against evidence-based perioperative standards, the engine quantifies the **Cumulative Compliance Index (CCI)**, categorizes variance root causes (**Patient**, **Clinician**, **Hospital System**, or **Surgical Complication**), and predicts excess **Length of Stay (LOS)** and financial cost impact.

```
                    +----------------------------------------------+
                    |    Multi-Phase Perioperative Milestone Data  |
                    |   (Pre-op, Intra-op, POD 0, POD 1, POD 2-3+) |
                    +----------------------------------------------+
                                           |
                                           v
                    +----------------------------------------------+
                    |    Clinical Pathway Variance Engine          |
                    |  - Specialty Protocol Rule Matching          |
                    |  - Severity Weighting (Minor to Critical)    |
                    |  - Root-Cause Attribution & Matrix           |
                    +----------------------------------------------+
                                           |
                                           v
                    +----------------------------------------------+
                    |           Decision Support Outputs           |
                    |  - Cumulative Compliance Index (CCI %)       |
                    |  - Predicted Excess LOS (Days)               |
                    |  - Financial Cost Deviation ($ USD)          |
                    |  - Targeted Actionable Remediation Plans     |
                    +----------------------------------------------+
```

---

## Clinical Domain & Formulas

### 1. Cumulative Compliance Index (CCI)
The Cumulative Compliance Index measures weighted protocol concordance across all phases:

$$\text{CCI} = \frac{\sum_{i=1}^{N} w_i \cdot c_i}{\sum_{i=1}^{N} w_i} \times 100\%$$

where $w_i$ is the clinical importance weight of milestone $i$, and $c_i \in \{0, 1\}$ denotes adherence.

### 2. Variance Burden Score (VBS)
Quantifies the overall severity and friction introduced by clinical deviations:

$$\text{VBS} = \sum_{v \in \text{Variances}} \text{SeverityWeight}(v) \cdot w_v$$

- **Minor** (Weight = 1.0): Brief timing delays, minimal clinical impact.
- **Moderate** (Weight = 2.5): Unwarranted practice variation (e.g., delayed Foley catheter removal).
- **Major** (Weight = 5.0): Substantial deviation (e.g., intraoperative fluid overload > 40 mL/kg/day).
- **Critical** (Weight = 10.0): Acute safety events or surgical complications (e.g., anastomotic leak).

### 3. Predicted Excess Length of Stay & Financial Impact
$$\widehat{\Delta \text{LOS}} = \sum_{v} \beta_{\text{sev}(v)} \cdot \frac{w_v}{2.0} + 2.5 \cdot N_{\text{complications}}$$

$$\Delta \text{Cost} = \sum_{v} \text{DirectCost}(v) + \left(\widehat{\Delta \text{LOS}} \times \text{DailyBedRate}\right)$$

---

## Supported Surgical Specialties & Protocols

| Specialty | Key Tracked ERAS Milestones | Target Benchmark |
| :--- | :--- | :--- |
| **Colorectal** | Pre-op CHO loading, GDFT (<30 mL/kg/day), TAP block, POD0 ambulation, POD1 Foley removal | LOS ≤ 3.0 days, CCI ≥ 80% |
| **Orthopedic** | Pre-incision TXA, regional adductor/spinal block, same-day PT (POD 0), cryocompression | LOS ≤ 2.0 days, CCI ≥ 85% |
| **Bariatric** | Opioid-sparing anesthesia, ambulation ≤ 2h, graduated sips protocol, early oral pain regimen | LOS ≤ 1.5 days, CCI ≥ 85% |
| **Gynecologic** | Zero-balance fluid strategy, TAP block, early feeding ≤ 4h, Foley catheter out ≤ 24h | LOS ≤ 1.0 day, CCI ≥ 85% |
| **Thoracic** | Inspiratory muscle training, ESP/paravertebral block, lung-protective ventilation, digital air leak monitoring | LOS ≤ 3.0 days, CCI ≥ 80% |

---

## Command-Line Interface (CLI)

### Demonstration Mode
Run a built-in analysis of a representative colorectal surgery case:
```bash
python cli.py --demo
```

### JSON Output
Export the complete structured analysis as JSON:
```bash
python cli.py --demo --json
```

### Interactive Assessment Mode
Evaluate a patient case in real-time with step-by-step milestone prompts:
```bash
python cli.py --interactive
```

### Protocol Inspection
List all standard milestones and weights across all specialties:
```bash
python cli.py --list-protocols
```

### Custom Patient File Evaluation
```bash
python cli.py --file patient_case.json
```

---

## Python API Usage

```python
from pathway_variance import (
    ClinicalPathwayVarianceEngine,
    PatientPathwayRecord,
    ClinicalMilestoneRecord,
    SurgicalSpecialty,
    PathwayPhase,
    VarianceSeverity,
    VarianceRootCause,
    analyze_patient_dict,
)

# Option A: Dictionary-driven workflow
payload = {
    "patient_id": "PT-COLO-442",
    "specialty": "COLORECTAL",
    "expected_los_days": 3.0,
    "milestones": [
        {"milestone_id": "PRE_FASTING", "status": True},
        {"milestone_id": "INTRA_GDFT", "status": False, "severity": "MAJOR", "root_cause": "CLINICIAN_PRACTICE"},
        {"milestone_id": "POD1_FOLEY_REMOVAL", "status": False, "severity": "MODERATE", "root_cause": "CLINICIAN_PRACTICE"},
    ]
}

result = analyze_patient_dict(payload)
print(f"Compliance Index: {result['cumulative_compliance_index']}%")
print(f"Predicted Excess LOS: +{result['predicted_excess_los_days']} days")
print(f"Excess Cost: ${result['estimated_excess_cost_usd']:,.2f}")
```

---

## Test Suite Execution

Run the complete test suite verifying protocol calculations, root-cause matrices, and edge cases:

```bash
python -m unittest discover -s tests -v
```

```
test_full_pipeline_colorectal ... ok
test_root_cause_categorization ... ok
test_orthopedic_pathway_evaluation ... ok
test_thoracic_pathway_evaluation ... ok
test_gynecologic_pathway_evaluation ... ok
test_bed_rate_scaling ... ok
test_complication_additive_impact ... ok
----------------------------------------------------------------------
Ran 23 tests in 0.003s

OK
```

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
