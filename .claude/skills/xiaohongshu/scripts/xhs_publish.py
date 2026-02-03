#!/usr/bin/env python3
"""
小红书发布辅助脚本 - 处理 MCP streamable HTTP 会话
用法:
  python xhs_publish.py check                    # 检查登录状态
  python xhs_publish.py qrcode                   # 获取登录二维码
  python xhs_publish.py publish --title "标题" --content "内容" --tags "标签1,标签2" --images "/path/to/img.jpg"
  python xhs_publish.py video --title "标题" --content "内容" --tags "标签1,标签2" --video "/path/to/video.mp4"
"""
import requests
import json
import base64
import argparse
import sys
import os

MCP_URL = "http://localhost:18060/mcp"

def create_session():
    """创建 MCP 会话"""
    session = requests.Session()
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }

    try:
        resp = session.post(MCP_URL, json={
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "xhs-publish", "version": "1.0.0"}
            },
            "id": 1
        }, headers=headers, timeout=10)

        session_id = resp.headers.get("mcp-session-id")
        if session_id:
            headers["mcp-session-id"] = session_id

        session.post(MCP_URL, json={
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }, headers=headers)

        return session, headers
    except requests.exceptions.ConnectionError:
        print("错误: 无法连接到小红书 MCP 服务")
        print("请确保服务已启动: cd xiaohongshu-mcp && go run .")
        sys.exit(1)

def call_tool(session, headers, tool_name, arguments, msg_id=2):
    """调用 MCP 工具"""
    resp = session.post(MCP_URL, json={
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
        "id": msg_id
    }, headers=headers, timeout=120)

    content_type = resp.headers.get("Content-Type", "")
    if "text/event-stream" in content_type:
        for line in resp.text.split("\n"):
            if line.startswith("data:"):
                data = line[5:].strip()
                if data:
                    return json.loads(data)
    return resp.json()

def check_login():
    """检查登录状态"""
    session, headers = create_session()
    result = call_tool(session, headers, "check_login_status", {})

    content = result.get("result", {}).get("content", [])
    if content:
        text = content[0].get("text", "")
        print(text)
        return "已登录" in text
    return False

def get_qrcode():
    """获取登录二维码"""
    session, headers = create_session()
    result = call_tool(session, headers, "get_login_qrcode", {})

    if "result" in result:
        content = result.get("result", {}).get("content", [])
        for item in content:
            data = None
            if item.get("type") == "image":
                data = item.get("data", "")
            elif item.get("type") == "text":
                text = item.get("text", "")
                if "base64" in text or text.startswith("data:image"):
                    data = text

            if data:
                if "," in data:
                    data = data.split(",")[1]
                qr_path = os.path.join(os.getcwd(), "xiaohongshu_login_qrcode.png")
                with open(qr_path, "wb") as f:
                    f.write(base64.b64decode(data))
                print(f"二维码已保存: {qr_path}")
                print("请用小红书 App 扫码登录（有效期约5分钟）")
                return True

    print("获取二维码失败")
    if "error" in result:
        print(f"错误: {result['error'].get('message', '')}")
    return False

def publish_content(title, content, tags, images):
    """发布图文内容"""
    session, headers = create_session()

    # 先检查登录
    result = call_tool(session, headers, "check_login_status", {})
    login_text = result.get("result", {}).get("content", [{}])[0].get("text", "")
    if "已登录" not in login_text:
        print("错误: 未登录，请先扫码登录")
        return False

    # 发布
    args = {
        "title": title,
        "content": content,
        "images": images
    }
    if tags:
        args["tags"] = tags

    print(f"正在发布...")
    print(f"  标题: {title}")
    print(f"  内容: {content[:50]}...")
    print(f"  标签: {tags}")
    print(f"  图片: {len(images)} 张")

    result = call_tool(session, headers, "publish_content", args, 3)

    if "result" in result:
        text = result.get("result", {}).get("content", [{}])[0].get("text", "")
        print(f"\n{text}")
        return "成功" in text
    else:
        print(f"发布失败: {result.get('error', {}).get('message', '未知错误')}")
        return False

def publish_video(title, content, tags, video):
    """发布视频内容"""
    session, headers = create_session()

    # 先检查登录
    result = call_tool(session, headers, "check_login_status", {})
    login_text = result.get("result", {}).get("content", [{}])[0].get("text", "")
    if "已登录" not in login_text:
        print("错误: 未登录，请先扫码登录")
        return False

    # 发布
    args = {
        "title": title,
        "content": content,
        "video": video
    }
    if tags:
        args["tags"] = tags

    print(f"正在发布视频...")
    print(f"  标题: {title}")
    print(f"  视频: {video}")

    result = call_tool(session, headers, "publish_with_video", args, 3)

    if "result" in result:
        text = result.get("result", {}).get("content", [{}])[0].get("text", "")
        print(f"\n{text}")
        return "成功" in text
    else:
        print(f"发布失败: {result.get('error', {}).get('message', '未知错误')}")
        return False

def main():
    parser = argparse.ArgumentParser(description="小红书发布工具")
    subparsers = parser.add_subparsers(dest="command", help="命令")

    # check 命令
    subparsers.add_parser("check", help="检查登录状态")

    # qrcode 命令
    subparsers.add_parser("qrcode", help="获取登录二维码")

    # publish 命令
    pub_parser = subparsers.add_parser("publish", help="发布图文")
    pub_parser.add_argument("--title", required=True, help="标题（最多20字）")
    pub_parser.add_argument("--content", required=True, help="正文内容")
    pub_parser.add_argument("--tags", help="标签，逗号分隔")
    pub_parser.add_argument("--images", required=True, help="图片路径，逗号分隔")

    # video 命令
    vid_parser = subparsers.add_parser("video", help="发布视频")
    vid_parser.add_argument("--title", required=True, help="标题（最多20字）")
    vid_parser.add_argument("--content", required=True, help="正文内容")
    vid_parser.add_argument("--tags", help="标签，逗号分隔")
    vid_parser.add_argument("--video", required=True, help="视频路径")

    args = parser.parse_args()

    if args.command == "check":
        check_login()
    elif args.command == "qrcode":
        get_qrcode()
    elif args.command == "publish":
        tags = [t.strip() for t in args.tags.split(",")] if args.tags else []
        images = [i.strip() for i in args.images.split(",")]
        publish_content(args.title, args.content, tags, images)
    elif args.command == "video":
        tags = [t.strip() for t in args.tags.split(",")] if args.tags else []
        publish_video(args.title, args.content, tags, args.video)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
