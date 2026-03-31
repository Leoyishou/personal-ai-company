#!/usr/bin/env python3
"""
环境检查脚本 - 检查小红书发布所需的所有配置
"""
import subprocess
import os
import sys

def check_mark(ok):
    return "✅" if ok else "❌"

def check_mcp_service():
    """检查 MCP 服务是否运行"""
    try:
        import requests
        resp = requests.post(
            "http://localhost:18060/mcp",
            json={"jsonrpc": "2.0", "method": "initialize", "params": {
                "protocolVersion": "2024-11-05", "capabilities": {},
                "clientInfo": {"name": "check", "version": "1.0"}
            }, "id": 1},
            headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"},
            timeout=5
        )
        return resp.status_code == 200
    except:
        return False

def check_mcp_configured():
    """检查 MCP 是否已添加到 Claude Code"""
    try:
        result = subprocess.run(["claude", "mcp", "list"], capture_output=True, text=True)
        return "xiaohongshu-mcp" in result.stdout
    except:
        return False

def check_nanobanana_env():
    """检查 nanobanana-draw 的 API Key"""
    env_path = os.path.expanduser("~/.claude/skills/nanobanana-draw/.env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            content = f.read()
            return "OPENROUTER_API_KEY" in content and "sk-or-" in content
    return False

def check_login_status():
    """检查小红书登录状态"""
    try:
        import requests
        session = requests.Session()
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }

        resp = session.post("http://localhost:18060/mcp", json={
            "jsonrpc": "2.0", "method": "initialize",
            "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                      "clientInfo": {"name": "check", "version": "1.0"}},
            "id": 1
        }, headers=headers, timeout=5)

        session_id = resp.headers.get("mcp-session-id")
        if session_id:
            headers["mcp-session-id"] = session_id

        session.post("http://localhost:18060/mcp", json={
            "jsonrpc": "2.0", "method": "notifications/initialized"
        }, headers=headers)

        resp = session.post("http://localhost:18060/mcp", json={
            "jsonrpc": "2.0", "method": "tools/call",
            "params": {"name": "check_login_status", "arguments": {}},
            "id": 2
        }, headers=headers, timeout=10)

        result = resp.json()
        text = result.get("result", {}).get("content", [{}])[0].get("text", "")
        return "已登录" in text
    except:
        return False

def main():
    print("=" * 50)
    print("小红书发布环境检查")
    print("=" * 50)
    print()

    # 1. 检查 MCP 服务
    mcp_running = check_mcp_service()
    print(f"{check_mark(mcp_running)} MCP 服务运行中 (localhost:18060)")
    if not mcp_running:
        print("   → 启动命令: cd xiaohongshu-mcp && go run .")

    # 2. 检查 MCP 配置
    mcp_configured = check_mcp_configured()
    print(f"{check_mark(mcp_configured)} MCP 已添加到 Claude Code")
    if not mcp_configured:
        print("   → 添加命令: claude mcp add --transport http xiaohongshu-mcp http://localhost:18060/mcp")

    # 3. 检查登录状态
    if mcp_running:
        logged_in = check_login_status()
        print(f"{check_mark(logged_in)} 小红书已登录")
        if not logged_in:
            print("   → 登录方式: 在 Claude Code 中调用 get_login_qrcode MCP 工具")
    else:
        print("⏭️  小红书登录状态 (需要先启动 MCP 服务)")

    # 4. 检查 nanobanana API Key
    nanobanana_ok = check_nanobanana_env()
    print(f"{check_mark(nanobanana_ok)} Nanobanana API Key 已配置")
    if not nanobanana_ok:
        print("   → 配置文件: ~/.claude/skills/nanobanana-draw/.env")
        print("   → 需要添加: OPENROUTER_API_KEY=sk-or-xxx")

    print()
    print("=" * 50)

    all_ok = mcp_running and mcp_configured and nanobanana_ok
    if mcp_running:
        all_ok = all_ok and logged_in

    if all_ok:
        print("🎉 所有配置正常，可以开始发布！")
    else:
        print("⚠️  请按上述提示完成配置")

    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
