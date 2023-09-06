import unittest
from rallycomp import FourDPosition, Odometer
from datetime import datetime

class TestFourDPosition(unittest.TestCase):

    def test_FourDPosition_distance_to_vertical(self):
        position1 = FourDPosition((47.69431, -122.345998333), 150, datetime(2020, 1, 1, 0, 0, 0, 0))
        position2 = FourDPosition((47.69431, -122.345998333), 155, datetime(2020, 1, 1, 0, 0, 2, 0))
        dist = position2.subtract(position1)
        self.assertEqual(dist.distance, 5)
        self.assertEqual(dist.time.seconds, 2)

    def test_FourDPosition_distance_to_horizontal(self):
        position1 = FourDPosition((47.69431, -122.345998333), 150, datetime(2020, 1, 1, 0, 0, 0, 0))
        position2 = FourDPosition((47.69432, -122.345998333), 150, datetime(2020, 1, 1, 0, 0, 2, 0))
        dist = position2.subtract(position1)
        self.assertEqual(dist.distance, 1.111949266008448)
        self.assertEqual(dist.time.seconds, 2)

        position1 = FourDPosition((47.69431, -122.345998333), 150, datetime(2020, 1, 1, 0, 0, 0, 0))
        position2 = FourDPosition((47.69430, -122.345998333), 150, datetime(2020, 1, 1, 0, 0, 2, 0))
        dist = position2.subtract(position1)
        self.assertEqual(dist.distance, 1.1119492667985353)  # shouldn't be much different
        self.assertEqual(dist.time.seconds, 2)

    def test_FourDPosition_distance_to_diagonal(self):
        position1 = FourDPosition((47.69431, -122.345998333), 150, datetime(2020, 1, 1, 0, 0, 0, 0))
        position2 = FourDPosition((47.69432, -122.345999333), 151, datetime(2020, 1, 1, 0, 0, 2, 0))
        dist = position2.subtract(position1)
        self.assertEqual(dist.distance, 1.49734189653602)
        self.assertEqual(dist.time.seconds, 2)

    def test_FourDPosition_distance_nautical_mile(self):
        position1 = FourDPosition((47.0, -122.0), 150, datetime(2020, 1, 1, 0, 0, 0, 0))
        position2 = FourDPosition((47.0 + (1/60), -122.0), 151, datetime(2020, 1, 1, 0, 0, 2, 0))
        dist = position2.subtract(position1)
        self.assertEqual(dist.distance, 1853.2490472056688)  # 1 nautical mile to km



class TestOdometer(unittest.TestCase):
    def test_odometer(self):
        position1 = FourDPosition((47.0, -122.0), 150, datetime(2020, 1, 1, 0, 0, 0, 0))
        position2 = FourDPosition((47.0 + (1/60), -122.0), 151, datetime(2020, 1, 1, 1, 0, 0, 0))
        odo = Odometer(position1)
        odo.addPosition(position2)
        self.assertEqual(odo.distanceAccumulator, 1853.2490472056688)
        self.assertEqual(odo.get_average_speed(), 1.8532490472056689) # 1 mph ish
        

    def test_odometer_more(self):
        position1 = FourDPosition((47.0, -122.0), 150, datetime(2020, 1, 1, 0, 0, 0, 0))
        position2 = FourDPosition((47.0 + (1/60), -122.0), 151, datetime(2020, 1, 1, 1, 0, 0, 0))
        position3 = FourDPosition((47.0 + (2/60), -122.0), 151, datetime(2020, 1, 1, 2, 0, 0, 0))
        odo = Odometer(position1)
        odo.addPosition(position2)
        odo.addPosition(position3)
        self.assertEqual(odo.distanceAccumulator, 3706.4978246148758)
        self.assertEqual(odo.get_average_speed(), 1.8532489123074378) # 1 mph ish
