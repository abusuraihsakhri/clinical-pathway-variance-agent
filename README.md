# Clinical Pathway Variance Agent

A Python and browser-based tool for reviewing pathway adherence, recording perioperative variances, and calculating weighted compliance metrics across five built-in surgical pathway profiles.

> **Important:** The included milestone definitions, variance weights, LOS coefficients, cost coefficients, and thresholds are configurable heuristics for research, education, or quality-improvement workflows. They are not validated patient-level outcome predictions, clinical guidelines, or medical advice. Confirm all pathway definitions and thresholds against current local policy and source guidelines before operational use.

## Features

- Colorectal, orthopedic, bariatric, gynecologic, and thoracic pathway profiles.
- Raw milestone compliance and a weight-adjusted Cumulative Compliance Index (CCI).
- Weighted variance burden, root-cause categorization, and an algorithmic variance tier.
- Illustrative excess length-of-stay and cost estimates using explicit coefficients in `pathway_variance/engine.py`.
- Single-case CLI, JSON input, interactive review, and CSV batch processing.
- Static browser application suitable for GitHub Pages; all browser calculations run locally without a backend.

## Browser application

The web interface provides a compact light theme, dark-mode toggle, specialty selector, milestone checklist, variance severity/root-cause controls, an **Analyze pathway** button, and JSON export. It uses a dependency-free JavaScript port of the same weighting and coefficient logic as the Python engine. CI includes a parity smoke test for the example case.

No case data is transmitted by the browser application. Do not enter identifiable patient information into public/shared devices or files.

## Python quick start

Python 3.9 or newer is required. The core package has no runtime dependencies.

```bash
python cli.py --demo
python cli.py --list-protocols
python cli.py --file patient_case.json --json
python cli.py batch -i sample.csv -o results.csv
```

Install the package locally if you want the console commands:

```bash
python -m pip install .
clinical-pathway-variance-agent --demo
```

## CSV batch format

`sample.csv` demonstrates the accepted columns. `variances_milestones` uses semicolon-separated entries in this form:

```text
MILESTONE_ID:SEVERITY:ROOT_CAUSE:REASON
```

The parser preserves additional colons inside `REASON`. Unsupported specialties, milestone IDs, severities, root causes, and malformed boolean values are rejected rather than silently mapped to another pathway.

## Calculation model

For each specialty, the engine assigns a weight `w` to each milestone. Weighted adherence is:

```text
CCI = achieved milestone weight / total milestone weight × 100
```

For a recorded variance, the engine combines the milestone weight with a severity weight and applies fixed illustrative LOS and direct-cost coefficients. Complications add fixed burden, LOS, and direct-cost increments. These values are transparent in the source and should be recalibrated before any institutional use.

The output field currently named `clinical_risk_tier` is retained for API compatibility; it is an algorithmic **variance tier**, not a validated estimate of patient risk.

## Validation and testing

```bash
python -m pytest -p no:zarr -v
python cli.py batch -i sample.csv -o out_smoke.csv
node tests/browser_smoke.mjs
python -m build --wheel
```

GitHub Actions runs the Python test suite on Python 3.10–3.12, exercises the CLI batch path, checks the browser engine, builds the wheel, and verifies installed console entry points.

## Technology

- Python standard library (`dataclasses`, `enum`, `argparse`, `csv`, `json`)
- Dependency-free HTML/CSS/JavaScript browser UI
- GitHub Actions and GitHub Pages

The browser app targets current versions of Chrome, Edge, Firefox, and Safari. JavaScript must be enabled.

## License

MIT License. See `LICENSE`.
