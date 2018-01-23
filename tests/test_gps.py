# need 
#export PYTHONPATH=/path/to/lib:/path/to/tests

#python3 -m unittest  test_gps

import unittest

from gpsPos import gpsConnection
from gpsPos import gpsPos

class TestgpsPosMethods(unittest.TestCase):

    #def setUp(self):
    #    self.pt = gpsPos(45.395676, -75.676829)

    #def setUp(self):
    #    self.widget = Widget('The widget')
    #
    #def tearDown(self):
    #    self.widget.dispose()

    def test_gpsPos(self):
       pt = gpsPos(45.395676, -75.676829)
       self.assertEqual((45.395676, -75.676829), (pt.lat, pt.lon))

       with self.assertRaises(ValueError): gpsPos(100.395676, -75.676829)

       with self.assertRaises(ValueError): gpsPos(45.395676, -275.676829)


    def test_move_nm(self):
       pt = gpsPos(45.395676, -75.676829)
       pt2 = gpsPos.move(pt, 240, 1.0)

       self.assertAlmostEqual(1.0,  gpsPos.nm(pt, pt2))

       fuzz = 1e-12
       self.assertTrue(abs(1.0 - gpsPos.nm(pt, pt2)) < fuzz)

    # need fake? gps for this
    #  con = gpsConnection()
    #  p = con.getGPS()
    #  p.lon
    #  p.lat


    def test_heading(self):
       pt = gpsPos(44.20978198674271, -76.51016279425306)
       
       # test to 7 places
       self.assertAlmostEqual( 240, 
           gpsPos.heading(pt, gpsPos(44.20144865340938, -76.53029941039073)) )

       pt2 = gpsPos.move(pt, 225, 1.0)
       self.assertAlmostEqual( 225,   gpsPos.heading(pt, pt2) )

       pt2 = gpsPos.move(pt, 315, 0.5)
       self.assertAlmostEqual( 315,   gpsPos.heading(pt, pt2) )

       pt2 = gpsPos.move(pt, 45, 1.0)
       self.assertAlmostEqual( 45,    gpsPos.heading(pt, pt2) )

       pt2 = gpsPos.move(pt, 135, 1.0)
       self.assertAlmostEqual( 135,   gpsPos.heading(pt, pt2) )

       self.assertAlmostEqual( 90, 
           gpsPos.heading(gpsPos(0, -76.51003278266177), 
                          gpsPos(0, -76.49359110683335))  )

       self.assertAlmostEqual( 180, 
           gpsPos.heading(gpsPos(44.21048983959772,  0), 
                          gpsPos(44.198704726577944, 0))  )

if __name__ == '__main__':
    unittest.main()
