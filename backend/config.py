import os
from dotenv import load_dotenv

load_dotenv()

BDL_API_KEY = os.environ["BDL_API_KEY"]
PROPODDS_API_KEY = os.environ["PROPODDS_API_KEY"]
ODDS_API_KEY = os.environ["ODDS_API_KEY"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
DATABASE_URL = os.getenv("DATABASE_URL", "edgeiq.db")
