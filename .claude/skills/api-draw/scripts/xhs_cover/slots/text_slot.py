"""
文字槽位 - 支持标题、列表、标签等
"""

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple, Union

from PIL import Image, ImageDraw, ImageFont


# 字体路径（macOS 系统字体）
FONT_PATHS = {
    "regular": [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
    ],
    "bold": [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
    ],
}


def get_font(size: int, weight: str = "regular") -> ImageFont.FreeTypeFont:
    """获取字体"""
    font_list = FONT_PATHS.get(weight, FONT_PATHS["regular"])

    for font_path in font_list:
        if os.path.exists(font_path):
            try:
                # PingFang.ttc 包含多个字体，索引 0 是 Regular，索引 1 是 Medium
                index = 1 if weight == "bold" else 0
                if font_path.endswith(".ttc"):
                    return ImageFont.truetype(font_path, size, index=index)
                return ImageFont.truetype(font_path, size)
            except Exception:
                continue

    # 回退到默认字体
    return ImageFont.load_default()


@dataclass
class TextSlot:
    """文字槽位"""
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
        渲染文字到画布

        content 格式：
        - 字符串：直接渲染
        - 列表：渲染为列表项
        """
        draw = ImageDraw.Draw(canvas)

        font_size = self.options.get("font_size", 48)
        font_weight = self.options.get("font_weight", "regular")
        color = self.options.get("color", "#1a1a1a")
        align = self.options.get("align", "left")
        line_spacing = self.options.get("line_spacing", 1.4)
        bullet_style = self.options.get("bullet_style", None)
        max_lines = self.options.get("max_lines", None)

        font = get_font(font_size, font_weight)

        # 处理列表内容
        if isinstance(content, list):
            text = self._format_list(content, bullet_style)
        else:
            text = str(content)

        # 自动换行
        wrapped_text = self._wrap_text(text, font, rect[2] - rect[0])

        # 限制行数
        if max_lines:
            lines = wrapped_text.split('\n')
            if len(lines) > max_lines:
                lines = lines[:max_lines]
                lines[-1] = lines[-1].rstrip() + "..."
            wrapped_text = '\n'.join(lines)

        # 计算位置
        x, y = self._calc_position(draw, rect, wrapped_text, font, align, line_spacing)

        # 绘制文字（支持多行）
        self._draw_multiline_text(draw, x, y, wrapped_text, font, color, align, line_spacing, rect)

    def _format_list(self, items: List[str], bullet_style: str = None) -> str:
        """格式化列表"""
        if not items:
            return ""

        if bullet_style == "number":
            return '\n'.join(f"{i+1}. {item}" for i, item in enumerate(items))
        elif bullet_style == "dash":
            return '\n'.join(f"- {item}" for item in items)
        elif bullet_style == "dot":
            return '\n'.join(f"• {item}" for item in items)
        else:
            return '\n'.join(items)

    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> str:
        """自动换行"""
        lines = []
        for paragraph in text.split('\n'):
            if not paragraph:
                lines.append('')
                continue

            words = list(paragraph)  # 中文按字符分割
            current_line = ""

            for char in words:
                test_line = current_line + char
                bbox = font.getbbox(test_line)
                width = bbox[2] - bbox[0]

                if width <= max_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = char

            if current_line:
                lines.append(current_line)

        return '\n'.join(lines)

    def _calc_position(
        self,
        draw: ImageDraw.Draw,
        rect: Tuple[int, int, int, int],
        text: str,
        font: ImageFont.FreeTypeFont,
        align: str,
        line_spacing: float
    ) -> Tuple[int, int]:
        """计算文字起始位置"""
        x1, y1, x2, y2 = rect
        slot_width = x2 - x1
        slot_height = y2 - y1

        # 计算文字总高度
        lines = text.split('\n')
        line_height = font.size * line_spacing
        total_height = line_height * len(lines)

        # 垂直居中
        v_align = self.options.get("v_align", "top")
        if v_align == "center":
            y = y1 + (slot_height - total_height) // 2
        elif v_align == "bottom":
            y = y2 - total_height
        else:
            y = y1

        # 水平位置
        if align == "center":
            x = x1 + slot_width // 2
        elif align == "right":
            x = x2
        else:
            x = x1

        return x, y

    def _draw_multiline_text(
        self,
        draw: ImageDraw.Draw,
        x: int,
        y: int,
        text: str,
        font: ImageFont.FreeTypeFont,
        color: str,
        align: str,
        line_spacing: float,
        rect: Tuple[int, int, int, int]
    ) -> None:
        """绘制多行文字"""
        lines = text.split('\n')
        line_height = int(font.size * line_spacing)
        slot_width = rect[2] - rect[0]

        for line in lines:
            if not line:
                y += line_height
                continue

            # 计算行宽
            bbox = font.getbbox(line)
            line_width = bbox[2] - bbox[0]

            # 根据对齐方式调整 x
            if align == "center":
                line_x = x - line_width // 2
            elif align == "right":
                line_x = x - line_width
            else:
                line_x = x

            draw.text((line_x, y), line, font=font, fill=color)
            y += line_height
