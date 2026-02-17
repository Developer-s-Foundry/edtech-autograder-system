import os
import redis
from dotenv import load_dotenv

load_dotenv()  # loads .env in the current folder

url = os.getenv("REDIS_URL")
print("REDIS_URL loaded?", url is not None)

r = redis.from_url(url, decode_responses=True)
print("Ping:", r.ping())
