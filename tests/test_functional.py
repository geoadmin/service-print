import os
import unittest
import json
import multiprocessing
import mock


from print3.utils import _normalize_projection, _normalize_imageDisplay, _qrcodeurlparse, _qrcodeurlunparse, _increment_info, _zeitreihen, _get_releases_info



url_tuple =("https://mf-chsdi3.dev.bgdi.ch/qrcodegenerator",
            "https://mf-geoadmin3.dev.bgdi.ch/",
            {'lang': 'fr', 'layers_visibility': 'true,false,false,false', 'bgLayer': 'voidLayer', 'E': '2499845.99', 'layers': 'ch.swisstopo.zeitreihen,ch.bfs.gebaeude_wohnungs_register,ch.bav.haltestellen-oev,ch.swisstopo.swisstlm3d-wanderwege', 'zoom': '5', 'N': '1117341.56', 'topic': 'ech', 'layers_timestamp': '18641231,,,'})
            
qrcodeurl =  "https://mf-chsdi3.dev.bgdi.ch/qrcodegenerator?url=https%3A%2F%2Fmf-geoadmin3.dev.bgdi.ch%2F%3Flang%3Dfr%26topic%3Dech%26bgLayer%3DvoidLayer%26layers%3Dch.swisstopo.zeitreihen%2Cch.bfs.gebaeude_wohnungs_register%2Cch.bav.haltestellen-oev%2Cch.swisstopo.swisstlm3d-wanderwege%26layers_visibility%3Dtrue%2Cfalse%2Cfalse%2Cfalse%26layers_timestamp%3D18641231%2C%2C%2C%26E%3D2499845.99%26N%3D1117341.56%26zoom%3D5"

lockfile = "tests/data/lock.json"


class TestServicePrintFunctional(unittest.TestCase):
    
    def setUp(self):
         data = {"done": 0}
         with open(lockfile, "w") as f:
             f.write(json.dumps(data))
         self.patch = None
         

    def tearDown(self):
         if os.path.exists(lockfile):
             os.remove(lockfile)
         if self.patch:
            self.patch.stop()

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
        
        
    def test_normalize_imageDisplay(self):
        display = [1000,500]
        
        normalize_display_str = _normalize_imageDisplay(display)
        
        self.assertEqual(normalize_display_str, '3555,1777,256.0')
        
    def test_qrcodeurlparse(self):
        
        (qrcode_service_url, map_url, params) = _qrcodeurlparse(qrcodeurl)
         
        self.assertEqual(qrcode_service_url, url_tuple[0])
        self.assertEqual(map_url, url_tuple[1])
        self.assertEqual(params, url_tuple[2] )
        
    def test_qrcodeurlunparse(self):
        
        
        (qrcode_service_url, map_url, params) = url_tuple
        
        
        result_url = _qrcodeurlunparse(url_tuple)
        
        self.assertEqual(result_url, 'https://mf-chsdi3.dev.bgdi.ch/qrcodegenerator?url=https%3A%2F%2Fmf-geoadmin3.dev.bgdi.ch%2F%3Furl%3Dlang%3Dfr%26layers_visibility%3Dtrue%2Cfalse%2Cfalse%2Cfalse%26bgLayer%3DvoidLayer%26E%3D2499845.99%26layers%3Dch.swisstopo.zeitreihen%2Cch.bfs.gebaeude_wohnungs_register%2Cch.bav.haltestellen-oev%2Cch.swisstopo.swisstlm3d-wanderwege%26zoom%3D5%26N%3D1117341.56%26topic%3Dech%26layers_timestamp%3D18641231%2C%2C%2C')
      
        
    def test_increment_info(self):
        
        lock = multiprocessing.Manager().Lock()
              
        _increment_info(lock, lockfile)
        
        with open(lockfile,'r') as l:
            data = json.loads(l.read())
            
        self.assertEqual(data['done'], 1)

        
    def test_zeitreihen_release(self):
        timestamps_expected = ['2005','2010']
        import print3
        print3.utils._get_releases_info = mock.Mock(return_value=timestamps_expected)
  
        
        timestamps = _zeitreihen({}, 'http://foo')

        self.assertEqual(timestamps_expected, timestamps)
        
        
        
        
        
        