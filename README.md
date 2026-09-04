# Clinical Pathway Variance Agent

> **Domain:** Perioperative Operations & Evidence-Based Clinical Pathways  
> **Clinical Standard:** ERAS® (Enhanced Recovery After Surgery) Society Guidelines  
> **Core Objective:** Multi-specialty pathway compliance tracking, variance burden quantification, LOS regression modeling, and actionable clinical remediation.

---

## 📖 Clinical Overview

The **Clinical Pathway Variance Agent** evaluates surgical patient trajectories against validated Enhanced Recovery After Surgery (ERAS®) multimodal protocols. Surgical pathways establish evidence-based milestones across preoperative, intraoperative, and postoperative recovery days (POD 0 through discharge).

Deviations from standard care pathways—termed **clinical variances**—prolong hospital Length of Stay (LOS), increase excess hospital costs, and predispose patients to preventable complications (such as CAUTIs, surgical site infections, pulmonary complications, and prolonged postoperative ileus).

### Key Clinical Capabilities
- **Multi-Specialty ERAS Protocols:** Built-in protocol benchmarks for **Colorectal**, **Orthopedic**, **Bariatric**, **Gynecologic**, and **Thoracic** surgery.
- **Quantitative Compliance Tracking:** Calculates raw compliance rate (%) alongside weight-adjusted **Cumulative Compliance Index (CCI)**.
- **Total Variance Burden Score (TVBS):** Weighted severity burden reflecting physiological impact and systemic deviation.
- **LOS & Cost Impact Projections:** Actuarial regression models projecting incremental inpatient days and direct intervention expenses.
- **Root-Cause Attribution:** Categorization across Patient Factors, Clinician Practice, Hospital System, and Surgical Complications.
- **Targeted Clinical Recommendations:** Automated action plans for CAUTI prevention, fluid management audit, and multimodal opioid-sparing analgesia.

---

## 📐 Clinical Methodology & Mathematical Formulations

### 1. Cumulative Compliance Index (CCI)

Each clinical milestone $m_i$ possesses an evidence-based clinical importance weight $w_i \in [1.0, 3.0]$. The Cumulative Compliance Index quantifies weighted milestone concordance:

$$\text{CCI} = \left( \frac{\sum_{i \in \text{Compliant}} w_i}{\sum_{i=1}^{N} w_i} \right) \times 100\%$$

| Compliance Range | Tier Status | Clinical Action |
|:---|:---|:---|
| **$\ge 85.0\%$** | Optimal Adherence | Maintain standard pathway protocols |
| **$70.0\% - 84.9\%$** | Acceptable / Moderate Variance | Unit-level clinical variance audit |
| **$< 70.0\%$** | Suboptimal Adherence | Mandatory multidisciplinary perioperative review |

### 2. Total Variance Burden Score (TVBS)

Each detected variance is assigned a severity weight $S(v)$ based on clinical risk:

$$\text{TVBS} = \sum_{v \in \text{Variances}} \Big( S(v) \times w_v \Big) + \sum_{c \in \text{Complications}} 10.0$$

| Variance Severity | Weight ($S$) | Clinical Example |
|:---|:---|:---|
| **MINOR** | 1.0 | Delayed mobilization (<2 hours late), mild PONV resolved with single dose |
| **MODERATE** | 2.5 | Unplanned Foley catheter retention past POD 1, delayed solid diet >24h |
| **MAJOR** | 5.0 | Fluid overload >35 mL/kg/day, omission of regional block, severe ileus |
| **CRITICAL** | 10.0 | Anastomotic breakdown, re-intubation, unplanned re-operation or ICU transfer |

### 3. Predicted Excess Length of Stay & Cost Impact

$$\Delta \text{LOS}_{\text{excess}} = \sum_{v \in \text{Variances}} \left( \beta_{\text{LOS}}(S_v) \times \frac{w_v}{2.0} \right) + (2.50 \times N_{\text{complications}})$$

$$\text{Total Predicted LOS} = \text{Expected LOS}_{\text{baseline}} + \Delta \text{LOS}_{\text{excess}}$$

$$\text{Estimated Excess Cost} = \sum_{v} C_{\text{direct}}(S_v) + (3500.00 \times N_{\text{complications}}) + (\Delta \text{LOS}_{\text{excess}} \times \text{Daily Bed Rate})$$

| Severity | $\beta_{\text{LOS}}$ (Days) | $C_{\text{direct}}$ (USD) |
|:---|:---|:---|
| **MINOR** | +0.15 days | $150.00 |
| **MODERATE** | +0.65 days | $650.00 |
| **MAJOR** | +1.85 days | $2,200.00 |
| **CRITICAL** | +4.20 days | $7,500.00 |

