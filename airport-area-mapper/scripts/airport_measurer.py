#!/usr/bin/env python3
"""
机场俯视图建筑物占地面积测量工具
Airport Building Area Measurer

使用方法:
    python3 airport_measurer.py <image_path>

功能:
    1. 标定模式: 选择两个点，输入实际距离，建立像素-米比例
    2. 测量模式: 框选建筑物，自动计算占地面积
    3. 导出: 带标注的结果图 + CSV数据表
"""

import cv2
import numpy as np
import csv
import sys
import os
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Tuple, Optional


@dataclass
class Measurement:
    """单个测量记录"""
    name: str
    pixel_area: float
    real_area_sqm: float
    real_area_hectare: float
    notes: str = ""


class AirportMeasurer:
    def __init__(self, image_path: str):
        self.image_path = image_path
        self.original_image = cv2.imread(image_path)
        if self.original_image is None:
            raise ValueError(f"无法加载图片: {image_path}")
        
        self.display_image = self.original_image.copy()
        self.scale_factor = None  # 米/像素
        
        # 标定相关
        self.calibration_points = []
        
        # 测量相关
        self.current_measure_points = []
        self.measurements: List[Measurement] = []
        
        # 窗口名称
        self.window_name = "Airport Measurer - 机场测量工具"
        
    def reset_display(self):
        """重置显示图像"""
        self.display_image = self.original_image.copy()
        self._draw_ui()
        
    def _draw_ui(self):
        """绘制UI信息"""
        h, w = self.display_image.shape[:2]
        
        # 绘制信息面板
        panel_h = 100
        cv2.rectangle(self.display_image, (0, 0), (w, panel_h), (40, 40, 40), -1)
        
        # 显示比例尺状态
        if self.scale_factor:
            scale_text = f"比例尺: 1像素 = {self.scale_factor:.4f}米 | 1米 = {1/self.scale_factor:.2f}像素"
            cv2.putText(self.display_image, scale_text, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        else:
            cv2.putText(self.display_image, "比例尺: 未标定 (按C开始标定)", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        # 显示操作提示
        cv2.putText(self.display_image, "[C]标定 [M]测量 [S]保存 [R]重置 [Q]退出", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        # 显示测量数量
        cv2.putText(self.display_image, f"已测量: {len(self.measurements)}个建筑物", (10, 85), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        # 绘制所有已保存的测量区域
        for i, m in enumerate(self.measurements):
            # 这里简化显示，实际应该存储多边形点
            pass
    
    def pixel_distance(self, p1: Tuple[int, int], p2: Tuple[int, int]) -> float:
        """计算两点像素距离"""
        return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
    
    def real_distance(self, pixel_dist: float) -> float:
        """像素距离转实际距离"""
        if self.scale_factor is None:
            return 0
        return pixel_dist * self.scale_factor
    
    def real_area(self, pixel_area: float) -> float:
        """像素面积转实际面积（平方米）"""
        if self.scale_factor is None:
            return 0
        return pixel_area * (self.scale_factor ** 2)
    
    def calibration_mode(self):
        """标定模式 - 建立像素与实际距离的关系"""
        print("\n=== 标定模式 ===")
        print("请在图片上点击两个点作为参考距离")
        print("建议选择已知长度的物体（如跑道宽度、航站楼长度等）")
        
        self.calibration_points = []
        self.reset_display()
        
        def mouse_callback(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                if len(self.calibration_points) < 2:
                    self.calibration_points.append((x, y))
                    # 绘制点
                    cv2.circle(self.display_image, (x, y), 5, (0, 255, 255), -1)
                    cv2.putText(self.display_image, f"P{len(self.calibration_points)}", 
                               (x+10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
                    cv2.imshow(self.window_name, self.display_image)
                    
                    if len(self.calibration_points) == 2:
                        # 绘制连线
                        cv2.line(self.display_image, self.calibration_points[0], 
                                self.calibration_points[1], (0, 255, 255), 2)
                        pixel_dist = self.pixel_distance(*self.calibration_points)
                        cv2.putText(self.display_image, f"{pixel_dist:.1f}px", 
                                   ((self.calibration_points[0][0] + self.calibration_points[1][0])//2,
                                    (self.calibration_points[0][1] + self.calibration_points[1][1])//2 - 10),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
                        cv2.imshow(self.window_name, self.display_image)
                        
                        print(f"\n像素距离: {pixel_dist:.2f} 像素")
                        real_dist = float(input("请输入实际距离（米）: "))
                        self.scale_factor = real_dist / pixel_dist
                        print(f"比例尺设定: 1像素 = {self.scale_factor:.4f}米")
                        print("按任意键继续...")
        
        cv2.setMouseCallback(self.window_name, mouse_callback)
        print("点击两个点...")
        cv2.waitKey(0)
        cv2.setMouseCallback(self.window_name, lambda *args: None)
        self.reset_display()
    
    def measure_polygon_mode(self):
        """多边形测量模式 - 框选建筑物计算面积"""
        if self.scale_factor is None:
            print("\n[!] 请先进行标定（按C）")
            return
        
        print("\n=== 多边形测量模式 ===")
        print("点击建筑物的各个顶点，右键完成，中键取消上一个点")
        
        self.current_measure_points = []
        temp_image = self.display_image.copy()
        
        def mouse_callback(event, x, y, flags, param):
            nonlocal temp_image
            
            if event == cv2.EVENT_LBUTTONDOWN:
                self.current_measure_points.append((x, y))
                # 重绘
                temp_image = self.display_image.copy()
                self._draw_polygon(temp_image, self.current_measure_points, incomplete=True)
                cv2.imshow(self.window_name, temp_image)
                
            elif event == cv2.EVENT_RBUTTONDOWN:
                # 右键完成
                if len(self.current_measure_points) >= 3:
                    self._finish_measurement()
                else:
                    print("需要至少3个点才能计算面积")
                    
            elif event == cv2.EVENT_MBUTTONDOWN:
                # 中键撤销上一个点
                if self.current_measure_points:
                    self.current_measure_points.pop()
                    temp_image = self.display_image.copy()
                    self._draw_polygon(temp_image, self.current_measure_points, incomplete=True)
                    cv2.imshow(self.window_name, temp_image)
        
        cv2.setMouseCallback(self.window_name, mouse_callback)
        print("左键:添加点 | 右键:完成 | 中键:撤销 | 按ESC取消")
        
        while True:
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                break
        
        cv2.setMouseCallback(self.window_name, lambda *args: None)
        self.reset_display()
    
    def _draw_polygon(self, image, points: List[Tuple[int, int]], incomplete: bool = False):
        """绘制多边形"""
        if len(points) < 2:
            return
        
        color = (0, 165, 255) if incomplete else (0, 255, 0)
        
        # 绘制边
        for i in range(len(points) - 1):
            cv2.line(image, points[i], points[i+1], color, 2)
            cv2.circle(image, points[i], 4, color, -1)
        
        cv2.circle(image, points[-1], 4, color, -1)
        
        if not incomplete and len(points) >= 3:
            # 闭合
            cv2.line(image, points[-1], points[0], color, 2)
            # 填充半透明
            overlay = image.copy()
            pts = np.array(points, np.int32).reshape((-1, 1, 2))
            cv2.fillPoly(overlay, [pts], (0, 255, 0))
            cv2.addWeighted(overlay, 0.3, image, 0.7, 0, image)
    
    def _finish_measurement(self):
        """完成当前测量"""
        if len(self.current_measure_points) < 3:
            return
        
        # 计算多边形面积（像素）
        pts = np.array(self.current_measure_points)
        pixel_area = self._polygon_area(pts)
        
        # 转换为实际面积
        real_area_sqm = self.real_area(pixel_area)
        real_area_ha = real_area_sqm / 10000
        
        print(f"\n--- 测量结果 ---")
        print(f"像素面积: {pixel_area:.2f} 平方像素")
        print(f"实际面积: {real_area_sqm:.2f} 平方米 ({real_area_ha:.4f} 公顷)")
        
        name = input("请输入建筑物名称（如：T1航站楼）: ").strip()
        notes = input("备注（可选）: ").strip()
        
        measurement = Measurement(
            name=name or f"建筑{len(self.measurements)+1}",
            pixel_area=pixel_area,
            real_area_sqm=real_area_sqm,
            real_area_hectare=real_area_ha,
            notes=notes
        )
        self.measurements.append(measurement)
        
        # 保存到显示图像
        self._draw_polygon(self.display_image, self.current_measure_points, incomplete=False)
        
        # 添加标签
        centroid = self._polygon_centroid(self.current_measure_points)
        label = f"{measurement.name}: {real_area_sqm:.0f}m"
        cv2.putText(self.display_image, label, centroid, 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        print(f"已保存: {measurement.name}")
        self.current_measure_points = []
    
    def _polygon_area(self, pts: np.ndarray) -> float:
        """计算多边形面积（使用鞋带公式）"""
        n = len(pts)
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += pts[i][0] * pts[j][1]
            area -= pts[j][0] * pts[i][1]
        return abs(area) / 2.0
    
    def _polygon_centroid(self, points: List[Tuple[int, int]]) -> Tuple[int, int]:
        """计算多边形中心点"""
        x = sum(p[0] for p in points) // len(points)
        y = sum(p[1] for p in points) // len(points)
        return (x, y)
    
    def save_results(self):
        """保存结果"""
        if not self.measurements:
            print("没有测量数据可保存")
            return
        
        base_name = os.path.splitext(self.image_path)[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存带标注的图片
        output_image = f"{base_name}_measured_{timestamp}.png"
        cv2.imwrite(output_image, self.display_image)
        print(f"\n标注图片已保存: {output_image}")
        
        # 保存CSV
        output_csv = f"{base_name}_measurements_{timestamp}.csv"
        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['name', 'pixel_area', 'real_area_sqm', 'real_area_hectare', 'notes']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for m in self.measurements:
                writer.writerow(asdict(m))
        print(f"数据表已保存: {output_csv}")
        
        # 打印汇总
        print("\n=== 测量汇总 ===")
        total_area = sum(m.real_area_sqm for m in self.measurements)
        print(f"总计: {len(self.measurements)}个建筑物, {total_area:.2f}平方米 ({total_area/10000:.4f}公顷)")
        for m in self.measurements:
            print(f"  - {m.name}: {m.real_area_sqm:.2f}m | {m.real_area_hectare:.4f}ha | {m.notes}")
    
    def run(self):
        """主循环"""
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, 1200, 800)
        self.reset_display()
        
        print("\n" + "="*50)
        print("  机场建筑物占地面积测量工具")
        print("="*50)
        print("\n操作说明:")
        print("  C - 进入标定模式（先选两个已知距离的点）")
        print("  M - 进入测量模式（框选建筑物）")
        print("  S - 保存结果")
        print("  R - 重置显示")
        print("  Q - 退出程序")
        print("="*50)
        
        while True:
            cv2.imshow(self.window_name, self.display_image)
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q') or key == ord('Q'):
                if self.measurements:
                    save = input("\n有未保存的测量数据，是否保存？(y/n): ").strip().lower()
                    if save == 'y':
                        self.save_results()
                break
                
            elif key == ord('c') or key == ord('C'):
                self.calibration_mode()
                
            elif key == ord('m') or key == ord('M'):
                self.measure_polygon_mode()
                
            elif key == ord('s') or key == ord('S'):
                self.save_results()
                
            elif key == ord('r') or key == ord('R'):
                self.reset_display()
        
        cv2.destroyAllWindows()
        print("\n程序已退出")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python3 airport_measurer.py <图片路径>")
        print("示例: python3 airport_measurer.py airport.png")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    try:
        measurer = AirportMeasurer(image_path)
        measurer.run()
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
