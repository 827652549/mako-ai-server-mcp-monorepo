"""
vision 工具单元测试
使用 mock 隔离 Anthropic API 调用
"""
import base64
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.tools.vision import _build_image_source, _call_vision


class TestBuildImageSource:
    def test_url_http(self):
        src = _build_image_source("http://example.com/img.png")
        assert src["type"] == "url"
        assert src["url"] == "http://example.com/img.png"

    def test_url_https(self):
        src = _build_image_source("https://example.com/img.png")
        assert src["type"] == "url"

    def test_local_file(self, tmp_path: Path):
        img = tmp_path / "test.png"
        img.write_bytes(b"fake-image-data")
        src = _build_image_source(str(img))
        assert src["type"] == "base64"
        assert src["media_type"] == "image/png"
        decoded = base64.standard_b64decode(src["data"])
        assert decoded == b"fake-image-data"

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            _build_image_source("/nonexistent/path/img.png")

    def test_unknown_extension_fallback(self, tmp_path: Path):
        img = tmp_path / "test.xyz"
        img.write_bytes(b"data")
        src = _build_image_source(str(img))
        assert src["media_type"] == "image/jpeg"


class TestCallVision:
    @pytest.mark.asyncio
    async def test_returns_text(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": [{"type": "text", "text": "这是描述"}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("app.tools.vision.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            result = await _call_vision(
                content=[{"type": "text", "text": "test"}]
            )
            assert result == "这是描述"

    @pytest.mark.asyncio
    async def test_empty_content_raises(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"content": []}
        mock_response.raise_for_status = MagicMock()

        with patch("app.tools.vision.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            with pytest.raises(ValueError, match="空内容"):
                await _call_vision(content=[])
