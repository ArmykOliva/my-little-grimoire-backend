import string
import random
from geopy.distance import geodesic
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def is_within_distance(lat1, lon1, lat2, lon2, max_distance=500):
    point1 = (lat1, lon1)
    point2 = (lat2, lon2)
    return geodesic(point1, point2).meters <= max_distance

def generate_code(length=5):
    return ''.join(random.choices(string.ascii_uppercase, k=length))

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)