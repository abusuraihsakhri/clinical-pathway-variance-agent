export const PROTOCOLS = {
  COLORECTAL: [
    ["PRE_FASTING","PREOPERATIVE","Carbohydrate loading & clear fluids",1.5],
    ["PRE_EDUCATION","PREOPERATIVE","Preoperative pathway counselling",1.0],
    ["PRE_ANTIBIOTIC","PREOPERATIVE","Prophylactic antibiotics",2.0],
    ["INTRA_GDFT","INTRAOPERATIVE","Goal-directed fluid strategy",2.5],
    ["INTRA_NORMOTHERMIA","INTRAOPERATIVE","Normothermia maintenance",2.0],
    ["INTRA_MULTIMODAL_ANALGESIA","INTRAOPERATIVE","Multimodal analgesia",2.5],
    ["INTRA_NO_ROUTINE_DRAIN","INTRAOPERATIVE","Avoid routine peritoneal drain",1.5],
    ["POD0_EARLY_FLUIDS","POD_0","Early oral fluids",2.0],
    ["POD0_MOBILIZATION","POD_0","Early mobilisation",2.5],
    ["POD0_OPIOID_MINIMIZATION","POD_0","Minimise IV opioids",2.0],
    ["POD1_SOLID_DIET","POD_1","Solid diet initiation",2.0],
    ["POD1_AMBULATION_6H","POD_1","Sustained mobilisation",2.5],
    ["POD1_FOLEY_REMOVAL","POD_1","Early urinary catheter removal",2.5],
    ["POD1_IVF_DISCONTINUATION","POD_1","Stop maintenance IV fluids",2.0],
    ["POD2_BOWEL_RECOVERY","POD_2","Gastrointestinal recovery",2.5],
    ["DISCHARGE_CRITERIA","DISCHARGE","Discharge readiness",3.0],
  ],
  ORTHOPEDIC: [
    ["PRE_EDUCATION","PREOPERATIVE","Preoperative joint education",1.0],
    ["PRE_TXA","PREOPERATIVE","Tranexamic acid pathway",2.5],
    ["INTRA_REGIONAL_BLOCK","INTRAOPERATIVE","Regional / neuraxial anaesthesia",2.5],
    ["INTRA_NORMOTHERMIA","INTRAOPERATIVE","Normothermia maintenance",1.5],
    ["POD0_PHYSICAL_THERAPY","POD_0","Same-day physical therapy",3.0],
    ["POD0_CRYO_COMPRESSION","POD_0","Cryotherapy / limb elevation",1.5],
    ["POD1_INDEPENDENT_TRANSFER","POD_1","Independent transfer & gait",2.5],
    ["POD1_MULTIMODAL_PAIN","POD_1","Oral multimodal pain regimen",2.0],
    ["DISCHARGE_CRITERIA","DISCHARGE","Discharge readiness",2.5],
  ],
  BARIATRIC: [
    ["PRE_FASTING","PREOPERATIVE","Carbohydrate loading",1.5],
    ["INTRA_MINIMAL_OPIOID","INTRAOPERATIVE","Opioid-sparing anaesthesia",2.5],
    ["POD0_EARLY_AMBULATION","POD_0","Early ambulation",3.0],
    ["POD0_SIP_PROTOCOL","POD_0","Graduated fluid protocol",2.0],
    ["POD1_ADEQUATE_HYDRATION","POD_1","Oral hydration target",2.0],
    ["POD1_PAIN_ORAL","POD_1","Oral analgesia conversion",2.0],
    ["DISCHARGE_CRITERIA","DISCHARGE","Discharge readiness",2.5],
  ],
  GYNECOLOGIC: [
    ["PRE_FASTING","PREOPERATIVE","Carbohydrate loading",1.5],
    ["INTRA_MULTIMODAL","INTRAOPERATIVE","Multimodal analgesia",2.5],
    ["INTRA_GDFT","INTRAOPERATIVE","Goal-directed fluid balance",2.0],
    ["POD0_EARLY_FEEDING","POD_0","Early oral intake",2.0],
    ["POD0_AMBULATION","POD_0","Early mobilisation",2.0],
    ["POD1_FOLEY_OUT","POD_1","Early urinary catheter removal",2.5],
    ["DISCHARGE_CRITERIA","DISCHARGE","Discharge readiness",2.5],
  ],
  THORACIC: [
    ["PRE_PULM_REHAB","PREOPERATIVE","Preoperative pulmonary preparation",1.5],
    ["INTRA_PARA_VERTEBRAL","INTRAOPERATIVE","Regional thoracic analgesia",2.5],
    ["INTRA_PROTECTIVE_VENT","INTRAOPERATIVE","Lung-protective ventilation",2.5],
    ["POD0_CHAIR_SITTING","POD_0","Out of bed to chair",2.5],
    ["POD1_CHEST_TUBE_MGMT","POD_1","Digital air-leak monitoring",3.0],
    ["POD1_AGGRESSIVE_PT","POD_1","Chest physiotherapy / ambulation",2.0],
    ["DISCHARGE_CRITERIA","DISCHARGE","Discharge readiness",2.5],
  ],
};

