import string
import random
from geopy.distance import geodesic

def is_within_distance(lat1, lon1, lat2, lon2, max_distance=500):
    point1 = (float(lat1), float(lon1))
    point2 = (float(lat2), float(lon2))
    return geodesic(point1, point2).meters <= max_distance

def generate_code(length=5):
    return ''.join(random.choices(string.ascii_uppercase, k=length))