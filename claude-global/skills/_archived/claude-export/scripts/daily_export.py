#!/usr/bin/env python3
"""
Claude Code 聊天记录每日导出脚本
每天导出当天的所有会话到指定目录
"""
import json
import os
import re
from datetime import datetime, date, timezone, timedelta
from pathlib import Path

# 配置
CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects"
OUTPUT_DIR = Path("/Users/liuyishou/usr/projects/odyssey/src/0 收集箱/Agent")
KNOWLEDGE_BASE_DIR = Path("/Users/liuyishou/usr/projects/odyssey/src")
# 北京时区 UTC+8
BEIJING_TZ = timezone(timedelta(hours=8))

# 技术/概念关键词模式（用于提取）
CONCEPT_PATTERNS = [
    # 英文技术词汇（大写开头或全大写）
    r'\b[A-Z][a-zA-Z]{2,}(?:\s+[A-Z][a-zA-Z]+)*\b',  # CamelCase words
    r'\b[A-Z]{2,}[a-z]*\b',  # Acronyms like API, MCP, LLM
    # 中文技术概念
    r'[\u4e00-\u9fa5]{2,}(?:框架|模型|算法|系统|工具|协议|服务|架构|模式|引擎|技术|方法|策略|机制)',
]


def build_knowledge_index() -> set:
    """从知识库文件名构建已有知识索引"""
    knowledge_set = set()

    if not KNOWLEDGE_BASE_DIR.exists():
        return knowledge_set

    # 排除的目录
    exclude_dirs = {'.git', '.obsidian', 'node_modules', '.trash', '0 收集箱'}

    for md_file in KNOWLEDGE_BASE_DIR.rglob("*.md"):
        # 跳过排除目录
        if any(ex in str(md_file) for ex in exclude_dirs):
            continue

        # 提取文件名（不含扩展名）作为概念
        name = md_file.stem

        # 跳过日期格式的文件（周报、日报等）
        if re.match(r'^\d{4}年第\d+周$', name) or re.match(r'^\d{4}-\d{2}-\d{2}', name):
            continue

        # 清理文件名，提取关键词
        # 移除前缀数字和特殊字符
        clean_name = re.sub(r'^[\d\.\s\$@]+', '', name)
        if clean_name:
            knowledge_set.add(clean_name.lower())

            # 也添加英文部分（如果有）
            english_parts = re.findall(r'[A-Za-z][A-Za-z0-9]+', clean_name)
            for part in english_parts:
                if len(part) >= 2:
                    knowledge_set.add(part.lower())

    return knowledge_set