export const DEFAULT_LOS = { COLORECTAL: 3.0, ORTHOPEDIC: 2.0, BARIATRIC: 2.0, GYNECOLOGIC: 1.5, THORACIC: 3.5 };
export const SEVERITY_WEIGHTS = { MINOR: 1.0, MODERATE: 2.5, MAJOR: 5.0, CRITICAL: 10.0 };
export const LOS_COEFFICIENTS = { MINOR: 0.15, MODERATE: 0.65, MAJOR: 1.85, CRITICAL: 4.20 };
export const COST_COEFFICIENTS = { MINOR: 150, MODERATE: 650, MAJOR: 2200, CRITICAL: 7500 };

export function defaultSeverity(id, phase) {
  if (id.includes("COMPLICATION") || phase === "DISCHARGE") return "MAJOR";
  if (phase === "POD_0" || phase === "POD_1") return "MODERATE";
  return "MINOR";
}

export function analyzeCase({ specialty, expectedLos, dailyRate, milestones = {}, complications = 0 }) {
  const protocol = PROTOCOLS[specialty];
  if (!protocol) throw new Error(`Unsupported specialty: ${specialty}`);
  const baseLos = Number(expectedLos);
  const bedRate = Number(dailyRate);
  const complicationCount = Number(complications);
  if (!Number.isFinite(baseLos) || baseLos < 0) throw new Error("Expected LOS must be a non-negative number.");
  if (!Number.isFinite(bedRate) || bedRate < 0) throw new Error("Daily bed rate must be a non-negative number.");
  if (!Number.isInteger(complicationCount) || complicationCount < 0) throw new Error("Complication count must be a non-negative integer.");

  let compliant = 0, totalWeight = 0, achievedWeight = 0, burden = 0, excessLos = 0, directCost = 0;
  const rootCauses = { PATIENT_FACTOR: 0, CLINICIAN_PRACTICE: 0, HOSPITAL_SYSTEM: 0, SURGICAL_COMPLICATION: 0 };
  const variances = [];

  for (const [id, phase, name, weight] of protocol) {
    totalWeight += weight;
    const observed = milestones[id];
    if (!observed || observed.status !== false) {
      compliant += 1;
      achievedWeight += weight;
      continue;
    }
    const severity = observed.severity || defaultSeverity(id, phase);
    const rootCause = observed.rootCause || "CLINICIAN_PRACTICE";
    if (!(severity in SEVERITY_WEIGHTS)) throw new Error(`Unsupported severity for ${id}.`);
    if (!(rootCause in rootCauses)) throw new Error(`Unsupported root cause for ${id}.`);
    const losImpact = LOS_COEFFICIENTS[severity] * (weight / 2);
    burden += SEVERITY_WEIGHTS[severity] * weight;
    excessLos += losImpact;
    directCost += COST_COEFFICIENTS[severity];
    rootCauses[rootCause] += 1;
    variances.push({ id, name, phase, severity, rootCause, weight, losImpact, directCost: COST_COEFFICIENTS[severity] });
  }

  burden += complicationCount * 10;
  excessLos += complicationCount * 2.5;
  directCost += complicationCount * 3500;
  rootCauses.SURGICAL_COMPLICATION += complicationCount;
  const complianceRate = protocol.length ? compliant / protocol.length * 100 : 0;
  const cci = totalWeight ? achievedWeight / totalWeight * 100 : 0;
  let tier;
  if (burden <= 2.5 && cci >= 85) tier = "LOW";
  else if (burden <= 8 && cci >= 70) tier = "MODERATE";
  else if (burden <= 18 || cci >= 50) tier = "HIGH";
  else tier = "CRITICAL";
  return {
    specialty,
    totalMilestones: protocol.length,
    compliantMilestones: compliant,
    nonCompliantMilestones: protocol.length - compliant,
    complianceRatePct: round2(complianceRate),
    cumulativeComplianceIndex: round2(cci),
    totalVarianceBurdenScore: round2(burden),
    predictedExcessLosDays: round2(excessLos),
    predictedLosDays: round2(baseLos + excessLos),
    estimatedExcessCostUsd: round2(directCost + excessLos * bedRate),
    varianceTier: tier,
    rootCauseBreakdown: rootCauses,
    variances,
  };
}

function round2(value) { return Math.round((value + Number.EPSILON) * 100) / 100; }