---

## 🏥 Supported Specialty Protocols

| Specialty | Key Milestones Evaluated | Benchmark LOS |
|:---|:---|:---|
| **COLORECTAL** | CHO loading, GDFT (<30 mL/kg), multimodal analgesia, early oral fluids, POD 1 Foley removal, POD 2 bowel recovery | 3.0 days |
| **ORTHOPEDIC** | Joint education class, pre-incision TXA, neuraxial/adductor canal block, same-day PT ambulation, cryo-compression | 2.0 days |
| **BARIATRIC** | CHO drink 2h pre-op, opioid-sparing anesthesia, 2h post-op ambulation, graduated 30-50 mL/h sip protocol | 2.0 days |
| **GYNECOLOGIC** | Pre-op CHO loading, TAP block + NSAIDs, euvolemic fluid balance, early feeding, <=24h Foley catheter removal | 1.5 days |
| **THORACIC** | Inspiratory muscle training, thoracic paravertebral block, lung-protective ventilation, digital air leak monitoring | 3.5 days |

---

## 💻 CLI Quickstart & Usage

### 1. Interactive Case Evaluation
Walk through an interactive questionnaire to evaluate an individual patient against specialty ERAS milestones:
```bash
python cli.py --interactive
```

### 2. Demonstration Colorectal Case
Run the clinical variance engine on a realistic laparoscopic colectomy case:
```bash
python cli.py --demo
```

### 3. List Specialty Milestones
Inspect ERAS Society standardized milestone catalog and weights:
```bash
python cli.py --list-protocols
```

### 4. JSON File Evaluation
Evaluate a single patient record JSON file:
```bash
python cli.py --file patient_case.json --json
```

### 5. High-Throughput Batch Processing
Process cohort data from CSV format with automated variance calculation and impact forecasting:
```bash
python cli.py batch -i sample.csv -o results.csv
```
Or use the equivalent flag syntax:
```bash
python cli.py batch --input sample.csv --output results.csv
```

---

## 📊 CSV Input & Output Data Schema

### Input Columns (`sample.csv`)

| Column Name | Type | Description | Example |
|:---|:---|:---|:---|
| `patient_id` | String | Unique patient or case identifier | `PT-COL-001` |
| `specialty` | Enum | Surgical specialty protocol | `COLORECTAL` |
| `procedure_name` | String | Surgical procedure descriptor | `Laparoscopic Sigmoid Colectomy` |
| `expected_los_days` | Float | Benchmark length of stay in days | `3.0` |
| `actual_los_days` | Float (Opt) | Observed actual discharge LOS | `3.5` |
| `daily_bed_rate_usd` | Float | Hospital per-diem ward/ICU bed rate | `2400.0` |
| `variances_milestones`| String (Opt) | Delimited custom non-compliant milestones (`ID:SEVERITY:ROOT_CAUSE:REASON;...`) | `INTRA_GDFT:MAJOR:CLINICIAN_PRACTICE:Excess fluid` |
| `complications` | String (Opt) | Semicolon-delimited surgical complications | `Prolonged Air Leak` |

### Output Generated Columns (`results.csv`)

| Output Field | Description |
|:---|:---|
| `total_milestones` | Total protocol milestones evaluated for the specialty |
| `compliant_milestones` | Number of successfully achieved milestones |
| `compliance_rate_pct` | Unweighted adherence percentage |
| `cumulative_compliance_index` | Weight-adjusted Cumulative Compliance Index (CCI %) |
| `total_variance_burden_score` | Cumulative weighted variance burden score (TVBS) |
| `clinical_risk_tier` | Multi-tier classification: `LOW`, `MODERATE`, `HIGH`, `CRITICAL` |
| `predicted_total_los_days` | Model-projected total hospital stay (days) |
| `predicted_excess_los_days` | Incremental days over clinical benchmark |
| `estimated_excess_cost_usd` | Total direct + indirect excess operational expense |
| `variance_count` | Total distinct clinical pathway variances recorded |

---

## 🧪 Verification & Testing

Execute the test suite across all clinical calculation engines and CLI batch processors:
```bash
python -m pytest -p no:zarr -v
```

Execute the CLI batch smoke test:
```bash
python cli.py batch -i sample.csv -o out_smoke.csv
```

---

## 📄 License
MIT License. Developed for clinical operational excellence and evidence-based surgical quality improvement.