def extract_concepts_from_text(text: str) -> set:
    """从文本中提取技术概念/关键词"""
    concepts = set()

    if not text:
        return concepts

    # 常用词过滤列表
    common_words = {
        'the', 'and', 'for', 'you', 'are', 'this', 'that', 'with', 'have', 'has',
        'was', 'were', 'been', 'being', 'will', 'would', 'could', 'should', 'may',
        'might', 'must', 'can', 'not', 'but', 'from', 'they', 'them', 'their',
        'what', 'which', 'who', 'whom', 'when', 'where', 'why', 'how', 'all',
        'each', 'every', 'both', 'few', 'more', 'most', 'other', 'some', 'such',
        'only', 'own', 'same', 'than', 'too', 'very', 'just', 'also', 'now',
        'here', 'there', 'then', 'once', 'done', 'make', 'made', 'get', 'got',
        'let', 'put', 'say', 'said', 'see', 'saw', 'seen', 'take', 'took',
        'come', 'came', 'want', 'use', 'used', 'using', 'new', 'first', 'last',
        'long', 'great', 'little', 'own', 'old', 'right', 'big', 'high', 'small',
        'large', 'next', 'early', 'young', 'important', 'public', 'bad', 'good',
        'yes', 'no', 'ok', 'okay', 'please', 'thanks', 'thank', 'sorry', 'hello',
        'hi', 'hey', 'well', 'sure', 'yeah', 'yep', 'nope', 'oh', 'um', 'uh',
        'do', 'did', 'does', 'doing', 'if', 'as', 'at', 'by', 'in', 'on', 'to',
        'up', 'so', 'it', 'its', 'be', 'we', 'he', 'she', 'or', 'an', 'my', 'your',
        'his', 'her', 'our', 'us', 'me', 'him', 'out', 'into', 'about', 'after',
    }

    # 提取英文技术词汇
    # CamelCase 或 PascalCase（如 LaunchAgent, OpenRouter）
    camel_words = re.findall(r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b', text)
    for w in camel_words:
        if w.lower() not in common_words:
            concepts.add(w)  # 保留原始大小写

    # 全大写缩写词（2-6个字母，常见技术缩写）
    acronyms = re.findall(r'\b[A-Z]{2,6}\b', text)
    for a in acronyms:
        if a.lower() not in common_words and len(a) >= 2:
            concepts.add(a)

    # 特定技术词汇模式
    tech_patterns = [
        r'\b[A-Z][a-z]+(?:JS|DB|ML|AI|UI|UX|IO|OS|VM|IP|ID)\b',  # ReactJS, MongoDB等
        r'\b(?:Open|Cloud|Data|Web|App|Auto|Multi|Pre|Post|Re)[A-Z][a-z]+\b',  # OpenAI, CloudFlare等
    ]
    for pattern in tech_patterns:
        matches = re.findall(pattern, text)
        concepts.update(matches)

    # 明确的技术词汇（小写匹配）
    tech_words = re.findall(r'\b(?:launchagent|launchd|crontab|plist|homebrew|raycast|obsidian|notion|roam|logseq|anki|telegram|discord|slack|webhook|cron|daemon|systemd|xpath|regex|glob|grep|sed|awk|vim|emacs|vscode|cursor|windsurf|copilot|tabnine|firecrawl|openrouter|replicate|huggingface|gradio|streamlit|chainlit|flowise|n8n|zapier|make|ifttt|airtable|supabase|firebase|prisma|drizzle|sqlalchemy|typeorm|sequelize|mongoose|graphene|strawberry|pydantic|marshmallow|celery|dramatiq|temporal|airflow|dagster|prefect|mlflow|wandb|dvc|optuna|ray|dask|polars|pandas|numpy|scipy|scikit|pytorch|tensorflow|keras|jax|flax|transformers|diffusers|accelerate|deepspeed|megatron|nemo|triton)\b', text.lower())
    concepts.update(w for w in tech_words)

    # 中文技术概念：使用白名单模式，只匹配明确的技术术语
    chinese_tech_terms = [
        # AI/ML 相关
        '知识图谱', '向量数据库', '提示词', '思维链', '智能体', '大语言模型', '大模型', '小模型',
        '微调', '蒸馏', '量化', '剪枝', '推理引擎', '训练框架', '预训练', '对齐', '强化学习',
        '监督学习', '无监督学习', '半监督学习', '自监督学习', '迁移学习', '元学习', '联邦学习',
        '多模态', '跨模态', '多轮对话', '上下文窗口', '注意力机制', '自注意力', '交叉注意力',
        '位置编码', '词向量', '词嵌入', '分词器', '标记器', '嵌入模型', '向量检索', '语义搜索',
        # 系统/架构
        '定时任务', '后台服务', '守护进程', '消息推送', '数据管道', '工作流引擎', '任务调度',
        '批处理', '流处理', '实时计算', '离线计算', '增量更新', '全量同步', '热更新', '冷启动',
        '缓存穿透', '缓存雪崩', '缓存击穿', '读写分离', '分库分表', '主从复制', '负载均衡',
        '服务网格', '服务发现', '配置中心', '注册中心', '网关', '中间件', '消息队列', '事件驱动',
        # 开发/工具
        '版本控制', '持续集成', '持续部署', '自动化测试', '单元测试', '集成测试', '端到端测试',
        '代码审查', '代码重构', '技术债务', '设计模式', '架构模式', '领域驱动', '事件溯源',
        '命令行工具', '脚手架', '包管理器', '构建工具', '打包工具', '代码生成', '低代码', '无代码',
        # 产品/运营
        '用户画像', '漏斗分析', '留存分析', '转化率', 'A/B测试', '灰度发布', '特性开关',
        '埋点', '数据埋点', '行为分析', '热力图', '用户旅程', '增长黑客', '病毒传播',
        # 内容/创作
        '视觉策略', '内容策略', '分发策略', '推荐算法', '个性化推荐', '协同过滤', '内容理解',
        '图文生成', '视频生成', '语音合成', '语音识别', '图像识别', '目标检测', '图像分割',
    ]

    for term in chinese_tech_terms:
        if term in text:
            concepts.add(term)

    # 过滤
    filtered = set()
    for c in concepts:
        # 过滤太短或太长的
        if len(c) < 2 or len(c) > 25:
            continue
        # 过滤纯数字
        if c.isdigit():
            continue
        # 过滤常用词
        if c.lower() in common_words:
            continue
        filtered.add(c)

    return filtered


def find_knowledge_gaps(sessions_data: list, knowledge_index: set) -> list:
    """找出今日会话中涉及但不在知识库中的概念"""
    all_concepts = set()

    for session in sessions_data:
        # 从摘要提取
        if session.get("summary"):
            all_concepts.update(extract_concepts_from_text(session["summary"]))

        # 从用户消息提取（只看前几条，避免太多噪音）
        messages = session.get("messages", [])
        user_msgs = [m["content"] for m in messages if m["role"] == "user"][:5]
        for msg in user_msgs:
            if isinstance(msg, str):
                all_concepts.update(extract_concepts_from_text(msg))

    # 找出不在知识库中的概念
    gaps = []
    for concept in all_concepts:
        # 检查是否已存在（忽略大小写）
        if concept.lower() not in knowledge_index:
            # 额外过滤：中文概念必须看起来像技术术语
            if not concept[0].isascii():
                # 中文概念：必须 2-8 字，且不含常见动词/代词开头
                if len(concept) < 2 or len(concept) > 8:
                    continue
                # 过滤以常见非技术词开头的
                skip_prefixes = ['我', '你', '他', '她', '它', '这', '那', '哪', '什', '怎', '为', '是', '有', '在', '的', '了', '和', '与', '或', '但', '如', '被', '把', '让', '给', '帮', '请', '想', '要', '能', '会', '可', '应', '该', '需', '看', '做', '写', '用', '去', '来', '到', '说', '问', '答']
                if any(concept.startswith(p) for p in skip_prefixes):
                    continue
            gaps.append(concept)

    # 按字母排序，优先显示英文
    gaps.sort(key=lambda x: (not x[0].isascii(), x.lower()))

    return gaps[:30]  # 最多返回30个


def get_today_sessions():
    """获取今天修改过的所有会话文件"""
    today = date.today()
    sessions = []

    if not CLAUDE_PROJECTS_DIR.exists():
        print(f"❌ Claude projects 目录不存在: {CLAUDE_PROJECTS_DIR}")
        return sessions

    # 遍历所有项目目录
    for project_dir in CLAUDE_PROJECTS_DIR.iterdir():
        if not project_dir.is_dir():
            continue

        # 查找所有 .jsonl 文件
        for jsonl_file in project_dir.glob("*.jsonl"):
            # 检查文件修改时间是否是今天
            mtime = datetime.fromtimestamp(jsonl_file.stat().st_mtime)
            if mtime.date() == today:
                sessions.append({
                    "path": jsonl_file,
                    "project": project_dir.name,
                    "mtime": mtime,
                    "size": jsonl_file.stat().st_size
                })

    return sorted(sessions, key=lambda x: x["mtime"])


def parse_session(jsonl_path: Path) -> dict:
    """解析会话文件，提取关键信息"""
    messages = []
    session_info = {
        "id": jsonl_path.stem,
        "messages": [],
        "summary": None,
        "start_time": None,
        "end_time": None
    }

    try:
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)

                    # 提取时间戳
                    if "timestamp" in entry:
                        ts = datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00"))
                        if session_info["start_time"] is None:
                            session_info["start_time"] = ts
                        session_info["end_time"] = ts

                    # 提取消息（全量保留）
                    if entry.get("type") == "user":
                        content = entry.get("message", {})
                        if isinstance(content, dict):
                            text = content.get("content", "")
                        else:
                            text = str(content)
                        if text:
                            messages.append({"role": "user", "content": text})

                    elif entry.get("type") == "assistant":
                        content = entry.get("message", {})
                        if isinstance(content, dict):
                            # 提取文本内容
                            content_blocks = content.get("content", [])
                            text_parts = []
                            for block in content_blocks:
                                if isinstance(block, dict) and block.get("type") == "text":
                                    text_parts.append(block.get("text", ""))
                            text = "\n".join(text_parts)
                        else:
                            text = str(content)
                        if text:
                            messages.append({"role": "assistant", "content": text})

                    # 提取摘要
                    elif entry.get("type") == "summary":
                        session_info["summary"] = entry.get("summary", "")

                except json.JSONDecodeError:
                    continue

    except Exception as e:
        print(f"⚠️ 解析失败 {jsonl_path}: {e}")

    session_info["messages"] = messages
    return session_info


