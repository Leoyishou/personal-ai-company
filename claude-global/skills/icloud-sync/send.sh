#!/bin/bash
# iCloud Sync - 发送文件到手机
# 用法: send.sh <文件路径...> [子文件夹名]

ICLOUD_BASE="$HOME/Library/Mobile Documents/com~apple~CloudDocs/Agent Data"

# 检查参数
if [ $# -eq 0 ]; then
    echo "用法: send.sh <文件路径...> [子文件夹名]"
    echo "示例: send.sh photo.jpg"
    echo "示例: send.sh *.png \"项目素材\""
    exit 1
fi

# 获取所有参数
args=("$@")
last_arg="${args[-1]}"

# 判断最后一个参数是文件还是文件夹名
if [ -e "$last_arg" ]; then
    # 最后一个参数是文件，使用默认文件夹
    subfolder="默认"
    files=("$@")
else
    # 最后一个参数是文件夹名
    subfolder="$last_arg"
    files=("${args[@]:0:$#-1}")
fi

# 创建目标目录
target_dir="$ICLOUD_BASE/$subfolder"
mkdir -p "$target_dir"

# 复制文件
count=0
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        cp "$file" "$target_dir/"
        filename=$(basename "$file")
        echo "✓ $filename"
        ((count++))
    fi
done

echo ""
echo "已发送 $count 个文件到: iCloud 云盘/Agent Data/$subfolder/"
echo "在 iPhone「文件」App 中查看"
