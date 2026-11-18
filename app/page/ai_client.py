import anthropic

from app.config import settings

# Anthropic() 会自动读取环境变量（.env 由 app.config 统一加载）：
#   ANTHROPIC_BASE_URL   接口地址
#   ANTHROPIC_AUTH_TOKEN 或 ANTHROPIC_API_KEY  鉴权密钥
# load_dotenv() 不会覆盖已存在的环境变量，因此终端里已有的配置优先级更高
client = anthropic.Anthropic()

MODEL = settings.anthropic_model
SYSTEM_PROMPT = "你是资深软件工程师,请用中文回答我的问题"
MAX_TOKENS = 4096


def chat():
  print("AI已启动,输入 exit() 退出")
  while True:
    try:
      user_input = input("你: ")
    except (EOFError, KeyboardInterrupt):
      print("\nAI已退出")
      break

    if user_input.strip().lower() == "exit()":
      print("AI已退出")
      break

    print("AI: ", end="", flush=True)
    try:
      with client.messages.stream(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_input}],
      ) as stream:
        for text in stream.text_stream:
          print(text, end="", flush=True)
      print()
    except anthropic.AuthenticationError:
      print("\n[错误] 鉴权失败：请检查 .env 中的 ANTHROPIC_AUTH_TOKEN 是否正确。")
    except anthropic.NotFoundError:
      print(f"\n[错误] 模型或接口不存在：请检查 ANTHROPIC_BASE_URL 与 ANTHROPIC_MODEL（当前为 {MODEL}）。")
    except anthropic.RateLimitError:
      print("\n[错误] 请求过于频繁，请稍后重试。")
    except anthropic.APIConnectionError:
      print("\n[错误] 网络连接失败：请检查 ANTHROPIC_BASE_URL 是否可访问。")
    except anthropic.APIStatusError as e:
      print(f"\n[错误] 接口返回异常（HTTP {e.status_code}）：{e.message}")


if __name__ == "__main__":
  chat()
