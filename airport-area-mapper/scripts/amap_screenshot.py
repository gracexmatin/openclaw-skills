#!/usr/bin/env python3
"""
高德地图自动截图工具
使用Playwright自动化浏览器截图
"""

import asyncio
import sys
import os
from pathlib import Path
from urllib.parse import quote

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("错误: 需要安装 Playwright")
    print("运行: pip3 install playwright")
    print("然后: playwright install chromium")
    sys.exit(1)


async def screenshot_amap(location: str, output_path: str, wait_time: int = 5):
    """
    对高德地图指定位置进行截图
    
    Args:
        location: 搜索的地点名称
        output_path: 截图保存路径
        wait_time: 等待地图加载时间（秒）
    """
    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080}
        )
        page = await context.new_page()
        
        try:
            # 构建搜索URL
            encoded = quote(location)
            url = f"https://ditu.amap.com/search?query={encoded}"
            
            print(f"正在访问: {url}")
            await page.goto(url, wait_until="networkidle")
            
            # 等待页面加载
            print(f"等待 {wait_time} 秒让地图加载...")
            await asyncio.sleep(wait_time)
            
            # 尝试切换到卫星视图
            try:
                # 查找卫星图按钮并点击
                satellite_btn = await page.query_selector('[title="卫星"]')
                if satellite_btn:
                    await satellite_btn.click()
                    await asyncio.sleep(2)
                    print("已切换到卫星视图")
            except Exception as e:
                print(f"切换卫星视图失败（可能已处于卫星视图）: {e}")
            
            # 截图
            await page.screenshot(path=output_path, full_page=False)
            print(f"✅ 截图已保存: {output_path}")
            
        except Exception as e:
            print(f"错误: {e}")
        finally:
            await browser.close()


async def batch_screenshot(locations: list, output_dir: str):
    """批量截图"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"\n开始批量截图，共 {len(locations)} 个地点")
    print(f"输出目录: {output_dir}\n")
    
    for i, location in enumerate(locations, 1):
        safe_name = location.replace("/", "_").replace("\\", "_")
        screenshot_file = output_path / f"{safe_name}.png"
        
        print(f"[{i}/{len(locations)}] {location}")
        await screenshot_amap(location, str(screenshot_file))
        print()


def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python3 amap_screenshot.py '<地点名>' [输出路径]")
        print("  python3 amap_screenshot.py --batch <地点1> <地点2> ... --output <目录>")
        print("")
        print("示例:")
        print("  python3 amap_screenshot.py '北京首都国际机场' ./首都机场.png")
        print("  python3 amap_screenshot.py --batch '机场A' '机场B' '机场C' --output ./screenshots")
        sys.exit(1)
    
    if sys.argv[1] == "--batch":
        # 批量模式
        locations = []
        output_dir = "./screenshots"
        
        i = 2
        while i < len(sys.argv):
            if sys.argv[i] == "--output":
                output_dir = sys.argv[i + 1]
                i += 2
            else:
                locations.append(sys.argv[i])
                i += 1
        
        if not locations:
            print("错误: 请提供至少一个地点")
            sys.exit(1)
        
        asyncio.run(batch_screenshot(locations, output_dir))
    else:
        # 单点模式
        location = sys.argv[1]
        output_path = sys.argv[2] if len(sys.argv) > 2 else f"{location}.png"
        
        asyncio.run(screenshot_amap(location, output_path))


if __name__ == "__main__":
    main()