def format_session_markdown(session_info: dict, project_name: str) -> str:
    """将会话格式化为 Markdown"""
    lines = []

    # 标题
    session_id = session_info["id"][:8]
    if session_info["start_time"]:
        time_str = session_info["start_time"].astimezone(BEIJING_TZ).strftime("%H:%M")
        lines.append(f"## 会话 {session_id} ({time_str})")
    else:
        lines.append(f"## 会话 {session_id}")

    lines.append("")

    # 项目路径
    # 解码项目路径
    decoded_project = project_name.replace("-", "/").lstrip("/")
    lines.append(f"**项目**: `{decoded_project}`")
    lines.append("")

    # 摘要（如果有，全量保留）
    if session_info.get("summary"):
        lines.append("### 摘要")
        lines.append(session_info["summary"])
        lines.append("")

    # 对话内容（精简版）
    lines.append("### 对话记录")
    lines.append("")

    for msg in session_info["messages"]:
        role = "👤 用户" if msg["role"] == "user" else "🤖 Claude"
        raw_content = msg["content"]
        if isinstance(raw_content, list):
            raw_content = " ".join(str(x) for x in raw_content)
        elif not isinstance(raw_content, str):
            raw_content = str(raw_content)
        # 保留完整内容，只替换换行符为段落
        content = raw_content.strip()
        lines.append(f"**{role}**: {content}")
        lines.append("")

    if not session_info["messages"]:
        lines.append("*无对话内容*")
        lines.append("")

    lines.append("---")
    lines.append("")

    return "\n".join(lines)


