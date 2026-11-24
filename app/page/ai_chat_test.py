from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

from app.config import settings


class AIChatTest:
    messages: list[ChatCompletionMessageParam] = [
        {"role": "system", "content": "You are a helpful assistant"},
    ]

    def __init__(self):
        self.clent = OpenAI(
            api_key=settings.api_key,
            base_url="https://api.deepseek.com",
        )

    def run(self):
        while True:
            question = input(">> 问题: ")
            self.messages.append({"role": "user", "content": question})

            response = self.clent.chat.completions.create(
                model="deepseek-flash",
                messages=self.messages,
                stream=False,
                reasoning_effort="high",
                extra_body={"thinking": {"type": "enabled"}},
            )

            message = response.choices[0].message
            self.messages.append({"role": message.role, "content": message.content})
            print(f"回答:{message.content}")


if __name__ == "__main__":
    AIChatTest().run()
