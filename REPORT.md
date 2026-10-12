# Predicted Against Measured

Renato Jacinto — EGN 321 Assignment 6.2

The supplied classroom temperature measurements are systematically higher than the supplied predictions. The mean disagreement is +1.735 °C across 1,747 comparable points. The analysis quantifies that pattern and proposes tests to distinguish possible explanations.

## 1 Prediction

The predicted variable is temperature in degrees Celsius. The comparison imports the supplied prediction CSV without changing its values or fitting it to the measurements. The supplied notebook identifies this pair as classroom practice data. The earlier deterministic function, its parameters and its physical assumptions are not documented in these files. Therefore, this analysis demonstrates comparison of supplied output, but does not establish that the output came from my earlier tool. Linking the original function and its scenario remains necessary for that requirement.

## 2 Measurement

The measured variable is also temperature in degrees Celsius. The measured CSV contains 1,800 records with raw temperature, accepted temperature, status, reason and a nominal two-second interval. The sensor model and physical placement are unspecified. The records span October 8, 2026, from 18:00:00 to 19:05:52 UTC. Both files use matching sample numbers and timestamps. Matching fields alone do not verify the physical situation.

## 3 Alignment

Rows are joined by sample_number with one-to-one validation. Every paired timestamp is checked in UTC. There are no duplicate sample keys or mismatched paired timestamps. Only status OK with finite raw and accepted values, an accepted value within the classroom 0–50 °C range, and a finite prediction enters the comparison. MISSING, REJECTED and SUSPICIOUS rows remain in the original file and audit. Missing values are never replaced, interpolated or set to zero.

## 4 Comparison Results

For each valid pair, signed difference equals measured minus predicted. Absolute difference is the magnitude of that signed difference. The summary is point-weighted across valid pairs, rather than a time-weighted average.

| Metric | Value |
|---|---:|
| Comparable points | 1,747 |
| Mean signed difference | +1.734865 °C |
| Mean absolute difference | 1.734865 °C |
| Largest absolute difference | 2.603000 °C |
| Smallest signed difference | +0.539000 °C |
| Excluded recorded rows | 53 |

## 5 Pattern

All 1,747 valid differences are positive. Measured values exceed predictions by 0.539 to 2.603 °C. The five broad sample regions have mean residuals from 1.708 to 1.771 °C. The dominant observation is a persistent positive bias with smaller fluctuations. A single offset would not explain every fluctuation. Figures 1 and 2 show the pattern and preserve interruptions.

## 6 Cause 1 Sensor calibration offset

A positive calibration offset is a plausible hypothesis. Supporting evidence: every valid residual is positive, and regional means remain close to the overall +1.735 °C mean. Missing evidence: the sensor identity, calibration record, reference voltage and readings from a trusted thermometer. Verification test: place the sensor and a calibrated reference together at three stable temperatures across the observed range, allow both to settle, and record at least 30 simultaneous pairs at each level. Calculate sensor minus reference independently of the prediction model. An offset near +1.735 °C at all levels would support this explanation. Sensor-reference differences near zero within reference uncertainty would reject a substantial sensor offset. A difference that changes with temperature would suggest a scale error instead. This test has not been performed.

## 7 Cause 2 Simplified thermal response

The prediction may assume an instantaneous response while the sensor or its surroundings respond gradually. Supporting evidence: predictions jump at samples 450, 800, 1180 and 1500. At sample 800, the prediction rises 0.795 °C and the residual falls from 1.818 to 0.539 °C. At sample 1180, a 1.199 °C prediction drop is followed by the maximum residual of 2.603 °C at sample 1181. These transient changes are compatible with response lag, but do not explain the sustained positive bias by themselves. Missing evidence: the model response assumptions, sensor response specification and synchronized stimulus/reference records. Verification test: apply a controlled temperature step and log a calibrated reference and sensor on the same clock in the same location. Compare the times each reaches 50 and 90 percent of its final change after independently verifying calibration. A repeatable sensor delay beyond clock uncertainty would support lag. Simultaneous responses within that uncertainty would weaken this explanation. The experiment has not been performed.

## 8 Effect of Gaps and Filtering

The comparison excludes 33 MISSING, 14 REJECTED and 6 SUSPICIOUS rows, leaving 1,747 of 1,800 supplied records. Four clock jumps exceed two seconds and imply 177 unrecorded expected acquisition slots, separate from the 33 recorded MISSING rows. These are inferred opportunities, not recovered measurements. Plots break across clock jumps and excluded measurements. The accepted values used here equal their raw values, so there is no numerical evidence of smoothing delay. Status filtering still changes which observations are summarized and can exclude real transient events. Matching timestamps does not prove synchronized physical acquisition. Both schemas specify Celsius, but acquisition units and timing still depend on source metadata.

## 9 Conclusion

The supplied pair shows a consistent positive disagreement, with mean signed and absolute differences both 1.734865 °C. Calibration offset and simplified thermal response remain hypotheses that may explain different parts of the disagreement. Environmental assumptions and placement also remain unverified. The evidence supports neither as a proven cause. Keep the supplied predictions and measurements unchanged while obtaining reference measurements and the original model metadata. No conclusion describes excluded intervals.

## AI Review and Verification

ChatGPT assisted with file review, the comparison code, tests, notebook, documentation and report. Python computed the reported numbers from the supplied CSV files. Nine software tests passed, including sign checks, timestamp mismatch rejection and gap handling. These software tests do not verify physical causes. Ollama was not run. AI_LOG.md records this assistance and the unresolved provenance requirement.

## Figures

![Predicted and measured temperature](outputs/predicted_vs_measured.png)

Figure 1. Prediction output and accepted measured evidence. Gray bands identify unrecorded time intervals. The measured line also breaks at excluded rows.

![Signed residual](outputs/residual_difference.png)

Figure 2. Measured minus predicted. The dashed line indicates zero disagreement. Gaps are preserved.
