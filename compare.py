"""Compare supplied prediction output with accepted temperature evidence.

This program does not recreate an undocumented prediction model. It imports
the instructor-supplied prediction output unchanged and calculates residuals.
"""
from pathlib import Path
import argparse
import hashlib
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MEASURED_FILE = "EGN321_Module6_Assignment6_2_1800_Measured.csv"
PREDICTED_FILE = "EGN321_Module6_Assignment6_2_1800_Predictions.csv"


def validate_source(frame, required, name):
    """Reject ambiguous keys, malformed clocks and unexpected source ordering."""
    missing = set(required) - set(frame.columns)
    if missing:
        raise ValueError(f"{name}: missing columns {sorted(missing)}")
    frame = frame.copy()
    keys = pd.to_numeric(frame["sample_number"], errors="coerce")
    if keys.isna().any() or not np.isfinite(keys).all() or (keys <= 0).any() or (keys % 1 != 0).any():
        raise ValueError(f"{name}: sample numbers must be positive finite integers")
    if keys.duplicated().any():
        raise ValueError(f"{name}: duplicate sample numbers")
    if not keys.is_monotonic_increasing:
        raise ValueError(f"{name}: sample numbers must be increasing")
    frame["sample_number"] = keys.astype(int)
    # A naive timestamp would silently assume UTC. Require explicit timezone.
    clocks = frame["timestamp"].map(pd.Timestamp)
    if clocks.isna().any() or any(t.tzinfo is None for t in clocks):
        raise ValueError(f"{name}: timestamps must be valid and timezone-aware")
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    if frame["timestamp"].duplicated().any() or not frame["timestamp"].is_monotonic_increasing:
        raise ValueError(f"{name}: timestamps must be unique and increasing")
    return frame


