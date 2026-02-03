"""
形状槽位 - 支持圆形边框、分隔线等装饰性元素
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Tuple

from PIL import Image, ImageDraw


@dataclass
class ShapeSlot:
    """形状槽位"""
    name: str = ""
    region: Tuple[float, float, float, float] = (0, 0, 1, 1)
    options: Dict[str, Any] = field(default_factory=dict)

    def get_rect(self, canvas_size: Tuple[int, int]) -> Tuple[int, int, int, int]:
        """计算实际像素坐标"""
        w, h = canvas_size
        x1, y1, x2, y2 = self.region
        return (int(x1 * w), int(y1 * h), int(x2 * w), int(y2 * h))

    def render(self, canvas: Image.Image, content: Any, rect: Tuple[int, int, int, int]) -> None:
        """
        渲染形状到画布

        content 格式：
        - {"shape": "circle", ...}
        - {"shape": "line", ...}
        - {"shape": "rect", ...}
        """
        if not isinstance(content, dict):
            content = {}

        shape = content.get("shape", self.options.get("shape", "rect"))
        color = content.get("color", self.options.get("color", "#333333"))
        stroke_width = content.get("stroke_width", self.options.get("stroke_width", 3))
        fill = content.get("fill", self.options.get("fill", None))

        draw = ImageDraw.Draw(canvas)

        if shape == "circle":
            self._draw_circle(draw, rect, color, stroke_width, fill)
        elif shape == "line":
            self._draw_line(draw, rect, color, stroke_width)
        elif shape == "rect":
            self._draw_rect(draw, rect, color, stroke_width, fill)
        elif shape == "handdrawn_circle":
            self._draw_handdrawn_circle(canvas, rect, color, stroke_width)

    def _draw_circle(
        self,
        draw: ImageDraw.Draw,
        rect: Tuple[int, int, int, int],
        color: str,
        stroke_width: int,
        fill: str = None
    ) -> None:
        """绘制圆形"""
        x1, y1, x2, y2 = rect
        # 确保是正圆
        size = min(x2 - x1, y2 - y1)
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        half = size // 2

        draw.ellipse(
            [cx - half, cy - half, cx + half, cy + half],
            outline=color,
            width=stroke_width,
            fill=fill
        )

    def _draw_line(
        self,
        draw: ImageDraw.Draw,
        rect: Tuple[int, int, int, int],
        color: str,
        stroke_width: int
    ) -> None:
        """绘制线条"""
        x1, y1, x2, y2 = rect
        # 默认画水平线
        cy = (y1 + y2) // 2
        draw.line([(x1, cy), (x2, cy)], fill=color, width=stroke_width)

    def _draw_rect(
        self,
        draw: ImageDraw.Draw,
        rect: Tuple[int, int, int, int],
        color: str,
        stroke_width: int,
        fill: str = None
    ) -> None:
        """绘制矩形"""
        draw.rectangle(rect, outline=color, width=stroke_width, fill=fill)

    def _draw_handdrawn_circle(
        self,
        canvas: Image.Image,
        rect: Tuple[int, int, int, int],
        color: str,
        stroke_width: int
    ) -> None:
        """绘制手绘风格圆形边框"""
        import math
        import random

        draw = ImageDraw.Draw(canvas)

        x1, y1, x2, y2 = rect
        size = min(x2 - x1, y2 - y1)
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        radius = size // 2 - stroke_width

        # 生成手绘效果的点
        points = []
        num_points = 100

        for i in range(num_points + 1):
            angle = 2 * math.pi * i / num_points
            # 添加随机扰动
            r_offset = random.uniform(-radius * 0.02, radius * 0.02)
            x = cx + (radius + r_offset) * math.cos(angle)
            y = cy + (radius + r_offset) * math.sin(angle)
            points.append((x, y))

        # 绘制手绘线条
        for i in range(len(points) - 1):
            # 随机线宽变化
            width = stroke_width + random.randint(-1, 1)
            width = max(1, width)
            draw.line([points[i], points[i + 1]], fill=color, width=width)
