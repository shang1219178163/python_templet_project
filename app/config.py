"""项目配置：集中从环境变量与项目根目录的 `.env` 读取。

优先级：进程已有的环境变量 > `.env` > 这里的默认值。
其他模块统一 ``from app.config import settings``，不要再各自调用 ``load_dotenv()``。
"""

from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"

# 先把 .env 注入环境变量：第三方 SDK（如 anthropic）直接读 os.environ 也能拿到；
# load_dotenv 不覆盖已有变量，所以终端里手动 export 的值依然优先。
load_dotenv(ENV_FILE)


class Settings(BaseSettings):
    """运行期配置，字段名与环境变量名大小写不敏感地一一对应。"""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    anthropic_base_url: str = ""
    anthropic_auth_token: str = ""
    anthropic_model: str = "deepseek-chat"
    anthropic_vision_model: str = ""
    api_key: str = ""

    @property
    def vision_model(self) -> str:
        """带图片的请求用视觉模型，未单独配置时退回默认模型"""
        return self.anthropic_vision_model or self.anthropic_model


settings = Settings()
