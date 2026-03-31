#!/bin/bash
# 极速视频发布 - 启动脚本

cd "$(dirname "$0")"

# 杀掉旧进程
lsof -ti :3456 | xargs kill -9 2>/dev/null

# 获取本机 IP
IP=$(ipconfig getifaddr en0 2>/dev/null || echo "localhost")

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║              极速视频发布 - Instant Publisher              ║"
echo "╠═══════════════════════════════════════════════════════════╣"
echo "║                                                           ║"
echo "║  电脑访问: http://localhost:3456                          ║"
echo "║  手机访问: http://$IP:3456                        ║"
echo "║                                                           ║"
echo "║  使用方法:                                                ║"
echo "║  1. 手机浏览器打开上面的地址                              ║"
echo "║  2. 点击「添加到主屏幕」变成 App                          ║"
echo "║  3. 输入标题 → 点击录制 → 点击结束 → 自动发布             ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# 启动服务
bun run start
