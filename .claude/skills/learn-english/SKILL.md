---
description: YouTube 英语学习增强 - 提取音频，基于个人词汇水平添加生词慢速播放和中文讲解
---

# learn-english

YouTube 视频个性化英语学习增强工具 - 基于用户词汇水平自动识别生词句子，添加慢速播放和中文讲解。

## 核心功能

根据用户在 Supabase 中的词汇数据，对 YouTube 视频进行智能增强：
1. 识别包含生词的句子
2. 该句子慢速播放 (0.7x) 让用户听清
3. 插入中文 TTS 讲解（通俗易懂，让用户瞬间理解整句含义）
4. 原速重播句子加强记忆

## SOP（标准操作流程）

**重要：无论原视频/音频多长，默认只处理前 15 分钟（900 秒）**

### 1. 准备音频和 ASR

如果没有 ASR 结果，先用 api-asr skill 处理：
```bash
# 调用 api-asr skill 获取语音识别结果
```

### 2. 增强处理

```bash
python ~/.claude/skills/learn-english/scripts/enhance_video.py \
    --audio /path/to/source.mp3 \
    --asr /path/to/asr.json \
    --output-dir ~/Library/Mobile\ Documents/com~apple~CloudDocs/practiceEngListen/yyMMdd_描述 \
    --duration 900
```

**重要参数说明：**
- `--output-dir`: 指定输出目录（必须在 `practiceEngListen` 下）
- `--duration`: 默认 900 秒 = 15 分钟

### 3. 输出规范

**必须使用 iCloud practiceEngListen 目录结构：**

```
~/Library/Mobile Documents/com~apple~CloudDocs/practiceEngListen/
├── 260202_gooning/
│   ├── enhanced.mp3      # 增强版音频（用于收听）
│   └── notes.txt         # 学习笔记（可用备忘录打开）
├── 260203_mkbhd_review/
│   ├── enhanced.mp3
│   └── notes.txt
└── ...
```

**目录命名规范：** `yyMMdd_描述`（如 `260202_gooning`）

**notes.txt 格式：**
```
# 260202_gooning 英语学习笔记

原始视频：https://youtube.com/xxx
处理时长：15 分钟

---

## 增强点 1 [00:10 - 00:21]

原文：This is an example sentence with some new words.
整句意思：这是一个包含一些生词的例句。

生词讲解：
- example: 例子，样本
- sentence: 句子

---

## 增强点 2 [00:25 - 00:33]
...
```

## 用户英语水平

- 词汇量：约 14,000 词（CEFR C1 高级）
- 基础词汇：托福 100+ 级别 (13,436 词)
- 额外积累：593 词（不在托福词表中）

**讲解原则：**
- 生词 >= 2 个时，调用 AI 翻译整句含义
- 生词释义要通俗易懂，避免学术化定义
- 结合用户 C1 水平，跳过基础词汇，聚焦真正陌生的词

## 词汇数据来源

从 Supabase AI50 项目查询：
- `vocab_levels` 表：toefl-100 级别词汇（约 13,436 词）
- `user_vocab` 表：用户个人词汇记录

## 增强规则

- 每分钟最多 3-4 个增强点
- 相邻增强间隔 ≥ 10 秒
- 优先增强：2+ 生词的句子 > 首次出现的关键词 > 技术术语

## 增强段落结构

```
[原始音频] → [慢速 0.7x] → [TTS 讲解] → [原速重播] → [继续原音频]
```

## 依赖

- ffmpeg（音频处理）
- supabase-py（数据库查询）
- api-tts skill（TTS 生成）

## 文件结构

```
learn-english/
├── SKILL.md
├── scripts/
│   ├── enhance_video.py    # 主入口
│   ├── asr_processor.py    # ASR 句子提取
│   ├── vocab_matcher.py    # Supabase 词汇匹配
│   ├── audio_mixer.py      # FFmpeg 音频处理
│   └── sync_vocab.py       # 词汇同步脚本
├── cache/
│   ├── vocab_cache.json    # 本地词汇缓存
│   └── sync_meta.json      # 同步元数据
└── data/
    └── definitions.json    # 预置词汇释义
```
