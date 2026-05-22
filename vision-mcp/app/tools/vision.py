"""
视觉工具箱
为无多模态能力的模型提供视觉分析能力，支持本地文件路径和 URL。

工具列表：
- vision_describe   通用图片描述与问答
- vision_ocr        从图片中提取文字
- vision_compare    对比两张图片
- vision_ui_audit   前端 UI 质量分析
"""
import base64
import mimetypes
from pathlib import Path
from typing import Literal

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger
from app.mcp_server.app import mcp_tool

logger = get_logger()

# 支持的图片 MIME 类型（Anthropic 限制）
_SUPPORTED_MEDIA_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
_FALLBACK_MEDIA_TYPE = "image/jpeg"

ImageSource = dict  # Anthropic API image source block


def _detect_media_type(path: str) -> str:
    """通过文件扩展名推断 MIME 类型，不支持时回退到 image/jpeg"""
    mime, _ = mimetypes.guess_type(path)
    return mime if mime in _SUPPORTED_MEDIA_TYPES else _FALLBACK_MEDIA_TYPE


async def _build_image_source(image_input: str) -> ImageSource:
    """
    构建 Anthropic API image source block（统一转为 base64）。
    - http(s):// 开头 → 下载后 base64 编码（规避中转不支持 url 类型）
    - 其他 → 本地文件，读取并 base64 编码
    """
    if image_input.startswith("http://") or image_input.startswith("https://"):
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(image_input)
            response.raise_for_status()
            raw = response.content
            content_type = response.headers.get("content-type", "image/jpeg").split(";")[0].strip()
            media_type = content_type if content_type in _SUPPORTED_MEDIA_TYPES else _FALLBACK_MEDIA_TYPE
        encoded = base64.standard_b64encode(raw).decode("utf-8")
        return {"type": "base64", "media_type": media_type, "data": encoded}

    path = Path(image_input)
    if not path.exists():
        raise FileNotFoundError(f"图片文件不存在: {image_input}")
    if not path.is_file():
        raise ValueError(f"路径不是文件: {image_input}")

    media_type = _detect_media_type(str(path))
    raw = path.read_bytes()
    encoded = base64.standard_b64encode(raw).decode("utf-8")
    return {"type": "base64", "media_type": media_type, "data": encoded}


