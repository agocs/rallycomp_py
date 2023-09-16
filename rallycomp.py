from enum import Enum
from pathlib import Path
import gpsd
import math
import time
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

import yaml


class Units(Enum):
    MILES = 0
    KILOMETERS = 1


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


class OdometerMode(Enum):
    PARK = 0
    DRIVE = 1
    REVERSE = 2


class Odometer:
    def __init__(self, origFix: FourDPosition, calibration: float = 1):
        self.origFix = origFix
        self.distanceAccumulator = 0
        self.lastFix = origFix
        self.mode = OdometerMode.PARK
        self.calibration = calibration

    def calibrate(self, expected_distance: float):
        self.calibration = (expected_distance * 1000) / self.distanceAccumulator

    def get_accumulated_distance(self):
        return self.distanceAccumulator * self.calibration

    def accumulate_distance(self, distance_meters: float):
        self.distanceAccumulator = self.distanceAccumulator + distance_meters

    def addPosition(self, newFix: FourDPosition):
        displacement = newFix.subtract(self.lastFix)
        if self.mode == OdometerMode.DRIVE:
            self.distanceAccumulator = self.distanceAccumulator + displacement.distance
        elif self.mode == OdometerMode.REVERSE:
            self.distanceAccumulator = self.distanceAccumulator - displacement.distance
        self.lastFix = newFix

    def get_average_speed(self):
        elapsed = self.lastFix.timestamp - self.origFix.timestamp
        hours = elapsed.total_seconds() / 60 / 60
        return self.get_accumulated_distance() / 1000 / hours  # kilometers per hour

    def get_last_speed(self):
        return self.lastFix.speed * self.calibration

    def get_elapsed_time(self):
        return self.lastFix.timestamp - self.origFix.timestamp

    def reset(self):
        self.origFix = self.lastFix
        self.distanceAccumulator = 0


class Instruction:
    def __init__(
        self,
        time: Optional[datetime] = None,
        speed_kmh: Optional[float] = None,
        distance_km: Optional[float] = None,
        dummy: bool = False,
    ):
        if distance_km is not None:
            self.absolute_distance = distance_km * 1000
        else:
            self.absolute_distance = None
        self.absolute_time = time
        self.speed = speed_kmh
        self.dummy = dummy

    def set_distance(self, distance_km: float):
        self.absolute_distance = distance_km * 1000

    def set_time(self, time: datetime):
        self.absolute_time = time

    def set_speed(self, speed_kmh: float):
        self.speed = speed_kmh

    def get_distance(self) -> float:
        if self.absolute_distance is not None:
            return self.absolute_distance / 1000
        else:
            return 0

    def get_time(self) -> datetime:
        if self.absolute_time is not None:
            return self.absolute_time
        else:
            return datetime(1, 1, 1, 0, 0, 0)

    def get_speed(self) -> float:
        if self.speed is not None:
            return self.speed
        else:
            return 0

    def verify(self) -> bool:
        if self.absolute_distance is not None and self.speed is not None:
            return True
        elif self.absolute_time is not None and self.speed is not None:
            return True
        elif self.absolute_time is not None and self.absolute_distance is not None:
            return True
        else:
            return False

    def activate(self, odometer: Odometer):
        self.odometer = odometer
        self.start_distance = odometer.get_accumulated_distance()
        self.start_time = odometer.lastFix.timestamp
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
            self.odometer.get_accumulated_distance()
            + self.speed * time_remaining.total_seconds() / 60 / 60 * 1000
        )

    def activate_time_distance(self):
        time_remaining = self.absolute_time - self.odometer.lastFix.timestamp
        self.speed = (
            (self.absolute_distance - self.odometer.get_accumulated_distance()) / 1000
        ) / (time_remaining.total_seconds() / 60 / 60)

    def activate_distance_speed(self):
        distance_remaining = (
            self.absolute_distance - self.odometer.get_accumulated_distance()
        )
        try:
            time_to_add = timedelta(
                seconds=(distance_remaining / 1000) / self.speed * 60 * 60
            )
        except ZeroDivisionError:
            time_to_add = timedelta(seconds=0)
        self.absolute_time = self.odometer.lastFix.timestamp + time_to_add

    def get_time_remaining(self) -> timedelta:
        """Returns time remaining in timedelta"""
        return self.absolute_time - self.odometer.lastFix.timestamp

    def get_distance_remaining(self) -> float:
        """Returns distance remaining in meters"""
        return self.absolute_distance - self.odometer.get_accumulated_distance()

    def get_elapsed_time(self) -> timedelta:
        """Returns elapsed time in timedelta"""
        return self.odometer.lastFix.timestamp - self.start_time

    def get_accumulated_distance(self) -> float:
        """Returns accumulated distance in meters"""
        return self.odometer.get_accumulated_distance() - self.start_distance


