import os

class LLMConfig:
    def __init__(self, api_key: str = None, api_endpoint: str = None, model_name: str = "gpt-4"):
        self.API_KEY = api_key if api_key is not None else os.getenv("LLM_API_KEY", "YOUR_LLM_API_KEY")
        self.API_ENDPOINT = api_endpoint if api_endpoint is not None else os.getenv("LLM_API_ENDPOINT", "https://api.apiyi.com/v1")
        self.MODEL_NAME = model_name
