from openai import OpenAI
import os
from pathlib import Path
from dotenv import load_dotenv

# โหลด .env
current_directory = os.getcwd()
env_path = Path(current_directory).parent / 'venv' / '.env'
load_dotenv(dotenv_path=env_path, override=True)

TYPHOON_API_KEY = os.getenv("TYPHOON_API_KEY")
TYPHOON_API_URL = os.getenv("TYPHOON_API_URL")

class TyphoonClient:
    def __init__(self, api_key: str, api_url: str, model: str = "typhoon-v2.1-12b-instruct", temperature: float = 0, max_tokens: int = 2000):
        # Initialize the client with the given API key and URL
        self.client = OpenAI(
            api_key=api_key,
            base_url=api_url
        )
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def get_response(self, prompt: str, **kwargs):
        # Allow overriding default params like model, temperature, max_tokens
        model = kwargs.get("model", self.model)
        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = kwargs.get("max_new_tokens", self.max_tokens)

        # Make the API request
        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )

        # Return the generated message content
        return response.choices[0].message.content

