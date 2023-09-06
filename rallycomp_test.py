import unittest
from rallycomp import FourDPosition
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