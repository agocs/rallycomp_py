import gpsd
import math
import time
from datetime import datetime
from typing import Tuple


class FourDPosition:
    def __init__(
        self,
        position: Tuple[float, float],
        alt: float,
        timestamp: datetime,
        speed: float = 0,
    ):
        self.lat = position[0]
        self.lon = position[1]
        self.alt = alt
        self.timestamp = timestamp
        self.speed = speed

    def distance_between_two_gps_points(self, lat1, lon1, lat2, lon2):
        R = 6371  # Radius of the earth in km
        dLat = self.deg2rad(lat2 - lat1)  # deg2rad below
        dLon = self.deg2rad(lon2 - lon1)
        a = math.sin(dLat / 2) * math.sin(dLat / 2) + math.cos(
            self.deg2rad(lat1)
        ) * math.cos(self.deg2rad(lat2)) * math.sin(dLon / 2) * math.sin(dLon / 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        d = R * c  # Distance in km
        return d * 1000  # Distance in m

    def deg2rad(self, deg):
        return deg * (math.pi / 180)

    def subtract(self, other):
        horiz = self.distance_between_two_gps_points(
            self.lat, self.lon, other.lat, other.lon
        )
        vert = other.alt - self.alt
        magnitude = math.sqrt(horiz**2 + vert**2)
        time_diff = self.timestamp - other.timestamp
        return Displacement(magnitude, time_diff)


class Displacement:
    def __init__(self, distance, time):
        self.distance = distance
        self.time = time


class Odometer:
    def __init__(self, origFix: FourDPosition, calibration: float = 1):
        self.origFix = origFix
        self.distanceAccumulator = 0
        self.lastFix = origFix

    def addPosition(self, newFix: FourDPosition):
        displacement = newFix.subtract(self.lastFix)
        self.distanceAccumulator = self.distanceAccumulator + displacement.distance
        self.lastFix = newFix

    def get_average_speed(self):
        elapsed = self.lastFix.timestamp - self.origFix.timestamp
        hours = elapsed.total_seconds() / 60 / 60
        return self.distanceAccumulator / 1000 / hours  # kilometers per hour

    def get_elapsed_time(self):
        return self.lastFix.timestamp - self.origFix.timestamp


class CAST:
    def __init__(self, average: float, odo: Odometer):
        self.average = average
        self.odo = odo

    def get_offset(self):
        ideal = (
            self.odo.get_elapsed_time().total_seconds() / 60 / 60
        ) * self.average  #  kilometers
        actual = self.odo.distanceAccumulator / 1000  # kilometers
        differential = actual - ideal
        return differential / self.average * 60 * 60  # seconds


class RallyComputer:
    def __init__(self):
        gpsd.connect()
        packet = gpsd.get_current()
        while packet.mode < 2:
            time.sleep(1)
            packet = gpsd.get_current()
        self.odo = Odometer(
            FourDPosition((packet.lat, packet.lon), packet.alt, packet.get_time())
        )
        self.cast = CAST(20, self.odo)

    def update(self):
        packet = self.block_until_new_fix()
        self.odo.addPosition(
            FourDPosition(
                (packet.lat, packet.lon), packet.alt, packet.get_time(), packet.speed()
            )
        )

    def block_until_new_fix(self):
        packet = gpsd.get_current()
        while packet.get_time() == self.odo.lastFix.timestamp:
            time.sleep(0.05)
            packet = gpsd.get_current()
        return packet


def block_until_new_fix(last_position):
    packet = gpsd.get_current()
    while packet.get_time() == last_position.timestamp:
        time.sleep(0.1)
        packet = gpsd.get_current()
    return packet


def main_loop():
    gpsd.connect()
    packet = gpsd.get_current()
    while packet.mode < 2:
        time.sleep(1)
        packet = gpsd.get_current()
        print(f"Waiting for fix... (mode: {packet.mode})")
    print("Fix acquired!")

    odo = Odometer(
        FourDPosition((packet.lat, packet.lon), packet.alt, packet.get_time())
    )
    cast = CAST(20, odo)

    while True:
        block_until_new_fix(odo.lastFix)
        packet = gpsd.get_current()
        odo.addPosition(
            FourDPosition((packet.lat, packet.lon), packet.alt, packet.get_time())
        )
        print(
            f"Distance: {odo.distanceAccumulator / 1000} km \t Average: {odo.get_average_speed()} km/h \t CAST:{cast.average} \t Offset: {cast.get_offset()}"
        )


if __name__ == "__main__":
    main_loop()
