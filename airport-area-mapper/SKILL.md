---
name: airport-area-mapper
description: 从Excel读取机场/地点列表，自动抓取高德地图卫星图，测量建筑物占地面积，并将结果回写到Excel。用于机场规划、地理信息分析、建筑物面积统计等场景。当用户需要从高德地图批量获取地点卫星图并测量建筑物面积时使用此skill。
---

# 机场/地点面积测量工作流

自动化整合流程：Excel → 高德地图 → 截图 → 面积测量 → Excel导出

## 功能概览

1. **读取Excel**: 从Excel文件读取地点/机场名称列表
2. **高德截图**: 自动访问高德地图，搜索地点并截取卫星视图
3. **面积测量**: 交互式测量建筑物占地面积（多边形框选）
4. **结果导出**: 将测量数据整理并导出到Excel

## 前置依赖

```bash
# 系统依赖
apt install python3-opencv python3-numpy python3-pandas python3-openpyxl

# Python依赖 (用于自动截图)
pip3 install playwright
playwright install chromium
```

## 使用步骤

### 步骤1: 准备Excel文件

Excel文件需要包含一列地点名称，列名可以是：
- `地点`
- `机场名`
- `名称`
- `机场`
- `location`
- `name`

示例:
| 机场名 | 城市 |
|--------|------|
| 北京首都国际机场 | 北京 |
| 上海浦东国际机场 | 上海 |
| 广州白云国际机场 | 广州 |

### 步骤2: 读取Excel并生成截图任务

```bash
cd /root/.openclaw/workspace/skills/airport-area-mapper/scripts

# 查看Excel中的地点列表
python3 airport_mapper.py /path/to/airports.xlsx read
```

### 步骤3: 自动截图（可选）

**方式A: 使用Playwright自动截图**

```bash
# 单个地点
python3 amap_screenshot.py '北京首都国际机场' ./output/screenshots/首都机场.png

# 批量截图
python3 amap_screenshot.py --batch '机场A' '机场B' '机场C' --output ./output/screenshots
```

**方式B: 使用OpenClaw浏览器工具**

```
browser action:open targetUrl:"https://ditu.amap.com/search?query=北京首都国际机场"
```

然后手动调整地图视角并截图保存到 `./output/screenshots/`

**方式C: 生成HTML指引文件**

```bash
python3 airport_mapper.py /path/to/airports.xlsx guide
```

生成的 `output/screenshots/screenshot_guide.html` 可以在浏览器中打开，点击链接快速跳转到对应地点。

### 步骤4: 测量建筑物面积

使用 `airport_measurer.py` 进行交互式测量：

```bash
python3 airport_measurer.py ./output/screenshots/北京首都国际机场.png
```

**操作流程**:
1. 按 `C` 进入标定模式
   - 点击两个已知实际距离的点（如跑道两端）
   - 输入实际距离（米）
   - 程序自动建立像素-米比例

2. 按 `M` 进入测量模式
   - 左键点击：添加多边形顶点
   - 中键点击：撤销上一个点
   - 右键点击：完成测量
   - 输入建筑物名称和备注

3. 按 `S` 保存结果
4. 按 `Q` 退出

测量结果会保存在 `./output/measurements/` 目录

### 步骤5: 导出结果到Excel

```bash
python3 airport_mapper.py /path/to/airports.xlsx export
```

结果会生成一个新的Excel文件 `airport_measurements_YYYYMMDD_HHMMSS.xlsx`，包含：
- 建筑物名称
- 像素面积
- 实际面积（平方米）
- 实际面积（公顷）
- 备注

## 快速开始（一键流程）

```bash
# 1. 进入skill目录
cd /root/.openclaw/workspace/skills/airport-area-mapper/scripts

# 2. 准备Excel文件 (如: airports.xlsx)

# 3. 运行完整流程
python3 airport_mapper.py ./airports.xlsx all

# 4. 根据提示完成截图和测量

# 5. 导出结果
python3 airport_mapper.py ./airports.xlsx export
```

## 文件结构

```
output/
├── screenshots/
│   ├── 北京首都国际机场.png
│   ├── 上海浦东国际机场.png
│   └── ...
├── measurements/
│   ├── 北京首都国际机场_measurements_20240308_171000.csv
│   └── ...
├── screenshot_guide.html  # 截图指引页面
└── workflow_state.json    # 工作流状态

airport_measurements_20240308_171000.xlsx  # 最终结果
```

## 脚本说明

### airport_mapper.py
主工作流脚本，整合所有步骤。

```bash
python3 airport_mapper.py <excel文件> [命令]

命令:
  read      - 读取Excel
  urls      - 生成高德URL
  guide     - 生成截图指引
  measure   - 测量面积
  export    - 导出到Excel
  all       - 运行全部步骤
```

### amap_screenshot.py
Playwright自动截图工具。

```bash
python3 amap_screenshot.py '<地点名>' [输出路径]
python3 amap_screenshot.py --batch '<地点1>' '<地点2>' ... --output <目录>
```

### airport_measurer.py
交互式面积测量工具（见 references/measurer.md）。

## 注意事项

1. **高德地图限制**: 频繁访问可能导致IP被限，建议截图间隔不要太短
2. **比例尺标定**: 测量前必须准确标定比例尺，否则面积数据不准确
3. **截图质量**: 建议使用1920x1080或更高分辨率，卫星视图能看清建筑物轮廓
4. **输出目录**: 默认在Excel文件同级目录创建 `output` 文件夹

## 进阶用法

### 使用OpenClaw浏览器工具截图

```
# 打开高德地图
browser action:open targetUrl:"https://ditu.amap.com/search?query=北京首都国际机场"

# 等待加载后截图
browser action:snapshot fullPage:true
```

### 批量处理多个Excel

```bash
for file in *.xlsx; do
    python3 airport_mapper.py "$file" all
done
```

## 故障排除

### Playwright安装失败
```bash
# 安装系统依赖
apt install libnss3 libatk-bridge2.0 libxss1 libgtk-3-0

# 重新安装playwright
pip3 install playwright
playwright install chromium
```

### OpenCV报错
```bash
apt install python3-opencv python3-numpy
```

### Excel读取失败
```bash
pip3 install pandas openpyxl
```
