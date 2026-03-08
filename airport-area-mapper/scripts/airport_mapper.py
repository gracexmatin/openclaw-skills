#!/usr/bin/env python3
"""
机场/地点高德地图抓取 + 面积测量自动化工具
整合流程：Excel读取 → 高德截图 → 面积测量 → 结果回写
"""

import sys
import os
import time
import json
import pandas as pd
from datetime import datetime
from pathlib import Path

# 确保能导入依赖
try:
    import cv2
    import numpy as np
except ImportError:
    print("错误: 需要安装 OpenCV 和 NumPy")
    print("运行: apt install python3-opencv python3-numpy")
    sys.exit(1)


class AirportAreaMapper:
    """机场面积测量工作流管理器"""
    
    def __init__(self, excel_path: str, output_dir: str = None):
        self.excel_path = excel_path
        self.excel_dir = Path(excel_path).parent
        self.output_dir = Path(output_dir) if output_dir else self.excel_dir / "output"
        self.output_dir.mkdir(exist_ok=True)
        
        # 截图保存目录
        self.screenshots_dir = self.output_dir / "screenshots"
        self.screenshots_dir.mkdir(exist_ok=True)
        
        # 测量结果目录
        self.measurements_dir = self.output_dir / "measurements"
        self.measurements_dir.mkdir(exist_ok=True)
        
        # 加载数据
        self.df = None
        self.results = []
        
    def load_excel(self, sheet_name=0, location_column="地点"):
        """加载Excel，查找地点列"""
        print(f"加载Excel: {self.excel_path}")
        
        # 尝试多种常见列名
        possible_columns = ["地点", "机场名", "名称", "机场", "location", "name", "机场名称"]
        
        try:
            # 尝试读取Excel
            self.df = pd.read_excel(self.excel_path, sheet_name=sheet_name)
            print(f"  共 {len(self.df)} 行数据")
            print(f"  列名: {list(self.df.columns)}")
            
            # 查找地点列
            for col in possible_columns:
                if col in self.df.columns:
                    self.location_column = col
                    print(f"  使用地点列: '{col}'")
                    return True
            
            # 如果没找到，使用第一列
            self.location_column = self.df.columns[0]
            print(f"  未找到标准地点列，使用第一列: '{self.location_column}'")
            return True
            
        except Exception as e:
            print(f"错误: 无法读取Excel文件: {e}")
            return False
    
    def get_locations(self):
        """获取所有地点名称列表"""
        if self.df is None:
            return []
        locations = self.df[self.location_column].dropna().astype(str).tolist()
        return [loc.strip() for loc in locations if loc.strip()]
    
    def generate_amap_url(self, location: str) -> str:
        """生成高德地图搜索URL"""
        # 高德地图搜索URL格式
        encoded = location.replace(" ", "%20").replace("(", "%28").replace(")", "%29")
        return f"https://ditu.amap.com/search?query={encoded}"
    
    def save_workflow_state(self, step: str, data: dict):
        """保存工作流状态，方便断点续传"""
        state_file = self.output_dir / "workflow_state.json"
        state = {
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "excel_path": str(self.excel_path),
            "data": data
        }
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        print(f"  状态已保存: {step}")


def step1_read_excel(excel_path: str) -> list:
    """
    步骤1: 读取Excel获取地点列表
    
    返回:
        list: 地点名称列表
    """
    print("\n" + "="*60)
    print("步骤1: 读取Excel文件")
    print("="*60)
    
    mapper = AirportAreaMapper(excel_path)
    if not mapper.load_excel():
        return []
    
    locations = mapper.get_locations()
    print(f"\n找到 {len(locations)} 个地点:")
    for i, loc in enumerate(locations[:10], 1):  # 只显示前10个
        print(f"  {i}. {loc}")
    if len(locations) > 10:
        print(f"  ... 还有 {len(locations) - 10} 个")
    
    return locations


def step2_prepare_amap_urls(locations: list) -> dict:
    """
    步骤2: 生成高德地图搜索URL
    
    返回:
        dict: {地点名: URL}
    """
    print("\n" + "="*60)
    print("步骤2: 生成高德地图搜索URL")
    print("="*60)
    
    mapper = AirportAreaMapper("")  # 临时实例用于URL生成
    urls = {}
    
    print(f"\n生成 {len(locations)} 个URL:")
    for loc in locations[:5]:  # 只显示前5个
        url = mapper.generate_amap_url(loc)
        urls[loc] = url
        print(f"  {loc}")
        print(f"    → {url}")
    
    if len(locations) > 5:
        print(f"  ... 还有 {len(locations) - 5} 个")
        for loc in locations[5:]:
            urls[loc] = mapper.generate_amap_url(loc)
    
    return urls


