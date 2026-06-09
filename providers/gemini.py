from google import genai

from config import settings
from providers.base import BaseLLMProvider


class GeminiLLMProvider(BaseLLMProvider):

    def __init__(self) -> None:
        self._client = genai.Client(api_key=settings.llm_api_key)

    def generate(self, prompt: str) -> str:
        response = self._client.models.generate_content(
            model=settings.llm_model,
            contents=prompt,
        )
        return response.text
