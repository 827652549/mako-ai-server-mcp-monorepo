"""
vision 集成测试 - 直接调用函数，验证真实 API 通路
"""
import asyncio
import sys
from pathlib import Path

# 加载 .env
import os
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

sys.path.insert(0, str(Path(__file__).parent.parent))

LOCAL_IMAGE = "/Users/mako/Downloads/IMG_CD369B45884D-1.jpeg"
REMOTE_IMAGE = "https://github.githubassets.com/favicons/favicon-dark.png"

async def test_local_image_describe():
    """本地图片 - vision_describe"""
    from app.tools.vision import vision_describe
    print("\n[1] 本地图片描述测试...")
    result = await vision_describe(LOCAL_IMAGE, "请简单描述这张图片的内容。")
    assert isinstance(result, str) and len(result) > 0
    print(f"    ✓ 返回 {len(result)} 字")
    print(f"    内容预览: {result[:120]}...")
    return result

async def test_remote_image_describe():
    """远程 URL 图片 - vision_describe"""
    from app.tools.vision import vision_describe
    print("\n[2] 远程图片描述测试...")
    result = await vision_describe(REMOTE_IMAGE, "这是什么图标？是哪个网站的？")
    assert isinstance(result, str) and len(result) > 0
    print(f"    ✓ 返回 {len(result)} 字")
    print(f"    内容预览: {result[:120]}...")
    return result

async def test_local_image_ocr():
    """本地图片 - vision_ocr"""
    from app.tools.vision import vision_ocr
    print("\n[3] 本地图片 OCR 测试...")
    result = await vision_ocr(LOCAL_IMAGE)
    assert isinstance(result, str)
    print(f"    ✓ 返回 {len(result)} 字")
    print(f"    内容预览: {result[:120]}...")
    return result

async def test_compare():
    """对比本地图片和远程图片"""
    from app.tools.vision import vision_compare
    print("\n[4] 图片对比测试（本地 vs 远程）...")
    result = await vision_compare(LOCAL_IMAGE, REMOTE_IMAGE, "这两张图片分别是什么？有什么不同？")
    assert isinstance(result, str) and len(result) > 0
    print(f"    ✓ 返回 {len(result)} 字")
    print(f"    内容预览: {result[:120]}...")
    return result

async def main():
    passed = 0
    failed = 0
    tests = [
        test_local_image_describe,
        test_remote_image_describe,
        test_local_image_ocr,
        test_compare,
    ]
    for test in tests:
        try:
            await test()
            passed += 1
        except Exception as e:
            print(f"    ✗ 失败: {e}")
            failed += 1
    print(f"\n结果: {passed} 通过 / {failed} 失败")
    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
