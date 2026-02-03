#!/usr/bin/env python3
"""
小红书封面画布 - 后端 API 服务器

运行：
    cd ~/.claude/skills/api-draw/scripts
    python -m xhs_cover.server

端口: 7861

底层统一调用 api-draw 的能力，不重复造轮子。
"""

import base64
import glob
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder=".")
CORS(app)

# 最近生成的封面路径
LAST_COVER_PATH = None

# api-draw 脚本目录
SCRIPTS_DIR = Path(__file__).parent.parent
# 模板目录
TEMPLATES_DIR = SCRIPTS_DIR.parent / "templates"


def load_prompt_template(style: str, user_content: str, target_size: tuple = None) -> str:
    """
    根据风格加载模板并构建完整 prompt。
    模仿 CC 调用 api-draw skill 时的 prompt 构建逻辑。

    Args:
        style: 风格名称
        user_content: 用户输入的描述
        target_size: 目标尺寸 (width, height)，用于在 prompt 中指定
    """
    # 尺寸说明（如果指定了目标尺寸）
    size_hint = ""
    if target_size:
        w, h = target_size
        ratio = f"{w}:{h}"
        # 简化比例
        from math import gcd
        g = gcd(w, h)
        ratio = f"{w//g}:{h//g}"
        size_hint = f"\n图片尺寸要求：{w}×{h}像素，{ratio}比例。"

    # 从模板文件提取核心 prompt 模板
    if style == "手绘白板":
        return f"""生成一张小红书风格封面图，
手绘白板草图风格，视觉笔记美学，
极简线条艺术，粗黑马克笔线条，蓝色高亮点缀，
简单涂鸦图标，流程图结构，箭头连接各元素，
纯白背景，干净专业，商业概念可视化。
{size_hint}

{user_content}

风格：Excalidraw 手绘美学，无阴影，无渐变，无3D效果，略带不规则的草图线条。
VERY simple doodle, NOT realistic, childlike simple sketch, crude imperfect lines,
like drawn with marker on whiteboard, wobbly hand-drawn style."""

    elif style in ("木刻肖像", "线刻肖像"):
        return f"""将这张照片中的人物转换为黑白线刻版画风格，但衣服保留彩色：
- 人物面部用精细的黑白平行线条刻画，木刻版画质感
- 衣服保留鲜艳的彩色，形成视觉焦点
- 背景极简：纯白色或浅米色，干净留白
- 黑白线条人像 + 彩色衣服的对比，吸引眼球
- 整体风格：简约现代的线刻插画
{size_hint}

{user_content}"""

    elif style == "板书插画":
        return f"""生成一张小红书风格封面图，
白板教学插画风格，像老师在白板上讲课，
干净的白色背景，黑色手写字体，
搭配简单的卡通人物或涂鸦图标，
有重点标记（橙色/黄色高亮），
适合财经理财、知识科普、教育课程、技术教程。
{size_hint}

{user_content}"""

    elif style == "学霸笔记":
        return f"""生成一张小红书风格封面图，
学霸笔记风格，方格纸背景，
手写字体配合荧光笔标记，
适合知识图解、原理拆解、错误vs正确对比。
{size_hint}

{user_content}"""

    elif style == "对比漫画":
        return f"""生成一张小红书风格封面图，
上下两格漫画风格，简单线条人物，
适合对比、反差、吐槽、生活感悟。
{size_hint}

{user_content}"""

    else:
        # 原始风格或其他
        if size_hint:
            return f"{user_content}{size_hint}"
        return user_content


@app.route("/")
def index():
    """返回画布 HTML"""
    return send_from_directory(".", "canvas.html")


