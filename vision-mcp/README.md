# vision-mcp

为无多模态能力的模型提供视觉工具箱的 MCP Server。

## 工具

| 工具 | 功能 |
|------|------|
| `vision_describe` | 通用图片描述与问答 |
| `vision_ocr` | 提取图片中的文字 |
| `vision_compare` | 对比两张图片的差异 |
| `vision_ui_audit` | 前端 UI 质量审查 |

## 快速开始

```bash
cd vision-mcp
cp .env.example .env
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8001
```

## Claude Code 接入

```json
{
  "vision-mcp": {
    "type": "http",
    "url": "http://localhost:8001/mcp",
    "headers": { "X-API-Key": "your-key" }
  }
}
```

## 支持的图片输入

- 本地绝对路径：`/Users/mako/screenshots/ui.png`
- HTTPS URL：`https://example.com/image.png`
- 支持格式：jpeg、png、gif、webp
