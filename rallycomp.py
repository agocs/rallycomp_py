import gpsd
import math
import time
from datetime import datetime, timedelta
from typing import Optional, Tuple


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


class Instruction:
    def __init__(
        self,
        time: Optional[datetime] = None,
        speed_kmh: Optional[float] = None,
        distance_km: Optional[float] = None,
    ):
        if distance_km is not None:
            self.absolute_distance = distance_km * 1000
        else:
            self.absolute_distance = None
        self.absolute_time = time
        self.speed = speed_kmh

    def activate(self, odometer: Odometer):
        self.odometer = odometer
        if self.absolute_distance is not None and self.speed is not None:
            self.activate_distance_speed()
        elif self.absolute_time is not None and self.speed is not None:
            self.activate_time_speed()
        elif self.absolute_time is not None and self.absolute_distance is not None:
            self.activate_time_distance()
        else:
            raise ValueError("Not enough information to activate instruction")

    def activate_time_speed(self):
        time_remaining = self.absolute_time - self.odometer.lastFix.timestamp
        self.absolute_distance = (
            self.odometer.distanceAccumulator
            + self.speed * time_remaining.total_seconds() / 60 / 60 * 1000
        )

    def activate_time_distance(self):
        time_remaining = self.absolute_time - self.odometer.lastFix.timestamp
        self.speed = (
            (self.absolute_distance - self.odometer.distanceAccumulator) / 1000
        ) / (time_remaining.total_seconds() / 60 / 60)

    def activate_distance_speed(self):
        distance_remaining = self.absolute_distance - self.odometer.distanceAccumulator
        time_to_add = timedelta(
            seconds=(distance_remaining / 1000) / self.speed * 60 * 60
        )
        self.absolute_time = self.odometer.lastFix.timestamp + time_to_add

    def get_time_remaining(self) -> timedelta:
        """Returns time remaining in timedelta"""
        return self.absolute_time - self.odometer.lastFix.timestamp

    def get_distance_remaining(self) -> float:
        """Returns distance remaining in meters"""
        return self.absolute_distance - self.odometer.distanceAccumulator

    def get_speed(self):
        """Returns speed in km/h"""
        return self.speed


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
        self.cast = CAST(0, self.odo)
        self.current_instruction = Instruction()

    def update(self):
        packet = self.block_until_new_fix()
        speed_mps = packet.hspeed
        speed_kph = speed_mps * 3.6
        self.odo.addPosition(
            FourDPosition(
                (packet.lat, packet.lon), packet.alt, packet.get_time(), speed_kph
            )
        )

    def block_until_new_fix(self):
        packet = gpsd.get_current()
        while packet.get_time() == self.odo.lastFix.timestamp:
            time.sleep(0.05)
            packet = gpsd.get_current()
        return packet

    def start_instruction(self, instruction: Instruction):
        self.current_instruction = instruction
        instruction.activate(self.odo)
        self.cast = CAST(instruction.get_speed(), self.odo)


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