def categorize_work(summaries: list) -> dict:
    """根据关键词分类工作类型"""
    categories = {
        "图片生成": [],
        "社交媒体发布": [],
        "自动化任务": [],
        "工具配置": [],
        "代码开发": [],
        "其他": []
    }

    keywords = {
        "图片生成": ["肖像", "画", "图片", "封面", "漫画", "白板", "设计", "portrait", "image", "draw"],
        "社交媒体发布": ["小红书", "XHS", "Twitter", "推特", "发布", "publish", "X "],
        "自动化任务": ["定时", "自动", "cron", "LaunchAgent", "监控", "总结", "导出"],
        "工具配置": ["配置", "MCP", "Raycast", "脚本", "script", "setup", "Hook"],
        "代码开发": ["代码", "开发", "bug", "fix", "实现", "implement", "功能"]
    }

    for summary in summaries:
        if not summary:
            continue
        matched = False
        for category, kws in keywords.items():
            for kw in kws:
                if kw.lower() in summary.lower():
                    if summary not in categories[category]:
                        categories[category].append(summary)
                    matched = True
                    break
            if matched:
                break
        if not matched:
            categories["其他"].append(summary)

    return {k: v for k, v in categories.items() if v}


def generate_topic_summary(sessions_data: list, today_str: str, knowledge_gaps: list = None) -> str:
    """生成话题总结"""
    lines = [
        "---",
        f"date: {today_str}",
        "type: daily-summary",
        f"sessions: {len(sessions_data)}",
        "---",
        "",
        f"# {today_str} Claude Code 话题总结",
        "",
        f"共 **{len(sessions_data)} 个会话**",
        "",
        "| 时间 | 话题 |",
        "|------|------|",
    ]

    summaries = []
    for s in sorted(sessions_data, key=lambda x: x["time"] or "99:99"):
        time_str = s["time"] if s["time"] else "—"
        summary = s["summary"] if s["summary"] else "*(无摘要)*"
        lines.append(f"| {time_str} | **{summary}** |")
        if s["summary"]:
            summaries.append(s["summary"])

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 主要工作类型")
    lines.append("")

    # 分类工作
    categories = categorize_work(summaries)

    icons = {
        "图片生成": "🎨",
        "社交媒体发布": "📱",
        "自动化任务": "⚙️",
        "工具配置": "🔧",
        "代码开发": "💻",
        "其他": "📝"
    }

    for category, items in categories.items():
        icon = icons.get(category, "📌")
        # 提取关键词
        keywords = []
        for item in items[:3]:  # 最多取3个
            # 简化摘要为关键词
            words = item.replace("&", "、").split("、")
            for w in words[:2]:
                w = w.strip()
                if w and len(w) < 20:
                    keywords.append(w)
        if keywords:
            lines.append(f"- {icon} **{category}**：{'、'.join(keywords[:4])}")

    lines.append("")

    # 添加认知盲区模块
    if knowledge_gaps:
        lines.append("---")
        lines.append("")
        lines.append("## 🧠 认知盲区（不在知识库中的概念）")
        lines.append("")
        lines.append("以下关键词在今日会话中出现，但尚未纳入你的知识体系，可按图索骥学习：")
        lines.append("")

        # 分组显示：英文 vs 中文
        english_gaps = [g for g in knowledge_gaps if g[0].isascii()]
        chinese_gaps = [g for g in knowledge_gaps if not g[0].isascii()]

        if english_gaps:
            lines.append(f"**英文概念**: `{'` `'.join(english_gaps[:15])}`")
            lines.append("")

        if chinese_gaps:
            lines.append(f"**中文概念**: `{'` `'.join(chinese_gaps[:10])}`")
            lines.append("")

        lines.append("")
        lines.append("> 💡 建议：选择感兴趣的关键词，搜索学习后在知识库中创建对应笔记")
        lines.append("")

    return "\n".join(lines)


