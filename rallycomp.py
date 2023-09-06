import gpsd
import math
import time

class FourDPosition:
    def __init__(self, position, alt, timestamp):
        self.lat = position[0]
        self.lon = position[1]
        self.alt = alt
        self.timestamp = timestamp

    def distance_between_two_gps_points(self, lat1, lon1, lat2, lon2):
        R = 6371 # Radius of the earth in km
        dLat = deg2rad(lat2-lat1) # deg2rad below
        dLon = deg2rad(lon2-lon1)
        a = math.sin(dLat/2) * math.sin(dLat/2) + \
            math.cos(deg2rad(lat1)) * math.cos(deg2rad(lat2)) * \
            math.sin(dLon/2) * math.sin(dLon/2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        d = R * c # Distance in km
        return d * 1000 # Distance in m

    def subtract(self, other):
        horiz = self.distance_between_two_gps_points(self.lat, self.lon, other.lat, other.lon)
        vert = other.alt - self.alt
        magnitude = math.sqrt(horiz**2 + vert**2)
        time_diff = self.timestamp - other.timestamp
        return Displacement(magnitude, time_diff)

class Displacement:
    def __init__(self, distance, time):
        self.distance = distance
        self.time = time 

def deg2rad(deg):
    return deg * (math.pi/180)


def block_until_new_fix(last_position):
    packet = gpsd.get_current()
    while packet.get_time() == last_position.timestamp:
        time.sleep(.1)
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

    odometer = 0
    last_position = FourDPosition(packet.position(), packet.altitude(), packet.get_time())
    while True:
        packet = block_until_new_fix(last_position)
        current_position = FourDPosition(packet.position(), packet.altitude(), packet.get_time())
        displacement = current_position.subtract(last_position)
        odometer += displacement.distance
        print(f"Odometer: {odometer}m")
        last_position = current_position


if __name__ == "__main__":
    main_loop()