class CAST:
    def __init__(self, instruction: Instruction, odo: Odometer):
        self.instruction = instruction
        self.average = instruction.get_speed()
        self.odo = odo

    def get_offset(self):
        ideal = (
            self.instruction.get_elapsed_time().total_seconds() / 60 / 60
        ) * self.average  #  kilometers
        actual = self.instruction.get_accumulated_distance() / 1000  # kilometers
        differential = actual - ideal
        try:
            return differential / self.average * 60 * 60  # seconds
        except ZeroDivisionError:
            return 0


class RallyComputer:
    def __init__(self):
        self.config = Config("config.yaml")
        gpsd.connect()
        packet = gpsd.get_current()
        while packet.mode < 2:
            time.sleep(1)
            packet = gpsd.get_current()
        packet_time = packet.get_time().replace(tzinfo=timezone.utc)
        self.odo = Odometer(
            FourDPosition((packet.lat, packet.lon), packet.alt, packet_time),
            calibration=self.config.get_odometer_calibration(),
        )
        self.current_instruction = Instruction()
        self.cast = CAST(self.current_instruction, self.odo)

    def update(self):
        packet = self.block_until_new_fix()
        speed_mps = packet.hspeed
        speed_kph = speed_mps * 3.6
        packet_time = packet.get_time().replace(tzinfo=timezone.utc)
        self.odo.addPosition(
            FourDPosition((packet.lat, packet.lon), packet.alt, packet_time, speed_kph)
        )

    def try_update(self):
        packet, new_fix = self.try_new_fix()
        if new_fix:
            speed_mps = packet.hspeed
            speed_kph = speed_mps * 3.6
            packet_time = packet.get_time().replace(tzinfo=timezone.utc)
            self.odo.addPosition(
                FourDPosition(
                    (packet.lat, packet.lon), packet.alt, packet_time, speed_kph
                )
            )

    def try_new_fix(self):
        packet = gpsd.get_current()
        if packet.get_time() != self.odo.lastFix.timestamp:
            return packet, True
        else:
            return packet, False

    def block_until_new_fix(self):
        packet = gpsd.get_current()
        while packet.get_time() == self.odo.lastFix.timestamp:
            time.sleep(0.05)
            packet = gpsd.get_current()
        return packet

    def start_instruction(self, instruction: Instruction):
        self.current_instruction = instruction
        instruction.activate(self.odo)
        self.cast = CAST(instruction, self.odo)
        if self.odo.mode == OdometerMode.PARK:
            self.odo.mode = OdometerMode.DRIVE


class Config:
    def __init__(self, filename: str) -> None:
        self.conf = yaml.safe_load(Path(filename).read_text())

    def get_units(self):
        if not self.conf:
            return Units.KILOMETERS
        elif self.conf["units"] == "miles":
            return Units.MILES
        else:
            return Units.KILOMETERS

    def get_timezone(self):
        if not self.conf:
            return timezone(timedelta(hours=0))
        else:
            hours = self.conf.get("timezone", {}).get("offset_hours", 0)
            return timezone(timedelta(hours=hours))

    def get_odometer_calibration(self):
        if not self.conf:
            return 1
        else:
            return self.conf.get("odometer_calibration", 1)

    def set_calibration(self, calibration):
        if not self.conf:
            self.conf = {}
        self.conf["odometer_calibration"] = calibration
        yaml.safe_dump(self.conf, Path("config.yaml").open("w"))

    def to_display_units(self, input_km: float) -> float:
        if self.get_units() == Units.KILOMETERS:
            return input_km
        else:
            return input_km / 1.60934

    def input_to_units(self, input_value):
        if self.get_units() == Units.KILOMETERS:
            return input_value
        else:
            return input_value * 1.60934

    def get_unit_name(self):
        if self.get_units() == Units.KILOMETERS:
            return "km"
        else:
            return "mi"
