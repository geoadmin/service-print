import unittest

from print3.utils import _normalize_projection



class TestServicePrintFunctional(unittest.TestCase):

    def test_normalize_projection(self):
        lv03_pnt = [600000.0, 200000.0]
        lv95_pnt = [2600000.0, 1200000.0]
        from_lv95 = _normalize_projection(lv95_pnt, use_lv95=True)
        from_lv03 = _normalize_projection(lv03_pnt, use_lv95=True)
    
        self.assertEqual(lv95_pnt, from_lv95)
        self.assertEqual(lv95_pnt, from_lv03)
        
        lv03_box = [600000.0, 200000.0, 700000.0, 300000.0]
        lv95_box = [2600000.0, 1200000.0, 2700000.0, 1300000.0]
        
        box_from_lv95 = _normalize_projection(lv95_box, use_lv95=True)
        box_from_lv03 = _normalize_projection(lv03_box, use_lv95=True)
        
        self.assertEqual(lv95_box, box_from_lv95)
        self.assertEqual(lv95_box, box_from_lv03)
