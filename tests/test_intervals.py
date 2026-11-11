import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import numpy as np
from pipeline import cumulative,recent,composition,validate_base,load,ROOT
class IntervalTests(unittest.TestCase):
 def test_partial_rolling_history(self):
  self.assertAlmostEqual(float(recent(130,[0,100],[40,160],60)),30)
 def test_prior_day_history_not_reset(self):
  self.assertAlmostEqual(float(recent(86410,[86300],[86350],1800)),50)
 def test_no_future_usage(self):
  self.assertEqual(float(recent(20,[100],[140],60)),0)
 def test_exact_tie_alphabetical(self):
  x=composition(0,60,np.array([0,30]),np.array([30,60]),np.array(['VIDEO','MESSAGING']))
  self.assertEqual(x['dominant_activity_category'],'MESSAGING');self.assertEqual(x['minority_category_sec'],30)
 def test_uncovered_time_not_filled(self):
  x=composition(0,60,np.array([10]),np.array([40]),np.array(['VIDEO']))
  self.assertEqual(x['unlabelled_sec'],30);self.assertEqual(x['dominant_fraction'],.5)
 def test_empty_window(self):
  x=composition(0,60,np.array([]),np.array([]),np.array([]));self.assertEqual(x['dominant_activity_category'],'UNLABELLED')
 def test_release_source_integrity(self):validate_base(load(ROOT))
if __name__=='__main__':unittest.main()
