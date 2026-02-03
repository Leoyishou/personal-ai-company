#!/usr/bin/env python3
"""
Reddit 深度调研模板生成器

支持多种调研场景：痛点挖掘、舆情分析、投资情绪、技术趋势等
"""

import json
import sys
from typing import List, Dict, Optional

# ============================================
# 搜索模板库
# ============================================

PAIN_TEMPLATES = {
    "emotion_trigger": [
        "tired of {topic}",
        "frustrated with {topic}",
        "why does {topic} suck",
        "anyone else hate {topic}",
        "sick of {topic}",
    ],
    "desire_seeking": [
        "wish there was {topic}",
        "how do I {topic}",
        "what actually works for {topic}",
        "best way to {topic}",
    ],
    "pain_validation": [
        "anyone else struggling with {topic}",
        "feeling stuck with {topic}",
        "can't figure out {topic}",
    ],
}

SENTIMENT_TEMPLATES = {
    "positive": [
        "{topic} is amazing",
        "love {topic}",
        "{topic} changed my life",
        "finally {topic} works",
    ],
    "negative": [
        "{topic} is terrible",
        "hate {topic}",
        "{topic} ruined",
        "never using {topic} again",
        "{topic} scam",
    ],
    "neutral_discussion": [
        "thoughts on {topic}",
        "what do you think about {topic}",
        "{topic} discussion",
        "honest opinion {topic}",
    ],
}

INVESTMENT_TEMPLATES = {
    "bullish": [
        "{ticker} to the moon",
        "buying more {ticker}",
        "{ticker} undervalued",
        "long {ticker}",
        "{ticker} bull case",
    ],
    "bearish": [
        "{ticker} overvalued",
        "selling {ticker}",
        "{ticker} crash",
        "short {ticker}",
        "{ticker} bear case",
    ],
    "analysis": [
        "{ticker} DD",
        "{ticker} analysis",
        "{ticker} fundamentals",
        "is {ticker} worth buying",
    ],
    "sentiment": [
        "what happened to {ticker}",
        "{ticker} news",
        "why is {ticker} down",
        "why is {ticker} up",
    ],
}

TECH_TEMPLATES = {
    "comparison": [
        "{tech1} vs {tech2}",
        "{tech} alternatives",
        "switching from {tech}",
        "migrating to {tech}",
    ],
    "experience": [
        "{tech} in production",
        "{tech} real world",
        "using {tech} for",
        "{tech} experience",
    ],
    "learning": [
        "learning {tech}",
        "{tech} worth learning",
        "{tech} roadmap",
        "how long to learn {tech}",
    ],
    "problems": [
        "{tech} problems",
        "{tech} issues",
        "{tech} not working",
        "hate {tech}",
    ],
}

ALTERNATIVE_TEMPLATES = {
    "seeking": [
        "{product} alternative",
        "leaving {product}",
        "migrating from {product}",
        "replace {product}",
    ],
    "comparison": [
        "{product} vs",
        "better than {product}",
        "{product} competitor",
    ],
}

# ============================================
# Subreddit 分类
# ============================================

SUBREDDIT_CATEGORIES = {
    "finance": [
        "wallstreetbets", "stocks", "investing", "options",
        "cryptocurrency", "Bitcoin", "ethereum", "CryptoMarkets",
        "personalfinance", "financialindependence", "Fire",
        "Bogleheads", "dividends", "ValueInvesting",
    ],
    "tech": [
        "programming", "webdev", "learnprogramming",
        "MachineLearning", "artificial", "LocalLLaMA",
        "devops", "sysadmin", "kubernetes",
        "reactjs", "node", "golang", "rust",
        "technology", "gadgets", "hardware",
    ],
    "ai": [
        "ChatGPT", "LocalLLaMA", "artificial",
        "MachineLearning", "singularity", "OpenAI",
        "StableDiffusion", "midjourney",
    ],
    "career": [
        "careerguidance", "jobs", "careeradvice",
        "cscareerquestions", "ExperiencedDevs",
        "antiwork", "workreform", "overemployed",
    ],
    "startup": [
        "Entrepreneur", "startups", "SideProject",
        "smallbusiness", "indiehackers",
    ],
    "productivity": [
        "productivity", "getdisciplined", "selfimprovement",
        "nosurf", "DecidingToBeBetter",
    ],
    "consumer": [
        "BuyItForLife", "Frugal", "deals",
        "homeautomation", "smarthome",
        "Apple", "Android", "GooglePixel",
    ],
    "news": [
        "news", "worldnews", "politics",
        "technology", "business", "economics",
        "OutOfTheLoop", "explainlikeimfive",
    ],
    "gaming": [
        "gaming", "pcgaming", "Games",
        "PS5", "XboxSeriesX", "NintendoSwitch",
    ],
    "china": [
        "China", "Sino", "ChinaStocks",
        "ChineseLanguage", "chinesefood",
    ],
}

