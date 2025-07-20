import os
from dotenv import load_dotenv

load_dotenv()

print("ARIZE_SPACE_ID:", os.getenv("ARIZE_SPACE_ID"))
print("ARIZE_API_KEY:", os.getenv("ARIZE_API_KEY"))
print("PAGERDUTY_ROUTING_KEY:", os.getenv("PAGERDUTY_ROUTING_KEY"))