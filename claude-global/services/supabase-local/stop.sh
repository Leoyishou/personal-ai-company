#!/bin/bash
# Supabase Local - 停止脚本

cd "$(dirname "$0")"

echo "🛑 Stopping Supabase Local..."
docker compose down

echo "✅ Supabase Local stopped."
echo "📁 Data is preserved in: $(pwd)/volumes/"