# ============================================
# 预设调研场景
# ============================================

PRESET_SCENARIOS = {
    # ===== 痛点/产品类 =====
    "youtube_职场": {
        "type": "pain",
        "description": "YouTube选题：20-30岁职场新人痛点",
        "queries": {
            "career": [
                "tired of dead-end job",
                "stuck in career",
                "hate my job but scared to quit",
            ],
            "productivity": [
                "struggling with productivity",
                "can't focus at work",
                "feeling burnt out in 20s",
            ],
            "side_hustle": [
                "side hustle that actually works",
                "passive income for beginners",
                "make money outside 9-5",
            ],
        },
        "subreddits": ["careerguidance", "jobs", "productivity", "getdisciplined", "antiwork", "sidehustle"],
    },
    "ai_product": {
        "type": "pain",
        "description": "AI产品机会调研",
        "queries": {
            "pain_points": [
                "frustrating about ChatGPT",
                "AI limitations annoying",
                "wish AI could",
            ],
            "workflow": [
                "AI workflow automation",
                "prompt chaining",
                "AI agent tools",
            ],
            "local_llm": [
                "run LLM locally",
                "VRAM not enough",
                "local AI privacy",
            ],
        },
        "subreddits": ["ChatGPT", "LocalLLaMA", "SideProject", "artificial", "singularity"],
    },
    "notion_competitor": {
        "type": "pain",
        "description": "Notion竞品分析",
        "queries": {
            "pain": [
                "Notion slow",
                "Notion offline",
                "Notion data export",
            ],
            "migration": [
                "leaving Notion",
                "Notion alternative",
                "Obsidian vs Notion",
            ],
            "pricing": [
                "Notion pricing",
                "Notion subscription",
                "Notion lock-in",
            ],
        },
        "subreddits": ["Notion", "ObsidianMD", "productivity", "PKMS"],
    },

    # ===== 舆情类 =====
    "sentiment_openai": {
        "type": "sentiment",
        "description": "OpenAI舆情分析",
        "queries": {
            "positive": [
                "OpenAI amazing",
                "ChatGPT changed my life",
                "love GPT",
            ],
            "negative": [
                "OpenAI terrible",
                "hate OpenAI",
                "OpenAI scam",
                "OpenAI unethical",
            ],
            "discussion": [
                "thoughts on OpenAI",
                "OpenAI vs Anthropic",
                "OpenAI news",
            ],
        },
        "subreddits": ["ChatGPT", "OpenAI", "artificial", "LocalLLaMA", "technology"],
    },
    "sentiment_tesla": {
        "type": "sentiment",
        "description": "Tesla品牌舆情",
        "queries": {
            "positive": [
                "love my Tesla",
                "Tesla best car",
                "Tesla amazing",
            ],
            "negative": [
                "Tesla problems",
                "Tesla quality issues",
                "regret buying Tesla",
                "hate Tesla",
            ],
            "discussion": [
                "Tesla vs",
                "is Tesla worth it",
                "Tesla honest review",
            ],
        },
        "subreddits": ["TeslaMotors", "electricvehicles", "cars", "technology", "RealTesla"],
    },

    # ===== 投资类 =====
    "investment_nvda": {
        "type": "investment",
        "description": "NVIDIA投资情绪",
        "queries": {
            "bullish": [
                "NVDA to the moon",
                "buying NVDA",
                "NVDA undervalued",
            ],
            "bearish": [
                "NVDA overvalued",
                "selling NVDA",
                "NVDA bubble",
            ],
            "analysis": [
                "NVDA DD",
                "NVDA analysis",
                "is NVDA worth buying",
            ],
        },
        "subreddits": ["wallstreetbets", "stocks", "investing", "nvda_stock", "options"],
    },
    "investment_btc": {
        "type": "investment",
        "description": "Bitcoin投资情绪",
        "queries": {
            "bullish": [
                "Bitcoin bull run",
                "buying more BTC",
                "Bitcoin to 100k",
            ],
            "bearish": [
                "Bitcoin crash",
                "selling Bitcoin",
                "Bitcoin bubble",
            ],
            "analysis": [
                "Bitcoin analysis",
                "BTC prediction",
                "Bitcoin halving",
            ],
        },
        "subreddits": ["Bitcoin", "CryptoCurrency", "BitcoinMarkets", "CryptoMarkets"],
    },
    "investment_china": {
        "type": "investment",
        "description": "中概股/中国市场情绪",
        "queries": {
            "bullish": [
                "China stocks undervalued",
                "buying China",
                "BABA undervalued",
            ],
            "bearish": [
                "China uninvestable",
                "selling China stocks",
                "China risk",
            ],
            "analysis": [
                "China market analysis",
                "BABA DD",
                "is China investable",
            ],
        },
        "subreddits": ["stocks", "investing", "ChinaStocks", "Sino", "wallstreetbets"],
    },

    # ===== 技术类 =====
    "tech_rust_go": {
        "type": "tech",
        "description": "Rust vs Go 技术对比",
        "queries": {
            "comparison": [
                "Rust vs Go",
                "switching from Go to Rust",
                "Rust or Go",
            ],
            "experience": [
                "Rust in production",
                "Go in production",
                "Rust real world",
            ],
            "learning": [
                "learning Rust",
                "Rust worth learning",
                "Go worth learning",
            ],
        },
        "subreddits": ["rust", "golang", "programming", "ExperiencedDevs"],
    },
    "tech_framework": {
        "type": "tech",
        "description": "前端框架趋势",
        "queries": {
            "comparison": [
                "React vs Vue vs Svelte",
                "Next.js vs Remix",
                "switching from React",
            ],
            "experience": [
                "React in production",
                "Vue experience",
                "Svelte real world",
            ],
            "problems": [
                "React problems",
                "Vue issues",
                "Next.js problems",
            ],
        },
        "subreddits": ["reactjs", "vuejs", "sveltejs", "webdev", "javascript"],
    },

    # ===== 热点事件类 =====
    "hot_deepseek": {
        "type": "mixed",
        "description": "DeepSeek社区反响",
        "queries": {
            "sentiment": [
                "DeepSeek amazing",
                "DeepSeek vs ChatGPT",
                "thoughts on DeepSeek",
            ],
            "technical": [
                "DeepSeek benchmark",
                "running DeepSeek locally",
                "DeepSeek API",
            ],
            "concern": [
                "DeepSeek China",
                "DeepSeek censorship",
                "DeepSeek privacy",
            ],
        },
        "subreddits": ["LocalLLaMA", "MachineLearning", "artificial", "ChatGPT"],
    },
}


