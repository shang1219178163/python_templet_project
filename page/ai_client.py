from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()

def chat():
  print("AI已启动,输入 exit() 退出")
  while True:
    user_input = input("你: ")
    if user_input.lower() == "exit()":
      print("AI已退出")
      break

    response = client.chat.completions.create(
      model="gpt-4.1-mini",
      messages=[
        {"role": "system", "content": "你是资深软件工程师,请用中文回答我的问题"},
        {"role": "user", "content": user_input}
      ]
    )
    print("AI: ", response.choices[0].message.content)

if __name__ == "__main__":
  chat()