def export_sessions():
    """导出今天的所有会话"""
    now = datetime.now(BEIJING_TZ)
    today_str = now.strftime("%Y-%m-%d")

    print(f"🔍 正在查找 {today_str} 的 Claude Code 会话...")

    sessions = get_today_sessions()

    if not sessions:
        print("📭 今天没有 Claude Code 会话记录")
        return

    print(f"✓ 找到 {len(sessions)} 个会话")

    # 确保输出目录存在
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 生成输出文件
    filename = f"{today_str}_Claude_Code.md"
    filepath = OUTPUT_DIR / filename

    # 构建 Markdown 内容
    content_lines = [
        f"---",
        f"date: {today_str}",
        f"type: claude-code-export",
        f"sessions: {len(sessions)}",
        f"---",
        f"",
        f"# {today_str} Claude Code 会话记录",
        f"",
        f"共 **{len(sessions)}** 个会话",
        f"",
    ]

    # 构建知识库索引
    print("📚 正在构建知识库索引...")
    knowledge_index = build_knowledge_index()
    print(f"   知识库包含 {len(knowledge_index)} 个概念")

    # 用于生成话题总结
    sessions_data = []

    # 解析并添加每个会话
    for i, session in enumerate(sessions, 1):
        print(f"  📄 处理会话 {i}/{len(sessions)}: {session['path'].stem[:8]}...")

        session_info = parse_session(session["path"])
        md_content = format_session_markdown(session_info, session["project"])
        content_lines.append(md_content)

        # 收集话题数据（包含消息用于概念提取）
        time_str = ""
        if session_info["start_time"]:
            time_str = session_info["start_time"].astimezone(BEIJING_TZ).strftime("%H:%M")
        sessions_data.append({
            "time": time_str,
            "summary": session_info.get("summary", ""),
            "messages": session_info.get("messages", [])
        })

    # 写入完整导出文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("\n".join(content_lines))

    print(f"✅ 已导出到: {filepath}")
    print(f"   文件大小: {filepath.stat().st_size / 1024:.1f} KB")

    # 找出认知盲区
    print("🔍 正在分析认知盲区...")
    knowledge_gaps = find_knowledge_gaps(sessions_data, knowledge_index)
    if knowledge_gaps:
        print(f"   发现 {len(knowledge_gaps)} 个新概念")

    # 生成话题总结
    summary_filename = f"{today_str}_话题总结.md"
    summary_filepath = OUTPUT_DIR / summary_filename

    summary_content = generate_topic_summary(sessions_data, today_str, knowledge_gaps)

    with open(summary_filepath, 'w', encoding='utf-8') as f:
        f.write(summary_content)

    print(f"✅ 话题总结: {summary_filepath}")


if __name__ == "__main__":
    export_sessions()