def generate_queries(
    template_type: str,
    topics: List[str],
    templates: Dict = None
) -> Dict[str, List[str]]:
    """
    根据模板类型和主题生成搜索查询

    Args:
        template_type: 模板类型 (pain/sentiment/investment/tech)
        topics: 主题列表
        templates: 自定义模板（可选）

    Returns:
        查询字典
    """
    if templates is None:
        template_map = {
            "pain": PAIN_TEMPLATES,
            "sentiment": SENTIMENT_TEMPLATES,
            "investment": INVESTMENT_TEMPLATES,
            "tech": TECH_TEMPLATES,
            "alternative": ALTERNATIVE_TEMPLATES,
        }
        templates = template_map.get(template_type, PAIN_TEMPLATES)

    queries = {}
    for category, patterns in templates.items():
        queries[category] = []
        for topic in topics:
            for pattern in patterns[:3]:  # 每个类别取前3个模板
                query = pattern.format(
                    topic=topic,
                    ticker=topic,
                    tech=topic,
                    tech1=topic,
                    tech2=topic,
                    product=topic,
                )
                queries[category].append(query)

    return queries


def get_subreddits(category: str) -> List[str]:
    """获取指定类别的subreddits"""
    return SUBREDDIT_CATEGORIES.get(category, ["all"])


