from groq import Groq

from config import settings
from providers.base import BaseLLMProvider


class GroqLLMProvider(BaseLLMProvider):

    def __init__(self) -> None:
        self._client = Groq(api_key=settings.llm_api_key)

    def generate(self, prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=settings.llm_model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
