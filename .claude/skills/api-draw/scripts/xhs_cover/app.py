#!/usr/bin/env python3
"""
小红书封面生成器 - Gradio 可视化界面

运行：
    cd ~/.claude/skills/api-draw/scripts
    python -m xhs_cover.app

依赖：
    pip install gradio
"""

import os
import sys
from datetime import datetime

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import gradio as gr
from PIL import Image

from xhs_cover.renderer import render_template, list_templates


# ============ 封面生成 ============

def generate_cover(template_name, image, title, subtitle, tags):
    """生成封面"""
    if not template_name:
        return None, "请选择模板"

    content = {}

    # 图片
    if image is not None:
        content["image"] = {"type": "file", "path": image}
        content["main_image"] = {"type": "file", "path": image}

    # 文字
    if title:
        content["title"] = title
    if subtitle:
        content["subtitle"] = subtitle
    if tags:
        content["tags"] = tags

    # 生成
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"/tmp/xhs_cover_{timestamp}.png"

    try:
        render_template(template_name, content, output_path)
        return output_path, f"生成成功: {output_path}"
    except Exception as e:
        return None, f"生成失败: {e}"


# ============ AI 生图 ============

def ai_generate_image(prompt, style):
    """AI 生图"""
    if not prompt:
        return None, "请输入描述"

    try:
        from nanobanana_draw import save_images_from_response
        from nanobanana_client import generate_image

        # 根据风格调整 prompt
        style_prompts = {
            "手绘白板": f"手绘白板风格，简洁线条插画，白色背景，{prompt}",
            "木刻肖像": f"木刻版画风格，黑白线刻肖像，{prompt}",
            "扁平插画": f"扁平矢量插画风格，简洁现代，{prompt}",
            "原始风格": prompt,
        }
        full_prompt = style_prompts.get(style, prompt)

        content, raw = generate_image(prompt=full_prompt)

        # 保存图片
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.expanduser("~/.claude/Nanobanana-draw-图片")
        saved = save_images_from_response(raw, output_dir, style=style, subject="Gradio")

        if saved:
            return saved[0], f"生成成功: {saved[0]}"
        else:
            return None, "生成失败：未找到图片"

    except Exception as e:
        return None, f"生成失败: {e}"


# ============ 抠图 ============

def remove_background(image, mode, threshold):
    """抠图"""
    if image is None:
        return None, "请上传图片"

    try:
        from remove_bg import remove_white_background, remove_background_ai

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"/tmp/nobg_{timestamp}.png"

        if mode == "AI抠图":
            remove_background_ai(image, output_path)
        else:
            remove_white_background(image, output_path, threshold=threshold)

        return output_path, f"抠图成功: {output_path}"

    except Exception as e:
        return None, f"抠图失败: {e}"


# ============ 图片合成 ============

def composite_images(bg_image, fg_image, position, size, padding):
    """图片合成"""
    if bg_image is None or fg_image is None:
        return None, "请上传背景图和前景图"

    try:
        from composite import composite_images as do_composite

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"/tmp/composite_{timestamp}.png"

        do_composite(
            background_path=bg_image,
            foreground_path=fg_image,
            output_path=output_path,
            position=position,
            size=size if size > 0 else None,
            padding=padding,
        )

        return output_path, f"合成成功: {output_path}"

    except Exception as e:
        return None, f"合成失败: {e}"


# ============ 构建界面 ============