def generate_bash_commands(
    queries: Dict[str, List[str]],
    subreddits: List[str],
    output_prefix: str = "research",
    time_filter: str = "month",
    limit: int = 10
) -> List[str]:
    """
    生成可执行的bash命令

    Args:
        queries: 查询字典
        subreddits: 目标subreddits
        output_prefix: 输出文件前缀
        time_filter: 时间过滤器
        limit: 结果数量限制

    Returns:
        Bash命令列表
    """
    base_cmd = """cd /Users/liuyishou/.claude/skills/research-by-reddit/scripts && \\
export $(cat ../.env | grep -v '^#' | xargs) && \\
python analyze_reddit.py \\
  --query "{query}" \\
  --search-subreddit {subreddit} \\
  --search-sort top \\
  --time-filter {time_filter} \\
  --limit {limit} \\
  --include-comments \\
  --comment-limit 8 \\
  --analysis-language zh \\
  --output-md {output}.md"""

    commands = []
    idx = 0

    for category, query_list in queries.items():
        # 合并同类查询（使用OR连接）
        combined_query = " OR ".join(query_list[:3])

        for subreddit in subreddits[:2]:  # 限制前2个subreddit
            cmd = base_cmd.format(
                query=combined_query,
                subreddit=subreddit,
                time_filter=time_filter,
                limit=limit,
                output=f"{output_prefix}_{category}_{idx}"
            )
            commands.append(cmd)
            idx += 1

    return commands


def print_research_plan(scenario_name: str, config: Dict):
    """打印调研计划"""
    print(f"\n{'='*60}")
    print(f"调研场景: {scenario_name}")
    print(f"描述: {config['description']}")
    print(f"类型: {config['type']}")
    print(f"{'='*60}")

    print(f"\n目标Subreddits: {', '.join(config['subreddits'])}")

    print("\n搜索查询:")
    for category, query_list in config['queries'].items():
        print(f"\n  [{category}]")
        for q in query_list[:5]:
            print(f"    - {q}")

    print(f"\n{'='*60}")


def print_available_scenarios():
    """打印所有可用场景"""
    print("\n可用调研场景:")
    print("-" * 60)

    categories = {
        "痛点/产品类": ["youtube_职场", "ai_product", "notion_competitor"],
        "舆情分析类": ["sentiment_openai", "sentiment_tesla"],
        "投资情绪类": ["investment_nvda", "investment_btc", "investment_china"],
        "技术趋势类": ["tech_rust_go", "tech_framework"],
        "热点事件类": ["hot_deepseek"],
    }

    for cat_name, scenarios in categories.items():
        print(f"\n{cat_name}:")
        for s in scenarios:
            if s in PRESET_SCENARIOS:
                print(f"  {s}: {PRESET_SCENARIOS[s]['description']}")

    print("\n" + "-" * 60)
    print("用法: python research_templates.py <scenario>")
    print("示例: python research_templates.py investment_nvda")


def create_custom_scenario(
    name: str,
    description: str,
    research_type: str,
    topics: List[str],
    subreddit_category: str
) -> Dict:
    """
    创建自定义调研场景

    Args:
        name: 场景名称
        description: 描述
        research_type: 调研类型 (pain/sentiment/investment/tech)
        topics: 主题列表
        subreddit_category: subreddit分类

    Returns:
        场景配置字典
    """
    queries = generate_queries(research_type, topics)
    subreddits = get_subreddits(subreddit_category)

    return {
        "type": research_type,
        "description": description,
        "queries": queries,
        "subreddits": subreddits,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_available_scenarios()
        sys.exit(0)

    scenario = sys.argv[1]

    # 检查是否是预设场景
    if scenario in PRESET_SCENARIOS:
        config = PRESET_SCENARIOS[scenario]
        print_research_plan(scenario, config)

        # 生成bash命令
        commands = generate_bash_commands(
            config["queries"],
            config["subreddits"],
            output_prefix=scenario
        )

        print("\n生成的Bash命令:")
        for i, cmd in enumerate(commands):
            print(f"\n# 命令 {i+1}")
            print(cmd)

    # 支持自定义格式: custom:type:topic1,topic2:subreddit_category
    elif scenario.startswith("custom:"):
        parts = scenario.split(":")
        if len(parts) < 4:
            print("自定义格式: custom:type:topic1,topic2:subreddit_category")
            print("示例: custom:sentiment:Tesla,Elon:tech")
            sys.exit(1)

        research_type = parts[1]
        topics = parts[2].split(",")
        subreddit_cat = parts[3]

        config = create_custom_scenario(
            name="custom",
            description=f"自定义调研: {', '.join(topics)}",
            research_type=research_type,
            topics=topics,
            subreddit_category=subreddit_cat
        )

        print_research_plan("custom", config)

        commands = generate_bash_commands(
            config["queries"],
            config["subreddits"],
            output_prefix="custom"
        )

        print("\n生成的Bash命令:")
        for i, cmd in enumerate(commands):
            print(f"\n# 命令 {i+1}")
            print(cmd)

    else:
        print(f"未知场景: {scenario}")
        print_available_scenarios()
        sys.exit(1)