def step3_screenshot_guide(urls: dict, output_dir: str):
    """
    步骤3: 截图操作指南
    由于浏览器自动化需要手动操作，这里输出操作指南
    """
    print("\n" + "="*60)
    print("步骤3: 高德地图截图")
    print("="*60)
    
    print("""
⚠️  注意: 此步骤需要手动操作浏览器

操作步骤:
1. 打开 Chrome/Edge 浏览器
2. 访问高德地图: https://ditu.amap.com
3. 搜索每个地点，调整地图视角使机场完全显示
4. 截图保存到指定目录

或者使用OpenClaw的浏览器自动化功能:
   browser action:open targetUrl:"https://ditu.amap.com/search?query=北京首都国际机场"

推荐的截图参数:
- 分辨率: 1920x1080 或更高
- 缩放级别: 卫星视图，能看到建筑物轮廓
- 每个地点保存为: <地点名>.png

保存位置: {screenshots_dir}
""".format(screenshots_dir=output_dir))
    
    # 生成本地HTML指引文件
    html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>机场地图截图指引</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }
        .location { border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }
        .location:hover { background: #f5f5f5; }
        .name { font-size: 18px; font-weight: bold; margin-bottom: 10px; }
        .url { color: #0066cc; word-break: break-all; }
        .actions { margin-top: 10px; }
        .btn { 
            display: inline-block; 
            padding: 8px 16px; 
            background: #0066cc; 
            color: white; 
            text-decoration: none; 
            border-radius: 4px;
            margin-right: 10px;
        }
        .status { 
            display: inline-block; 
            padding: 5px 10px; 
            border-radius: 3px;
            font-size: 12px;
        }
        .pending { background: #ffcc00; color: #333; }
        .done { background: #00cc66; color: white; }
    </style>
</head>
<body>
    <h1>🏢 机场地图截图指引</h1>
    <p>点击"打开地图"在新窗口打开高德地图，调整视角后截图保存。</p>
    <hr>
"""
    
    for i, (loc, url) in enumerate(urls.items(), 1):
        safe_name = loc.replace("/", "_").replace("\\", "_")
        screenshot_path = Path(output_dir) / f"{safe_name}.png"
        exists = screenshot_path.exists()
        status_class = "done" if exists else "pending"
        status_text = "✓ 已截图" if exists else "⏳ 待截图"
        
        html_content += f"""
    <div class="location">
        <div class="name">{i}. {loc}</div>
        <div class="url">{url}</div>
        <div class="actions">
            <a href="{url}" target="_blank" class="btn">打开地图</a>
            <span class="status {status_class}">{status_text}</span>
        </div>
    </div>
"""
    
    html_content += """
</body>
</html>
"""
    
    guide_file = Path(output_dir) / "screenshot_guide.html"
    with open(guide_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n已生成本地指引文件: {guide_file}")
    print("可用浏览器打开此文件，点击链接快速跳转")


def step4_measure_area(screenshots_dir: str, locations: list = None):
    """
    步骤4: 测量建筑物面积
    调用 airport_measurer.py 进行交互式测量
    """
    print("\n" + "="*60)
    print("步骤4: 测量建筑物面积")
    print("="*60)
    
    screenshots_path = Path(screenshots_dir)
    
    if not screenshots_path.exists():
        print(f"错误: 截图目录不存在: {screenshots_dir}")
        print("请先完成步骤3的截图")
        return []
    
    # 查找所有截图
    images = list(screenshots_path.glob("*.png")) + list(screenshots_path.glob("*.jpg"))
    
    if not images:
        print(f"错误: 在 {screenshots_dir} 中没有找到截图文件")
        return []
    
    print(f"\n找到 {len(images)} 张截图:")
    for img in images:
        print(f"  - {img.name}")
    
    print("""
\n接下来需要对每张图片进行交互式测量:
1. 按 C 进入标定模式（选择两个已知距离的点）
2. 按 M 进入测量模式（框选建筑物）
3. 按 S 保存结果

测量完成后，数据将保存在 measurements/ 目录
""")
    
    return images


def step5_export_to_excel(excel_path: str, measurements_dir: str):
    """
    步骤5: 将测量结果导出到Excel
    """
    print("\n" + "="*60)
    print("步骤5: 导出结果到Excel")
    print("="*60)
    
    measurements_path = Path(measurements_dir)
    
    if not measurements_path.exists():
        print(f"错误: 测量结果目录不存在: {measurements_dir}")
        return False
    
    # 读取所有CSV结果
    csv_files = list(measurements_path.glob("*_measurements_*.csv"))
    
    if not csv_files:
        print("错误: 没有找到测量结果CSV文件")
        return False
    
    print(f"\n找到 {len(csv_files)} 个测量结果文件")
    
    # 合并所有测量结果
    all_measurements = []
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            # 从文件名提取地点名
            location_name = csv_file.stem.split("_measurements_")[0]
            df["来源地点"] = location_name
            all_measurements.append(df)
            print(f"  ✓ {csv_file.name}: {len(df)} 条记录")
        except Exception as e:
            print(f"  ✗ {csv_file.name}: {e}")
    
    if not all_measurements:
        print("错误: 没有成功读取任何测量结果")
        return False
    
    # 合并数据
    combined_df = pd.concat(all_measurements, ignore_index=True)
    
    # 生成输出文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_excel = Path(excel_path).parent / f"airport_measurements_{timestamp}.xlsx"
    
    # 保存到Excel
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        combined_df.to_excel(writer, sheet_name='测量结果', index=False)
    
    print(f"\n✅ 结果已保存: {output_excel}")
    print(f"   总计: {len(combined_df)} 条测量记录")
    
    # 打印汇总
    print("\n=== 测量汇总 ===")
    total_area = combined_df['real_area_sqm'].sum()
    print(f"总面积: {total_area:,.2f} 平方米 ({total_area/10000:.4f} 公顷)")
    
    return True


def main():
    """主函数 - 命令行入口"""
    if len(sys.argv) < 2:
        print("用法:")
        print("  python3 airport_mapper.py <excel文件> [命令]")
        print("")
        print("命令:")
        print("  read      - 步骤1: 读取Excel")
        print("  urls      - 步骤2: 生成高德URL")
        print("  guide     - 步骤3: 生成截图指引")
        print("  measure   - 步骤4: 测量面积")
        print("  export    - 步骤5: 导出到Excel")
        print("  all       - 运行全部步骤")
        print("")
        print("示例:")
        print("  python3 airport_mapper.py airports.xlsx read")
        print("  python3 airport_mapper.py airports.xlsx all")
        sys.exit(1)
    
    excel_path = sys.argv[1]
    command = sys.argv[2] if len(sys.argv) > 2 else "all"
    
    if not os.path.exists(excel_path):
        print(f"错误: 文件不存在: {excel_path}")
        sys.exit(1)
    
    # 确定输出目录
    output_dir = Path(excel_path).parent / "output"
    screenshots_dir = output_dir / "screenshots"
    measurements_dir = output_dir / "measurements"
    
    if command in ("read", "all"):
        locations = step1_read_excel(excel_path)
        if not locations:
            sys.exit(1)
    else:
        locations = []
    
    if command in ("urls", "all"):
        if not locations:
            locations = step1_read_excel(excel_path)
        urls = step2_prepare_amap_urls(locations)
    else:
        urls = {}
    
    if command in ("guide", "all"):
        if not urls:
            if not locations:
                locations = step1_read_excel(excel_path)
            urls = step2_prepare_amap_urls(locations)
        step3_screenshot_guide(urls, str(screenshots_dir))
    
    if command == "measure":
        step4_measure_area(str(screenshots_dir), locations)
    
    if command == "export":
        step5_export_to_excel(excel_path, str(measurements_dir))
    
    if command == "all":
        print("\n" + "="*60)
        print("工作流完成!")
        print("="*60)
        print(f"\n请按以下顺序手动完成剩余步骤:")
        print(f"1. 截图: 打开 {output_dir}/screenshot_guide.html")
        print(f"2. 截图保存到: {screenshots_dir}")
        print(f"3. 测量: python3 airport_measurer.py <截图文件>")
        print(f"4. 导出: python3 airport_mapper.py {excel_path} export")


if __name__ == "__main__":
    main()
