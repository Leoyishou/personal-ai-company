# 贴纸库 (Sticker Library)

视频制作中可复用的贴纸素材库。

## 目录结构

```
stickers/
├── brands/           # 品牌 Logo 贴纸
│   ├── ai/          # AI 公司/产品
│   ├── apps/        # 常用 App
│   └── tech/        # 科技公司
├── concepts/         # 概念类贴纸（如：大C端、食之无味）
├── icons/           # 通用图标
└── text/            # 纯文字贴纸
```

## 命名规范

**格式：** `{英文名}.png`

- 全部小写
- 多词用下划线 `_` 连接
- 必须是透明背景 PNG
- 建议尺寸：400x400px 或更大

**示例：**
- `doubao.png` - 豆包
- `qq_music.png` - QQ音乐
- `call_center.png` - 外呼客服

## 当前素材

### brands/ai/ - AI 品牌
| 文件名 | 中文名 | 描述 |
|--------|--------|------|
| doubao.png | 豆包 | 字节跳动 AI 助手 |
| qwen.png | 千问 | 阿里通义千问 |
| gemini.png | Gemini | Google AI |
| anthropic.png | Anthropic | Claude 母公司 |
| openai.png | OpenAI | GPT 系列 |
| lingguang.png | 灵光 | 蚂蚁集团 AI |

### brands/apps/ - 常用 App
| 文件名 | 中文名 |
|--------|--------|
| qq_music.png | QQ音乐 |

### concepts/ - 概念类
| 文件名 | 中文名 | 适用场景 |
|--------|--------|----------|
| c_end.png | 大C端 | 消费级产品 |
| call_center.png | 外呼客服 | 客服/呼叫中心 |
| exploration.png | 纯探索 | 创新/实验性产品 |
| chicken_rib.png | 食之无味 | 鸡肋产品 |

## 使用方式

### 1. 直接引用路径

```bash
STICKER_LIB="$HOME/.claude/agents/content-pr-department/assets/stickers"
# 使用豆包贴纸
ffmpeg -i video.mp4 -i "$STICKER_LIB/brands/ai/doubao.png" ...
```

### 2. 在 video-maker skill 中使用

贴纸会根据 ASR 关键词自动匹配并叠加到视频。

## 新增贴纸流程

1. 使用 draw skill 生成贴纸
2. 使用 remove-bg skill 去除背景
3. 按命名规范存入对应目录
4. 更新本文档的素材列表

## 音效配套

贴纸出现时的配套音效：
```
~/.claude/agents/content-pr-department/assets/audio/sfx/pop.mp3
```
