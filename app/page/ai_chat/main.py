"""命令行入口：python -m app.page.ai_chat.main"""

from app.page.ai_chat.chat import AIChat


def main() -> None:
    chat = AIChat()
    try:
        while True:
            question = input(">> 问题: ").strip()
            if not question:
                continue
            chat.ask(question)
    except (EOFError, KeyboardInterrupt):
        print()
    finally:
        chat.close()


if __name__ == "__main__":
    main()