async def _call_vision(
    content: list[dict],
    max_tokens: int | None = None,
    system: str | None = None,
) -> str:
    """
    调用视觉 API（Anthropic 兼容格式，当前接入小米中转）。

    Args:
        content: user 消息的 content 列表（image + text blocks）
        max_tokens: 最大输出 token，None 则使用配置默认值
        system: 可选的 system prompt

    Returns:
        模型返回的文本内容
    """
    settings = get_settings()
    payload: dict = {
        "model": settings.VISION_MODEL,
        "max_tokens": max_tokens or settings.VISION_MAX_TOKENS,
        "messages": [{"role": "user", "content": content}],
    }
    if system:
        payload["system"] = system

    url = f"{settings.VISION_BASE_URL.rstrip('/')}/v1/messages"

    async with httpx.AsyncClient(timeout=settings.VISION_TIMEOUT) as client:
        response = await client.post(
            url,
            headers={
                "x-api-key": settings.VISION_AUTH_TOKEN,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    # 提取文本（第一个 text block）
    for block in data.get("content", []):
        if block.get("type") == "text":
            return block["text"]

    raise ValueError("Anthropic API 返回了空内容")


# ─────────────────────────────────────────────
# Tool 1: vision_describe
# ─────────────────────────────────────────────

@mcp_tool(
    name="vision_describe",
    description=(
        "通用图片描述与问答。输入图片路径（本地绝对路径或 https:// URL）和你想问的问题，"
        "返回详细的文字描述。适合理解截图内容、分析图表、识别界面元素等通用场景。"
    ),
)
async def vision_describe(
    image_source: str,
    question: str = "请详细描述这张图片的内容。",
) -> str:
    """
    对图片进行通用描述与问答。

    Args:
        image_source: 图片来源，支持本地绝对路径（/Users/mako/...）或 https:// URL
        question: 针对图片的问题，默认请求整体描述

    Returns:
        str: 模型对图片内容的分析结果

    Examples:
        vision_describe("/tmp/screenshot.png", "这个报错是什么意思？")
        vision_describe("https://example.com/chart.png", "图表显示了什么趋势？")
    """
    logger.info("vision_describe_start", image_source=image_source, question=question[:50])

    source = await _build_image_source(image_source)
    content = [
        {"type": "image", "source": source},
        {"type": "text", "text": question},
    ]

    result = await _call_vision(content)
    logger.info("vision_describe_done", chars=len(result))
    return result


# ─────────────────────────────────────────────
# Tool 2: vision_ocr
# ─────────────────────────────────────────────

@mcp_tool(
    name="vision_ocr",
    description=(
        "从图片中提取所有文字内容（OCR）。支持截图、扫描件、代码截图、错误日志图片等。"
        "返回识别出的纯文本，尽量保留原始格式和排版结构。"
    ),
)
async def vision_ocr(image_source: str) -> str:
    """
    提取图片中的文字。

    Args:
        image_source: 图片来源，支持本地绝对路径或 https:// URL

    Returns:
        str: 图片中识别出的文字内容
    """
    logger.info("vision_ocr_start", image_source=image_source)

    source = await _build_image_source(image_source)
    content = [
        {"type": "image", "source": source},
        {
            "type": "text",
            "text": (
                "请提取这张图片中的所有文字内容。"
                "要求：\n"
                "1. 完整提取所有可见文字，不要遗漏\n"
                "2. 尽量保留原始的排版结构（如代码缩进、表格对齐）\n"
                "3. 如果是代码，保留语言格式\n"
                "4. 不要添加任何解释或额外内容，只输出文字本身"
            ),
        },
    ]

    result = await _call_vision(content, max_tokens=4096)
    logger.info("vision_ocr_done", chars=len(result))
    return result


# ─────────────────────────────────────────────
# Tool 3: vision_compare
# ─────────────────────────────────────────────

@mcp_tool(
    name="vision_compare",
    description=(
        "对比两张图片，找出差异或进行比较分析。"
        "适用场景：UI 改版前后对比、设计稿 vs 实现对比、两个版本的截图对比等。"
        "可以通过 question 参数指定关注点。"
    ),
)
async def vision_compare(
    image_source_a: str,
    image_source_b: str,
    question: str = "请详细对比这两张图片的差异，列出所有不同点。",
) -> str:
    """
    对比两张图片。

    Args:
        image_source_a: 第一张图片（本地路径或 URL）
        image_source_b: 第二张图片（本地路径或 URL）
        question: 对比的具体问题，默认列出所有差异

    Returns:
        str: 对比分析结果
    """
    logger.info(
        "vision_compare_start",
        source_a=image_source_a,
        source_b=image_source_b,
        question=question[:50],
    )

    source_a = await _build_image_source(image_source_a)
    source_b = await _build_image_source(image_source_b)

    content = [
        {"type": "text", "text": "以下是需要对比的两张图片，第一张（图A）："},
        {"type": "image", "source": source_a},
        {"type": "text", "text": "第二张（图B）："},
        {"type": "image", "source": source_b},
        {"type": "text", "text": question},
    ]

    result = await _call_vision(content)
    logger.info("vision_compare_done", chars=len(result))
    return result


# ─────────────────────────────────────────────
# Tool 4: vision_ui_audit
# ─────────────────────────────────────────────

_UI_AUDIT_SYSTEM = """你是一位资深前端工程师，同时具备 UI/UX 审查经验。
分析用户提供的界面截图，从以下维度给出专业评估：
1. 视觉层次与信息架构
2. 间距、对齐、一致性（8px 栅格系统）
3. 颜色对比度与可访问性（WCAG 标准）
4. 交互状态完整性（hover/focus/disabled/error）
5. 响应式与边界情况（文字截断、空状态、加载态）
6. 潜在的用户体验问题
输出结构清晰，使用 Markdown 格式，按严重程度（critical/warning/suggestion）分类。"""


@mcp_tool(
    name="vision_ui_audit",
    description=(
        "前端 UI 质量审查。分析界面截图，从视觉层次、间距对齐、颜色对比度、"
        "交互状态完整性、响应式等维度给出专业评估报告，按严重程度分级输出。"
        "适合 code review 前的 UI 自查，或设计还原度评估。"
    ),
)
async def vision_ui_audit(
    image_source: str,
    focus: str = "全面审查",
) -> str:
    """
    对界面截图进行 UI 质量审查。

    Args:
        image_source: 界面截图路径或 URL
        focus: 重点关注的方向，如"表单交互状态"、"移动端适配"，默认全面审查

    Returns:
        str: Markdown 格式的 UI 审查报告
    """
    logger.info("vision_ui_audit_start", image_source=image_source, focus=focus)

    source = await _build_image_source(image_source)
    question = f"请对这个界面进行 UI 质量审查。重点关注：{focus}"

    content = [
        {"type": "image", "source": source},
        {"type": "text", "text": question},
    ]

    result = await _call_vision(content, system=_UI_AUDIT_SYSTEM)
    logger.info("vision_ui_audit_done", chars=len(result))
    return result
