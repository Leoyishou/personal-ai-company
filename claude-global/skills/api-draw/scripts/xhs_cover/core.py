"""
核心基类定义：Template, Slot
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class Slot(ABC):
    """槽位基类"""
    name: str
    region: Tuple[float, float, float, float]  # (x1, y1, x2, y2) 比例 0-1
    options: Dict[str, Any] = field(default_factory=dict)

    def get_rect(self, canvas_size: Tuple[int, int]) -> Tuple[int, int, int, int]:
        """计算实际像素坐标"""
        w, h = canvas_size
        x1, y1, x2, y2 = self.region
        return (int(x1 * w), int(y1 * h), int(x2 * w), int(y2 * h))

    def get_size(self, canvas_size: Tuple[int, int]) -> Tuple[int, int]:
        """计算槽位尺寸"""
        rect = self.get_rect(canvas_size)
        return (rect[2] - rect[0], rect[3] - rect[1])

    @abstractmethod
    def render(self, canvas, content: Any, rect: Tuple[int, int, int, int]) -> None:
        """渲染到画布（子类实现）"""
        pass


@dataclass
class Template:
    """模板基类"""
    name: str
    size: Tuple[int, int]
    bg_color: str
    slots: List[Slot]

    def validate_content(self, content: Dict[str, Any]) -> bool:
        """验证内容是否包含所有必需的槽位"""
        slot_names = {slot.name for slot in self.slots}
        content_keys = set(content.keys())
        missing = slot_names - content_keys
        if missing:
            print(f"Warning: Missing content for slots: {missing}")
        return True


def create_slot(slot_config: Dict[str, Any]) -> Slot:
    """工厂方法：根据配置创建对应类型的 Slot"""
    from .slots import ImageSlot, TextSlot, ShapeSlot

    slot_type = slot_config.get("type")
    name = slot_config.get("name")
    region = tuple(slot_config.get("region", [0, 0, 1, 1]))
    options = slot_config.get("options", {})

    if slot_type == "image":
        return ImageSlot(name=name, region=region, options=options)
    elif slot_type == "text":
        return TextSlot(name=name, region=region, options=options)
    elif slot_type == "shape":
        return ShapeSlot(name=name, region=region, options=options)
    else:
        raise ValueError(f"Unknown slot type: {slot_type}")


def load_template(template_name: str) -> Template:
    """从 JSON 文件加载模板"""
    import json
    import os

    templates_dir = os.path.join(os.path.dirname(__file__), "templates")
    template_path = os.path.join(templates_dir, f"{template_name}.json")

    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template not found: {template_path}")

    with open(template_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    slots = [create_slot(s) for s in config.get("slots", [])]

    return Template(
        name=config.get("name", template_name),
        size=tuple(config.get("size", [1080, 1440])),
        bg_color=config.get("bg_color", "#FFFFFF"),
        slots=slots,
    )
