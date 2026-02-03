"""
图片槽位 - 支持 AI 生图、本地文件、URL、抠图
"""

import os
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, Tuple

from PIL import Image

# 添加父目录到路径，以便导入 nanobanana_client
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from ..core import Slot


@dataclass
class ImageSlot(Slot):
    """图片槽位"""
    name: str = ""
    region: Tuple[float, float, float, float] = (0, 0, 1, 1)
    options: Dict[str, Any] = field(default_factory=dict)

    def render(self, canvas: Image.Image, content: Any, rect: Tuple[int, int, int, int]) -> None:
        """
        渲染图片到画布

        content 格式：
        - {"type": "file", "path": "/path/to/image.png"}
        - {"type": "generate", "prompt": "AI机器人，白色背景"}
        - {"type": "url", "url": "https://..."}
        - 字符串路径（直接当作文件路径）
        """
        # 1. 获取图片
        img = self._get_image(content)
        if img is None:
            return

        # 2. 抠图（可选）
        if self.options.get("bg_remove"):
            img = self._remove_background(img)

        # 3. 适配尺寸
        slot_size = (rect[2] - rect[0], rect[3] - rect[1])
        img = self._fit_image(img, slot_size)

        # 4. 计算居中位置
        x_offset = rect[0] + (slot_size[0] - img.width) // 2
        y_offset = rect[1] + (slot_size[1] - img.height) // 2

        # 5. 粘贴到画布（带透明度）
        if img.mode == 'RGBA':
            canvas.paste(img, (x_offset, y_offset), img)
        else:
            canvas.paste(img, (x_offset, y_offset))

    def _get_image(self, content: Any) -> Image.Image:
        """获取图片（生成/本地/URL）"""
        if isinstance(content, str):
            # 直接是路径
            if os.path.exists(content):
                return Image.open(content).convert('RGBA')
            else:
                print(f"Warning: Image not found: {content}")
                return None

        if isinstance(content, dict):
            content_type = content.get("type", "file")

            if content_type == "file":
                path = content.get("path")
                if path and os.path.exists(path):
                    return Image.open(path).convert('RGBA')
                print(f"Warning: Image not found: {path}")
                return None

            elif content_type == "generate":
                return self._generate_image(content.get("prompt", ""))

            elif content_type == "url":
                return self._fetch_image(content.get("url"))

        return None

    def _generate_image(self, prompt: str) -> Image.Image:
        """使用 Nanobanana 生成图片"""
        try:
            from nanobanana_client import generate_image
            import base64
            from io import BytesIO

            print(f"Generating image: {prompt[:50]}...")
            content, raw = generate_image(prompt=prompt)

            # 从响应中提取图片
            choices = raw.get("choices", [])
            for choice in choices:
                message = choice.get("message", {})
                images = message.get("images", [])

                for img_data in images:
                    b64_data = None
                    if isinstance(img_data, dict):
                        image_url = img_data.get("image_url", {})
                        if isinstance(image_url, dict):
                            url = image_url.get("url", "")
                            if url.startswith("data:"):
                                _, b64_data = url.split(",", 1)
                    elif isinstance(img_data, str) and img_data.startswith("data:"):
                        _, b64_data = img_data.split(",", 1)

                    if b64_data:
                        img_bytes = base64.b64decode(b64_data)
                        return Image.open(BytesIO(img_bytes)).convert('RGBA')

            print("Warning: No image found in generation response")
            return None

        except Exception as e:
            print(f"Error generating image: {e}")
            return None

    def _fetch_image(self, url: str) -> Image.Image:
        """从 URL 获取图片"""
        try:
            import requests
            from io import BytesIO

            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return Image.open(BytesIO(response.content)).convert('RGBA')
        except Exception as e:
            print(f"Error fetching image from URL: {e}")
            return None

    def _remove_background(self, img: Image.Image) -> Image.Image:
        """去除背景"""
        mode = self.options.get("bg_remove_mode", "white")

        if mode == "ai":
            try:
                from rembg import remove
                return remove(img)
            except ImportError:
                print("Warning: rembg not installed, falling back to white mode")
                mode = "white"

        if mode == "white":
            import numpy as np
            from PIL import ImageFilter

            data = np.array(img)
            if data.shape[2] < 4:
                # 添加 alpha 通道
                data = np.dstack([data, np.full(data.shape[:2], 255, dtype=np.uint8)])

            # 计算亮度
            rgb = data[:, :, :3]
            brightness = np.mean(rgb, axis=2)

            threshold = self.options.get("bg_threshold", 245)
            feather = self.options.get("bg_feather", 2)

            # 创建透明度蒙版
            alpha = np.where(brightness > threshold, 0, 255).astype(np.uint8)

            # 边缘羽化
            if feather > 0:
                alpha_img = Image.fromarray(alpha, mode='L')
                alpha_img = alpha_img.filter(ImageFilter.GaussianBlur(feather))
                alpha = np.array(alpha_img)
                alpha = np.clip(alpha * 1.5, 0, 255).astype(np.uint8)

            data[:, :, 3] = alpha
            return Image.fromarray(data)

        return img

    def _fit_image(self, img: Image.Image, target_size: Tuple[int, int]) -> Image.Image:
        """适配图片尺寸"""
        fit_mode = self.options.get("fit", "contain")
        target_w, target_h = target_size
        img_w, img_h = img.size

        if fit_mode == "contain":
            # 保持比例，完整显示
            ratio = min(target_w / img_w, target_h / img_h)
            new_size = (int(img_w * ratio), int(img_h * ratio))
            return img.resize(new_size, Image.Resampling.LANCZOS)

        elif fit_mode == "cover":
            # 保持比例，填满区域（可能裁剪）
            ratio = max(target_w / img_w, target_h / img_h)
            new_size = (int(img_w * ratio), int(img_h * ratio))
            resized = img.resize(new_size, Image.Resampling.LANCZOS)
            # 居中裁剪
            left = (resized.width - target_w) // 2
            top = (resized.height - target_h) // 2
            return resized.crop((left, top, left + target_w, top + target_h))

        elif fit_mode == "fill":
            # 拉伸填满
            return img.resize(target_size, Image.Resampling.LANCZOS)

        return img
