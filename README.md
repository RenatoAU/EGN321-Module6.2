# EGN 321 Assignment 6.2 — Predicted Against Measured

Author: Renato Jacinto

This project compares the two **supplied classroom CSV files**. It calculates residuals deterministically, preserves excluded evidence and creates plots that show gaps.

## Main result

| Metric | Value |
|---|---:|
| Supplied measured records | 1,800 |
| Comparable points | 1,747 |
| Mean signed difference | +1.734865 °C |
| Mean absolute difference | 1.734865 °C |
| Maximum absolute difference | 2.603000 °C |

Every valid residual is positive. That supports a persistent disagreement, but does not establish its physical cause.

## Source and scope

- `data/EGN321_Module6_Assignment6_2_1800_Measured.csv`: supplied measurements; preserved byte for byte.
- `data/EGN321_Module6_Assignment6_2_1800_Predictions.csv`: supplied prediction output; preserved byte for byte.
- The uploaded Student Guide, Report Template, Worked Example and Ollama v2 notebook define the workflow. The example's 20/22 °C scenario is illustrative; it was not substituted for the CSV data.
- Instructor repository: https://github.com/ivansuarez-AU/EGN321_Module6_Assignment6_2
- Exact earlier model function, parameters, physical sensor identity, placement and acquisition method are absent from the supplied materials. The notebook calls the CSV pair practice files. This package does not identify them as my personally collected Module 5 readings.
- Both variables are temperature in Celsius. Sample numbers and timestamps match. Matching columns does not establish identical physical conditions.

**Earlier-tool requirement:** the supplied prediction output is included, but its connection to my earlier tool is unverified. Add the original function and scenario metadata, or obtain instructor confirmation that this classroom pair satisfies that requirement. Do not relabel a tank-volume or valve-selection output as temperature. If replacing the inputs, use an independent deterministic temperature model and measurements of the same situation, units and times.

## Run on Windows or in VS Code

Extract the ZIP. Open a terminal in the folder containing this README.

```powershell
py -m pip install -r requirements.txt
py src/compare.py
py -m unittest discover -s tests -v
```

If `py` is unavailable, use `python` for each command. The main command creates the evidence files and two PNG plots inside `outputs`. No typed engineering inputs, Ollama installation or network service are required to run the comparison.

To compare another properly documented pair with the same schema:

```powershell
py src/compare.py --measured data/my_measured.csv --predicted data/my_predictions.csv --output outputs
```

Changing inputs requires updating the report and provenance notes. The supplied 0–50 °C classroom rule must be reviewed if a different sensor or operating range is used.

## Optional notebook

`Assignment6_2_Comparison.ipynb` provides the same pipeline, plots and evidence review in a local notebook. Open it in VS Code with the Jupyter extension and select a Python environment containing the requirements. If prompted, install `ipykernel` in that environment. Run cells from top to bottom with the project folder as the working directory. The delivered notebook has no claimed Jupyter execution results; the shared calculation pipeline was run and tested through the command line.

The original Ollama section is optional under the assignment guide. It was not executed here, and no Ollama responses are claimed. Actual ChatGPT assistance is recorded in `AI_LOG.md`.

## Calculation and alignment

1. Validate required columns, increasing positive integer keys and timezone-aware timestamps.
2. Reject duplicate keys and mismatched timestamps for a matched sample.
3. Join by `sample_number`, keeping an audit of unmatched or excluded evidence.
4. Compare only finite accepted temperatures with `sensor_status == OK` and finite predictions. OK temperatures must obey the supplied 0–50 °C classroom range.
5. Calculate `signed_difference_c = measured_value - predicted_value` and `absolute_difference_c = abs(signed_difference_c)`.
6. Summarize valid pairs only. Means are point-weighted, not time-weighted.
7. Break the measured and residual lines at excluded rows; break all series across unrecorded timestamp intervals. Plotting separators are NaN markers, not generated measurements.

The source statuses are retained rather than recreated from an undocumented suspicious-reading threshold. Suspicious readings are excluded according to the supplied notebook even when their accepted field is numeric. No smoothing, offset correction, model refitting or interpolation is applied.

## Files and deliverables

| Required item | File |
|---|---|
| Measured sensor data | `data/EGN321_Module6_Assignment6_2_1800_Measured.csv` |
| Supplied prediction output | `data/EGN321_Module6_Assignment6_2_1800_Predictions.csv` |
| Reproducible comparison | `src/compare.py` |
| Comparison table | `outputs/comparison_table.csv` |
| Two plots | `outputs/predicted_vs_measured.png`, `outputs/residual_difference.png` |
| Summary metrics | `outputs/comparison_metrics.csv` |
| Report and verification proposals | `Comparison_Report.docx`, `REPORT.md` |
| AI disclosure | `AI_LOG.md` |
| Complete alignment audit | `outputs/alignment_audit.csv` |
| Excluded rows and timing evidence | `outputs/excluded_rows.csv`, `outputs/clock_gaps.csv` |
| Regional pattern and source hashes | `outputs/region_summary.csv`, `outputs/deterministic_evidence.json` |
| Software validation | `tests/test_comparison.py` |
| Notebook | `Assignment6_2_Comparison.ipynb` |
| Final actions | `SUBMISSION_CHECKLIST.md` |

## Missing data and interpretation

There are 33 recorded MISSING rows, 14 REJECTED rows and 6 SUSPICIOUS rows. Four clock gaps imply another 177 unrecorded two-second acquisition opportunities over the 65 minute 52 second span. No measurements were invented at those opportunities. The 53 recorded exclusions and the 177 unrecorded opportunities are different counts. Retained accepted readings equal their raw readings, so this dataset does not show a numeric smoothing transformation. Exclusion may still hide real transients.

See the report for calibration and thermal-response hypotheses, missing evidence and one verification experiment per cause. No physical verification experiment has been performed.

## Validation

Nine unit tests passed. They verify residual sign and magnitude, source exclusions, duplicates, timestamp mismatches, timezone handling, nonfinite predictions, unmatched samples and visual gap separators. The supplied CSV results were also checked against an independent standard-library calculation. Software validation is distinct from the proposed physical experiments.

## GitHub submission

Create your own repository, for example `EGN321-Assignment6-2`. Upload the contents of this folder while preserving its subfolders. Include the CSV data, outputs, code, tests and documentation. The instructor repository above is the assignment source, not your submission repository. Copy your own repository URL into `SUBMISSION_CHECKLIST.md` and submit that link.

A useful commit sequence is:

1. `Add supplied temperature data and provenance notes`
2. `Implement deterministic residual comparison and alignment checks`
3. `Preserve excluded readings and clock gaps in plots`
4. `Add comparison validation tests`
5. `Document results verification proposals and AI assistance`
