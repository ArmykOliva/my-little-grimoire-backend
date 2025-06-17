import string
import random
from geopy.distance import geodesic

def is_within_distance(lat1, lon1, lat2, lon2, max_distance=500):
    point1 = (lat1, lon1)
    point2 = (lat2, lon2)
    return geodesic(point1, point2).meters <= max_distance

def generate_code(length=5):
    return ''.join(random.choices(string.ascii_uppercase, k=length))