def compare_frames(measured, predicted):
    """Align by sample, verify clocks, retain exclusions and compute valid pairs."""
    measured = validate_source(measured, ["sample_number", "timestamp",
        "measured_temperature_c", "accepted_temperature_c", "sensor_status",
        "status_reason", "expected_interval_seconds"], "Measured")
    predicted = validate_source(predicted, ["sample_number", "timestamp",
        "predicted_temperature_c"], "Predicted")
    measured["sensor_status"] = measured["sensor_status"].astype(str).str.strip().str.upper()
    if not measured["sensor_status"].isin(["OK", "MISSING", "REJECTED", "SUSPICIOUS"]).all():
        raise ValueError("Measured: unknown sensor status")
    interval = pd.to_numeric(measured["expected_interval_seconds"], errors="coerce")
    if not np.isfinite(interval).all() or (interval <= 0).any() or interval.nunique() != 1:
        raise ValueError("Measured: expected interval must be a constant positive number")
    measured["expected_interval_seconds"] = interval
    for col in ["measured_temperature_c", "accepted_temperature_c"]:
        measured[col] = pd.to_numeric(measured[col], errors="coerce")
    predicted["predicted_temperature_c"] = pd.to_numeric(predicted["predicted_temperature_c"], errors="coerce")
    audit = measured.merge(predicted.rename(columns={"timestamp": "prediction_timestamp"}),
        on="sample_number", how="outer", validate="one_to_one", indicator=True)
    both = audit["_merge"].eq("both")
    if (both & audit["timestamp"].ne(audit["prediction_timestamp"])).any():
        raise ValueError("Timestamp mismatch at matched sample number")
    audit["timestamp"] = audit["timestamp"].fillna(audit["prediction_timestamp"])
    audit = audit.sort_values("sample_number").reset_index(drop=True)
    both = audit["_merge"].eq("both")
    accepted = np.isfinite(audit["accepted_temperature_c"])
    prediction_valid = np.isfinite(audit["predicted_temperature_c"])
    raw_valid = np.isfinite(audit["measured_temperature_c"])
    # The 0-50 C limit comes from the supplied classroom status reasons.
    invalid_ok = both & audit["sensor_status"].eq("OK") & (
        ~accepted | ~raw_valid | ~audit["accepted_temperature_c"].between(0, 50))
    if invalid_ok.any():
        raise ValueError("OK row has invalid raw/accepted classroom temperature")
    valid = both & audit["sensor_status"].eq("OK") & accepted & prediction_valid
    audit["included_in_comparison"] = valid
    audit["comparison_reason"] = np.select(
        [audit["_merge"].eq("left_only"), audit["_merge"].eq("right_only"),
         ~audit["sensor_status"].eq("OK"), ~prediction_valid],
        ["No prediction for sample", "No measured row for sample", "Excluded by sensor status", "Nonfinite prediction"],
        default="Comparable")
    audit["measured_value"] = audit["accepted_temperature_c"].where(valid)
    audit["predicted_value"] = audit["predicted_temperature_c"]
    audit["signed_difference_c"] = (audit["measured_value"] - audit["predicted_value"]).where(valid)
    audit["absolute_difference_c"] = audit["signed_difference_c"].abs()
    audit["elapsed_minutes"] = (audit["timestamp"] - audit["timestamp"].min()).dt.total_seconds() / 60
    comparable = audit.loc[valid].copy()
    if comparable.empty:
        raise ValueError("No comparable points")
    gaps = []
    nominal = float(interval.iloc[0])
    for i in range(1, len(measured)):
        elapsed = (measured.iloc[i]["timestamp"] - measured.iloc[i-1]["timestamp"]).total_seconds()
        if elapsed > nominal:
            slots = elapsed / nominal - 1
            gaps.append({"previous_sample": int(measured.iloc[i-1]["sample_number"]),
                "next_sample": int(measured.iloc[i]["sample_number"]),
                "previous_timestamp": measured.iloc[i-1]["timestamp"].isoformat(),
                "next_timestamp": measured.iloc[i]["timestamp"].isoformat(),
                "elapsed_seconds": elapsed, "extra_seconds": elapsed - nominal,
                "unrecorded_expected_slots": int(slots) if slots.is_integer() else None})
    residual = comparable["signed_difference_c"]
    regions = []
    for lo, hi in [(1,450), (451,800), (801,1180), (1181,1500), (1501,1800)]:
        region = comparable[comparable.sample_number.between(lo, hi)]
        if len(region):
            regions.append({"region": f"{lo}-{hi}", "count": len(region),
                "mean_signed_difference_c": float(region.signed_difference_c.mean()),
                "mean_absolute_difference_c": float(region.absolute_difference_c.mean())})
    metrics = {"units": "degrees Celsius", "alignment_key": "sample_number",
        "original_measured_rows": len(measured), "original_prediction_rows": len(predicted),
        "comparable_points": len(comparable), "excluded_measured_rows": len(measured) - int(valid.sum()),
        "status_counts": {str(k): int(v) for k,v in measured.sensor_status.value_counts().items()},
        "timestamp_mismatches": 0, "mean_signed_difference_c": float(residual.mean()),
        "mean_absolute_difference_c": float(residual.abs().mean()),
        "minimum_signed_difference_c": float(residual.min()),
        "maximum_absolute_difference_c": float(residual.abs().max()),
        "positive_residual_count": int((residual > 0).sum()),
        "negative_residual_count": int((residual < 0).sum()),
        "zero_residual_count": int((residual == 0).sum()),
        "accepted_raw_difference_count": int(((comparable.accepted_temperature_c-comparable.measured_temperature_c).abs()>1e-9).sum()),
        "expected_interval_seconds": nominal,
        "elapsed_seconds": float((measured.timestamp.iloc[-1]-measured.timestamp.iloc[0]).total_seconds()),
        "clock_gap_count": len(gaps),
        "unrecorded_expected_slots": sum(x["unrecorded_expected_slots"] for x in gaps) if all(x["unrecorded_expected_slots"] is not None for x in gaps) else None,
        "clock_gaps": gaps, "region_summary": regions,
        "provenance": "Supplied classroom CSV pair; earlier model and physical sensor not identified"}
    return audit.drop(columns="_merge"), comparable.drop(columns="_merge"), metrics


def gap_plot_arrays(audit, column, expected_interval):
    """Insert only visual NaN separators, never fabricate observations."""
    x, y = [], []
    for i, row in audit.iterrows():
        if i:
            previous = audit.iloc[i-1]
            delta = (row.timestamp - previous.timestamp).total_seconds()
            if delta > expected_interval or row.sample_number-previous.sample_number != 1:
                x.append((previous.elapsed_minutes + row.elapsed_minutes) / 2)
                y.append(np.nan)
        x.append(row.elapsed_minutes)
        y.append(row[column])
    return np.asarray(x), np.asarray(y)


