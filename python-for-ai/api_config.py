import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


class APIConfig:
    base_url = "https://api.openai.com/v1"
    retries_on_failure = 3
    retry_delay = timedelta(seconds=10)

    def __init__(
        self,
        api_key,
        model="gpt-3.5-turbo",
        max_tokens=100,
        timeout=timedelta(seconds=30),
    ):
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.timeout = timeout


# ---------------------------------------------------------------------
# Configurations
# ---------------------------------------------------------------------

dev_config = APIConfig(api_key=os.environ.get("OPENAI_DEV_API_KEY"), max_tokens=50)

prod_config = APIConfig(
    api_key=os.environ.get("OPENAI_PROD_API_KEY"), model="gpt-4", max_tokens=1000
)
