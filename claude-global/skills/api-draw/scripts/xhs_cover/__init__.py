"""
小红书封面模板系统

Remotion 启发：代码定义布局 + AI 填充内容 = 可控稳定 + 创意灵活

用法：
    from xhs_cover import render_template

    cover = render_template(
        template="knowledge",
        content={
            "title": "5个让你效率翻倍的AI工具",
            "main_image": {"type": "generate", "prompt": "AI机器人助手，白色背景"},
            "points": ["ChatGPT", "Claude", "Midjourney"],
            "tags": "#AI工具 #效率提升"
        },
        output="cover.png"
    )
"""

from .renderer import render_template
from .core import Template, Slot

__all__ = ["render_template", "Template", "Slot"]