def save_plots(audit, metrics, output_dir):
    """Preserve both excluded sensor rows and unrecorded elapsed-time intervals."""
    plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False})
    for kind in ["predicted_vs_measured", "residual_difference"]:
        fig, ax = plt.subplots(figsize=(11, 4.2), layout="constrained")
        if kind == "predicted_vs_measured":
            for column, label, color in [("predicted_value", "Predicted output", "#2455A4"),
                                         ("measured_value", "Accepted measurement", "#C46321")]:
                x, y = gap_plot_arrays(audit, column, metrics["expected_interval_seconds"])
                ax.plot(x, y, label=label, color=color, linewidth=1.1)
            ax.set_ylabel("Temperature (°C)")
            ax.set_title("Predicted and measured temperature")
        else:
            x, y = gap_plot_arrays(audit, "signed_difference_c", metrics["expected_interval_seconds"])
            ax.plot(x, y, label="Measured − predicted", color="#246E57", linewidth=1)
            ax.axhline(0, color="#444444", linestyle="--", linewidth=1, label="Zero difference")
            ax.set_ylabel("Signed difference (°C)")
            ax.set_title("Temperature residual over elapsed time")
        for j, gap in enumerate(metrics["clock_gaps"]):
            origin = audit.timestamp.min()
            lo = (pd.Timestamp(gap["previous_timestamp"])-origin).total_seconds()/60
            hi = (pd.Timestamp(gap["next_timestamp"])-origin).total_seconds()/60
            ax.axvspan(lo, hi, color="#999999", alpha=.15,
                       label="Unrecorded time interval" if j == 0 else None)
        origin_label = audit.timestamp.min().strftime("%Y-%m-%d %H:%M UTC")
        ax.set_xlabel(f"Elapsed time (minutes from {origin_label})")
        ax.grid(alpha=.2)
        ax.legend(loc="best", fontsize=9)
        fig.savefig(output_dir / f"{kind}.png", dpi=180)
        plt.close(fig)


def run(measured_path, predicted_path, output_dir):
    """Write all evidence files from the original CSV inputs."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    audit, comparable, metrics = compare_frames(pd.read_csv(measured_path), pd.read_csv(predicted_path))
    audit.to_csv(output_dir / "alignment_audit.csv", index=False, float_format="%.6f")
    columns = ["sample_number", "timestamp", "sensor_status", "predicted_value", "measured_value",
               "signed_difference_c", "absolute_difference_c"]
    comparable[columns].to_csv(output_dir / "comparison_table.csv", index=False, float_format="%.6f")
    audit.loc[~audit.included_in_comparison].to_csv(output_dir / "excluded_rows.csv", index=False, float_format="%.6f")
    pd.DataFrame(metrics["clock_gaps"]).to_csv(output_dir / "clock_gaps.csv", index=False)
    pd.DataFrame(metrics["region_summary"]).to_csv(output_dir / "region_summary.csv", index=False, float_format="%.6f")
    names = ["comparable_points", "mean_signed_difference_c", "mean_absolute_difference_c", "maximum_absolute_difference_c"]
    pd.DataFrame({"metric": names, "value": [metrics[n] for n in names]}).to_csv(output_dir / "comparison_metrics.csv", index=False)
    metrics["source_files"] = [{"filename": Path(path).name,
        "sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest()} for path in [measured_path, predicted_path]]
    (output_dir / "deterministic_evidence.json").write_text(json.dumps(metrics, indent=2)+"\n", encoding="utf-8")
    save_plots(audit, metrics, output_dir)
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--measured", type=Path, default=ROOT / "data" / MEASURED_FILE)
    parser.add_argument("--predicted", type=Path, default=ROOT / "data" / PREDICTED_FILE)
    parser.add_argument("--output", type=Path, default=ROOT / "outputs")
    args = parser.parse_args()
    result = run(args.measured, args.predicted, args.output)
    print(f"Comparable points: {result['comparable_points']}")
    print(f"Mean signed difference: {result['mean_signed_difference_c']:.6f} °C")
    print(f"Mean absolute difference: {result['mean_absolute_difference_c']:.6f} °C")
    print(f"Maximum absolute difference: {result['maximum_absolute_difference_c']:.6f} °C")
    print(f"Saved outputs to: {args.output.resolve()}")
