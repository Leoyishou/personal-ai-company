#!/bin/bash
# Supabase Local - 启动脚本
# 位置: ~/.claude/services/supabase-local

cd "$(dirname "$0")"

echo "🚀 Starting Supabase Local..."
echo ""
echo "📁 Data Directory: $(pwd)/volumes/db/data"
echo ""

# 检查 Docker
if ! docker info &>/dev/null; then
    echo "❌ Docker not running. Please start OrbStack first."
    exit 1
fi

# 启动服务
docker compose up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# 检查状态
docker compose ps

echo ""
echo "✅ Supabase Local is running!"
echo ""
echo "📊 Dashboard: http://localhost:8000"
echo "   Username: supabase"
echo "   Password: (see .env file)"
echo ""
echo "🔗 API URL:     http://localhost:8000"
echo "🔗 Studio:      http://localhost:54323"
echo "🔗 PostgreSQL:  localhost:5432"
echo ""