def create_app():
    """创建 Gradio 应用"""

    with gr.Blocks(title="小红书封面生成器", theme=gr.themes.Soft()) as app:
        gr.Markdown("# 小红书封面生成器")
        gr.Markdown("整合 AI 生图、抠图、模板合成能力")

        with gr.Tabs():
            # Tab 1: 封面生成
            with gr.Tab("封面生成"):
                with gr.Row():
                    with gr.Column(scale=1):
                        template_dropdown = gr.Dropdown(
                            choices=list_templates(),
                            label="选择模板",
                            value="hero",
                        )
                        cover_image = gr.Image(
                            label="上传图片（可选）",
                            type="filepath",
                        )
                        cover_title = gr.Textbox(label="标题", placeholder="输入标题...")
                        cover_subtitle = gr.Textbox(label="副标题", placeholder="输入副标题...")
                        cover_tags = gr.Textbox(label="标签", placeholder="#标签1 #标签2")
                        cover_btn = gr.Button("生成封面", variant="primary")

                    with gr.Column(scale=1):
                        cover_output = gr.Image(label="生成结果")
                        cover_msg = gr.Textbox(label="状态", interactive=False)

                cover_btn.click(
                    generate_cover,
                    inputs=[template_dropdown, cover_image, cover_title, cover_subtitle, cover_tags],
                    outputs=[cover_output, cover_msg],
                )

            # Tab 2: AI 生图
            with gr.Tab("AI 生图"):
                with gr.Row():
                    with gr.Column(scale=1):
                        ai_prompt = gr.Textbox(
                            label="描述",
                            placeholder="描述你想要的图片...",
                            lines=3,
                        )
                        ai_style = gr.Dropdown(
                            choices=["手绘白板", "木刻肖像", "扁平插画", "原始风格"],
                            label="风格",
                            value="手绘白板",
                        )
                        ai_btn = gr.Button("生成图片", variant="primary")

                    with gr.Column(scale=1):
                        ai_output = gr.Image(label="生成结果")
                        ai_msg = gr.Textbox(label="状态", interactive=False)

                ai_btn.click(
                    ai_generate_image,
                    inputs=[ai_prompt, ai_style],
                    outputs=[ai_output, ai_msg],
                )

            # Tab 3: 抠图
            with gr.Tab("抠图"):
                with gr.Row():
                    with gr.Column(scale=1):
                        bg_input = gr.Image(label="上传图片", type="filepath")
                        bg_mode = gr.Radio(
                            choices=["白底抠图", "AI抠图"],
                            label="抠图模式",
                            value="白底抠图",
                        )
                        bg_threshold = gr.Slider(
                            minimum=200,
                            maximum=255,
                            value=245,
                            step=1,
                            label="白底阈值（仅白底模式）",
                        )
                        bg_btn = gr.Button("开始抠图", variant="primary")

                    with gr.Column(scale=1):
                        bg_output = gr.Image(label="抠图结果")
                        bg_msg = gr.Textbox(label="状态", interactive=False)

                bg_btn.click(
                    remove_background,
                    inputs=[bg_input, bg_mode, bg_threshold],
                    outputs=[bg_output, bg_msg],
                )

            # Tab 4: 图片合成
            with gr.Tab("图片合成"):
                with gr.Row():
                    with gr.Column(scale=1):
                        comp_bg = gr.Image(label="背景图", type="filepath")
                        comp_fg = gr.Image(label="前景图（建议PNG透明）", type="filepath")
                        comp_position = gr.Dropdown(
                            choices=["top-left", "top-right", "bottom-left", "bottom-right", "center"],
                            label="位置",
                            value="top-right",
                        )
                        comp_size = gr.Slider(
                            minimum=0,
                            maximum=500,
                            value=150,
                            step=10,
                            label="前景尺寸（0=原始大小）",
                        )
                        comp_padding = gr.Slider(
                            minimum=0,
                            maximum=100,
                            value=40,
                            step=5,
                            label="边距",
                        )
                        comp_btn = gr.Button("合成图片", variant="primary")

                    with gr.Column(scale=1):
                        comp_output = gr.Image(label="合成结果")
                        comp_msg = gr.Textbox(label="状态", interactive=False)

                comp_btn.click(
                    composite_images,
                    inputs=[comp_bg, comp_fg, comp_position, comp_size, comp_padding],
                    outputs=[comp_output, comp_msg],
                )

        gr.Markdown("---")
        gr.Markdown("生成的图片保存在 `/tmp/` 目录，AI 生图保存在 `~/.claude/Nanobanana-draw-图片/`")

    return app


if __name__ == "__main__":
    import os
    # 禁用代理，避免 Surge 拦截 localhost
    os.environ["no_proxy"] = "localhost,127.0.0.1"
    os.environ["NO_PROXY"] = "localhost,127.0.0.1"

    app = create_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
    )
