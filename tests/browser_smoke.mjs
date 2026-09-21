import assert from "node:assert/strict";
import { analyzeCase, PROTOCOLS } from "../docs/engine.mjs";

const milestones = Object.fromEntries(PROTOCOLS.COLORECTAL.map(([id]) => [id, { status: true, severity: "MODERATE", rootCause: "CLINICIAN_PRACTICE" }]));
Object.assign(milestones.INTRA_GDFT, { status: false, severity: "MAJOR", rootCause: "CLINICIAN_PRACTICE" });
Object.assign(milestones.POD0_MOBILIZATION, { status: false, severity: "MINOR", rootCause: "PATIENT_FACTOR" });
Object.assign(milestones.POD1_SOLID_DIET, { status: false, severity: "MINOR", rootCause: "PATIENT_FACTOR" });
Object.assign(milestones.POD1_FOLEY_REMOVAL, { status: false, severity: "MODERATE", rootCause: "CLINICIAN_PRACTICE" });
const result = analyzeCase({ specialty: "COLORECTAL", expectedLos: 3, dailyRate: 2400, milestones, complications: 0 });
assert.equal(result.totalMilestones, 16);
assert.equal(result.compliantMilestones, 12);
assert.equal(result.cumulativeComplianceIndex, 72.06);
assert.equal(result.totalVarianceBurdenScore, 23.25);
assert.equal(result.predictedExcessLosDays, 3.46);
assert.equal(result.estimatedExcessCostUsd, 11460);
assert.equal(result.varianceTier, "HIGH");
console.log("Browser engine parity smoke test passed.");

const empty = analyzeCase({ specialty: "ORTHOPEDIC", expectedLos: 2, dailyRate: 2000, milestones: {}, complications: 0 });
assert.equal(empty.compliantMilestones, 0);
assert.equal(empty.nonCompliantMilestones, PROTOCOLS.ORTHOPEDIC.length);
assert.equal(empty.varianceTier, "CRITICAL");
