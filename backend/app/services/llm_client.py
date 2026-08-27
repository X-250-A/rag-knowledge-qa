import httpx
from openai import AsyncOpenAI

from backend.app.config import settings


class LlmClient:
    def __init__(self):
        http_client = httpx.AsyncClient(
            proxy=None,
            trust_env=False,
            timeout=httpx.Timeout(
                connect=settings.LLM_CONNECTION_TIMEOUT,
                read=settings.LLM_READ_TIMEOUT,
                write=10.0,
                pool=5
            )
        )
        self.client = AsyncOpenAI(
            http_client=http_client,
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.BASE_URL,
        )
        self.model = settings.DEEPSEEK_MODEL


    # 非流式输出回答
    async def chat(self, messages: list[dict]):
        kwargs = {
            "model" : self.model,
            "timeout" : settings.LLM_REQUEST_TIMEOUT,
            "messages" : messages,
        }
        response = await self.client.chat.completions.create(**kwargs, stream=False)
        return response.choices[0].message.content

    # 流式输出
    async def stream_chat(self, messages: list[dict]):
        kwargs = {
            "model" : self.model,
            "timeout" : settings.LLM_REQUEST_TIMEOUT,
            "messages" : messages,
            "stream" : True
        }
        stream = await self.client.chat.completions.create(**kwargs)

        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta


