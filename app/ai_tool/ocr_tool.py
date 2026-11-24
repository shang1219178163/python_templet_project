"""图片 OCR 工具：优先用 ocrmac（Apple Vision），失败时回退 natocr。"""

import json
from pathlib import Path
from typing import Any, ClassVar

from app.ai_tool.tool_registry import BaseTool, ToolError


class OcrTool(BaseTool):
    """识别本地图片中的文字，并向对话模型提供函数定义。"""

    name = "ocr_image"
    description = (
        "识别本地图片中的文字，支持中英文混排。"
        "用户给出图片路径、要求提取或识别图片文字时调用，不要凭想象编造图片内容。"
    )
    parameters: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "image_path": {
                "type": "string",
                "description": "本地图片文件路径，例如 /Users/shang/test.png 或 ./data/screenshot.jpg",
            },
        },
        "required": ["image_path"],
    }

    def run(self, **kwargs: Any) -> str:
        image_path = kwargs.get("image_path")
        if not isinstance(image_path, str) or not image_path.strip():
            return "缺少图片路径"
        return self.recognize(image_path.strip())

    def recognize(self, image_path: str) -> str:
        """识别图片文字；两个引擎都不可用时抛 ToolError"""
        path = Path(image_path).expanduser()
        if not path.is_file():
            return f"找不到图片文件: {image_path}"

        errors: list[str] = []
        recognized = False
        for engine, func in (
            ("ocrmac", self._recognize_ocrmac),
            ("natocr", self._recognize_natocr),
        ):
            try:
                lines = func(path)
            except ImportError as err:
                errors.append(f"{engine} 未安装: {err}")
                continue
            except Exception as err:  # 第三方库异常类型不统一，交给下一个引擎兜底
                errors.append(f"{engine} 识别失败: {err}")
                continue

            recognized = True
            clean = [line.strip() for line in lines if line.strip()]
            if clean:
                return json.dumps(
                    {
                        "engine": engine,
                        "image": str(path),
                        "text": "\n".join(clean),
                        "lines": clean,
                    },
                    ensure_ascii=False,
                )

        if recognized:
            return "图片中没有识别到文字"
        raise ToolError("OCR 识别失败: " + "；".join(errors))

    @staticmethod
    def _recognize_ocrmac(path: Path) -> list[str]:
        from ocrmac import ocrmac

        annotations = ocrmac.OCR(
            str(path),
            language_preference=["zh-Hans", "en-US"],
            recognition_level="accurate",
        ).recognize()
        return [text for text, _confidence, _bbox in annotations if isinstance(text, str)]

    @staticmethod
    def _recognize_natocr(path: Path) -> list[str]:
        from natocr import OCR

        pages = OCR(language="auto").recognize(str(path))
        return [line for page in pages for line in page.lines]