@app.route("/generate", methods=["POST"])
def generate_image():
    """AI 生图 - 调用 api-draw 的 nanobanana_draw.py"""
    global LAST_COVER_PATH

    data = request.json
    prompt = data.get("prompt", "")
    style = data.get("style", "手绘白板")
    remove_bg = data.get("remove_bg", False)
    ref_image = data.get("ref_image")  # base64 或路径

    if not prompt:
        return jsonify({"success": False, "error": "请输入描述"})

    try:
        # 映射风格名（用于文件命名）
        style_map = {
            "木刻肖像": "线刻肖像",
            "扁平插画": "其他",
        }
        actual_style = style_map.get(style, style)

        # 计算图片槽位的实际尺寸（基于 hero 模板）
        # 画布: 1080 x 1440
        # 图片区域: [0.05, 0.02, 0.95, 0.58]
        canvas_w, canvas_h = 1080, 1440
        region = [0.05, 0.02, 0.95, 0.58]  # hero 模板的图片槽位
        slot_w = int((region[2] - region[0]) * canvas_w)  # 972
        slot_h = int((region[3] - region[1]) * canvas_h)  # 806

        # 使用模板构建完整 prompt（核心！）
        full_prompt = load_prompt_template(style, prompt, target_size=(slot_w, slot_h))

        # 处理参考图片（base64 -> 临时文件）
        ref_image_path = None
        if ref_image:
            if ref_image.startswith("data:"):
                # base64 图片，保存到临时文件
                header, encoded = ref_image.split(",", 1)
                img_data = base64.b64decode(encoded)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                ref_image_path = f"/tmp/ref_image_{timestamp}.png"
                with open(ref_image_path, "wb") as f:
                    f.write(img_data)
            elif os.path.exists(ref_image):
                ref_image_path = ref_image

        # 构建命令
        cmd = [
            sys.executable,
            str(SCRIPTS_DIR / "nanobanana_draw.py"),
            full_prompt,  # 传完整 prompt，不是用户输入的简单描述
            "--style", actual_style,
            "--subject", "Canvas",
        ]

        # 如果有参考图片（线刻肖像等需要）
        if ref_image_path:
            cmd.extend(["--image", ref_image_path])

        # 执行生图脚本
        env = os.environ.copy()
        result = subprocess.run(
            cmd,
            cwd=str(SCRIPTS_DIR),
            capture_output=True,
            text=True,
            env=env,
            timeout=120,
        )

        if result.returncode != 0:
            return jsonify({
                "success": False,
                "error": f"生图失败: {result.stderr}"
            })

        # 找到最新生成的图片
        output_dir = os.path.expanduser("~/.claude/Nanobanana-draw-图片")
        pattern = os.path.join(output_dir, f"*{actual_style}*Canvas*.png")
        files = glob.glob(pattern)
        if not files:
            # 尝试更宽松的匹配
            pattern = os.path.join(output_dir, "*.png")
            files = glob.glob(pattern)

        if not files:
            return jsonify({"success": False, "error": "未找到生成的图片"})

        # 取最新的文件
        image_path = max(files, key=os.path.getctime)

        # 抠图（可选）
        if remove_bg:
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                nobg_path = f"/tmp/nobg_{timestamp}.png"

                # 调用 remove_bg.py
                subprocess.run([
                    sys.executable,
                    str(SCRIPTS_DIR / "remove_bg.py"),
                    image_path,
                    "-o", nobg_path,
                ], cwd=str(SCRIPTS_DIR), check=True)

                if os.path.exists(nobg_path):
                    image_path = nobg_path
            except Exception as e:
                print(f"抠图失败: {e}")

        # 返回 base64 图片供前端显示
        with open(image_path, "rb") as f:
            img_data = base64.b64encode(f.read()).decode("utf-8")

        return jsonify({
            "success": True,
            "image_path": image_path,
            "image_url": f"data:image/png;base64,{img_data}",
        })

    except subprocess.TimeoutExpired:
        return jsonify({"success": False, "error": "生图超时"})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)})


@app.route("/render", methods=["POST"])
def render_cover():
    """渲染封面"""
    global LAST_COVER_PATH

    data = request.json
    template = data.get("template", "hero")
    image = data.get("image")  # 可能是路径或 base64
    title = data.get("title", "")
    subtitle = data.get("subtitle", "")
    tags = data.get("tags", "")

    if not title:
        return jsonify({"success": False, "error": "请输入标题"})

    try:
        from xhs_cover.renderer import render_template

        # 构建内容
        content = {
            "title": title,
        }

        if subtitle:
            content["subtitle"] = subtitle
        if tags:
            content["tags"] = tags

        # 处理图片
        if image:
            if image.startswith("data:"):
                # base64 图片，需要先保存
                header, encoded = image.split(",", 1)
                img_data = base64.b64decode(encoded)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                temp_path = f"/tmp/canvas_img_{timestamp}.png"
                with open(temp_path, "wb") as f:
                    f.write(img_data)
                content["image"] = {"type": "file", "path": temp_path}
            else:
                # 文件路径
                content["image"] = {"type": "file", "path": image}

        # 生成封面
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"/tmp/xhs_cover_{timestamp}.png"

        render_template(template, content, output_path)
        LAST_COVER_PATH = output_path

        # 返回预览
        with open(output_path, "rb") as f:
            img_data = base64.b64encode(f.read()).decode("utf-8")

        return jsonify({
            "success": True,
            "output": output_path,
            "preview_url": f"data:image/png;base64,{img_data}",
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)})


@app.route("/export", methods=["POST"])
def export_cover():
    """导出封面"""
    global LAST_COVER_PATH

    data = request.json
    destination = data.get("destination", "~/Desktop/xhs_cover.png")
    destination = os.path.expanduser(destination)

    if not LAST_COVER_PATH or not os.path.exists(LAST_COVER_PATH):
        return jsonify({"success": False, "error": "没有可导出的封面"})

    try:
        shutil.copy(LAST_COVER_PATH, destination)
        return jsonify({
            "success": True,
            "path": destination,
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/preview/<path:filename>")
def preview_file(filename):
    """预览图片文件"""
    return send_file(filename)


if __name__ == "__main__":
    print("小红书封面画布服务器")
    print("打开浏览器访问: http://localhost:7861")
    app.run(host="0.0.0.0", port=7861, debug=True)
