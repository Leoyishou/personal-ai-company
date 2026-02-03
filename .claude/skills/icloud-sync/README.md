# iCloud Sync - 发送数据到手机

通过 iCloud Drive 将文件同步到 iPhone/iPad。

## 快速使用

```bash
# 发送单个文件
~/.claude/skills/icloud-sync/send.sh /path/to/file.jpg

# 发送多个文件
~/.claude/skills/icloud-sync/send.sh /path/to/*.png

# 发送到指定子文件夹
~/.claude/skills/icloud-sync/send.sh /path/to/file.jpg "项目名称"
```

## 工作流程

1. 文件会被复制到 `iCloud Drive/Agent Data/[子文件夹]/`
2. iCloud 自动同步到所有设备
3. 在 iPhone 上打开「文件」App → iCloud 云盘 → Agent Data
4. 长按文件 → 保存到相册（如果是图片）

## 目录结构

```
iCloud 云盘/
└── Agent Data/
    ├── 默认/           # 未指定子文件夹时的默认位置
    ├── 大师原典素材/    # 项目专属文件夹
    └── ...
```

## 在 Claude Code 中使用

直接说：
- "把这个图片发到我手机"
- "同步到 iCloud"
- "发送到手机"

Claude 会自动调用此 skill。

## 注意事项

- 确保 Mac 已登录 iCloud 且开启 iCloud Drive
- 大文件同步可能需要几秒到几分钟
- iPhone 需要在同一 iCloud 账号下
