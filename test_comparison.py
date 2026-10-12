"""Run with python -m unittest discover -s tests -v."""
import unittest
import numpy as np
import pandas as pd
from src.compare import compare_frames, gap_plot_arrays, ROOT, MEASURED_FILE, PREDICTED_FILE


def tiny_sources():
    measured = pd.DataFrame({
        'sample_number': [1,2,3],
        'timestamp': ['2026-10-08T18:00:00+00:00', '2026-10-08T18:00:02+00:00', '2026-10-08T18:00:10+00:00'],
        'measured_temperature_c': [19.0,np.nan,23.0],
        'accepted_temperature_c': [19.0,np.nan,23.0],
        'sensor_status': ['OK','MISSING','OK'],
        'status_reason': ['','No value',''],
        'expected_interval_seconds': [2,2,2]})
    predicted = measured[['sample_number','timestamp']].copy()
    predicted['predicted_temperature_c'] = [20.0,20.0,20.0]
    return measured,predicted


class ComparisonTests(unittest.TestCase):
    def test_signed_absolute_and_missing(self):
        m,p=tiny_sources()
        audit,valid,metrics=compare_frames(m,p)
        self.assertEqual(valid.signed_difference_c.tolist(),[-1.0,3.0])
        self.assertEqual(valid.absolute_difference_c.tolist(),[1.0,3.0])
        self.assertEqual(metrics['mean_signed_difference_c'],1.0)
        self.assertEqual(metrics['mean_absolute_difference_c'],2.0)
        self.assertEqual(len(audit),3)
        self.assertTrue(pd.isna(audit.loc[1,'signed_difference_c']))
        self.assertEqual(metrics['unrecorded_expected_slots'],3)

    def test_duplicate_measured_keys(self):
        m,p=tiny_sources();m.loc[1,'sample_number']=1
        with self.assertRaisesRegex(ValueError,'duplicate'): compare_frames(m,p)

    def test_duplicate_prediction_keys(self):
        m,p=tiny_sources();p.loc[1,'sample_number']=1
        with self.assertRaisesRegex(ValueError,'duplicate'): compare_frames(m,p)

    def test_timestamp_mismatch(self):
        m,p=tiny_sources();p.loc[1,'timestamp']='2026-10-08T18:00:04+00:00'
        with self.assertRaisesRegex(ValueError,'Timestamp mismatch'): compare_frames(m,p)

    def test_naive_timestamp(self):
        m,p=tiny_sources();m.loc[0,'timestamp']='2026-10-08T18:00:00'
        with self.assertRaisesRegex(ValueError,'timezone-aware'): compare_frames(m,p)

    def test_nonfinite_prediction(self):
        m,p=tiny_sources();p.loc[0,'predicted_temperature_c']=np.inf
        audit,valid,_=compare_frames(m,p)
        self.assertEqual(valid.sample_number.tolist(),[3])
        self.assertEqual(audit.loc[0,'comparison_reason'],'Nonfinite prediction')

    def test_gap_plot_preserves_observations(self):
        m,p=tiny_sources();audit,_,_=compare_frames(m,p)
        x,y=gap_plot_arrays(audit,'measured_value',2)
        self.assertEqual(len(x),4)
        self.assertTrue(np.isnan(y[1]) and np.isnan(y[2]))
        self.assertEqual(y[-1],23.0)
        self.assertEqual(len(audit),3)

    def test_unmatched_sample_preserved(self):
        m,p=tiny_sources();p=p.iloc[1:].copy()
        audit,valid,_=compare_frames(m,p)
        self.assertEqual(len(audit),3)
        self.assertEqual(valid.sample_number.tolist(),[3])
        self.assertEqual(audit.loc[0,'comparison_reason'],'No prediction for sample')

    def test_supplied_reference_results(self):
        m=pd.read_csv(ROOT/'data'/MEASURED_FILE);p=pd.read_csv(ROOT/'data'/PREDICTED_FILE)
        audit,valid,metrics=compare_frames(m,p)
        self.assertEqual((len(audit),len(valid)),(1800,1747))
        self.assertEqual(metrics['status_counts'],{'OK':1747,'MISSING':33,'REJECTED':14,'SUSPICIOUS':6})
        self.assertAlmostEqual(metrics['mean_signed_difference_c'],1.7348654836863193,places=12)
        self.assertAlmostEqual(metrics['maximum_absolute_difference_c'],2.603,places=12)
        self.assertEqual((metrics['clock_gap_count'],metrics['unrecorded_expected_slots']),(4,177))
        self.assertTrue(valid.signed_difference_c.gt(0).all())


if __name__ == '__main__': unittest.main()
