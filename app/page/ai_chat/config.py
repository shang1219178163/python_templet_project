"""AI 对话页面的可调配置。

默认值写在这里，临时改可在项目根 `.env` 里用 `AI_CHAT_` 前缀覆盖，例如：

    AI_CHAT_MODEL=deepseek-chat
    AI_CHAT_MAX_TOOL_ROUNDS=8
    AI_CHAT_PRINT_THINKING=false

API Key 仍由 `app.config.settings.api_key` 提供，不在这里重复定义。
"""

from openai.types.shared import ReasoningEffort
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.config import ENV_FILE


class AIChatConfig(BaseSettings):
    """模型、接口地址与对话循环参数"""

    model_config = SettingsConfigDict(
        env_prefix="AI_CHAT_",
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-flash"
    reasoning_effort: ReasoningEffort = "high"
    max_tool_rounds: int = 5
    print_thinking: bool = True


ai_chat_config = AIChatConfig()
