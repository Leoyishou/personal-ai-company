#!/usr/bin/env python3
"""
词汇匹配器 - 从 Supabase 获取用户已知词汇并进行匹配

数据来源：
- vocab_levels 表：toefl-100 级别词汇（约 13,436 词）
- user_vocab 表：用户个人词汇记录
"""

import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# 常见停用词
STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "must", "shall", "can", "need", "dare",
    "to", "of", "in", "for", "on", "with", "at", "by", "from", "as",
    "into", "through", "during", "before", "after", "above", "below",
    "between", "under", "again", "further", "then", "once", "here",
    "there", "when", "where", "why", "how", "all", "each", "few",
    "more", "most", "other", "some", "such", "no", "nor", "not",
    "only", "own", "same", "so", "than", "too", "very", "just",
    "and", "but", "if", "or", "because", "until", "while", "although",
    "this", "that", "these", "those", "i", "me", "my", "myself", "we",
    "our", "ours", "ourselves", "you", "your", "yours", "yourself",
    "he", "him", "his", "himself", "she", "her", "hers", "herself",
    "it", "its", "itself", "they", "them", "their", "theirs", "themselves",
    "what", "which", "who", "whom", "whose", "about", "also", "any",
    "both", "either", "neither", "every", "much", "many", "another",
    "get", "got", "getting", "go", "going", "gone", "went", "come",
    "coming", "came", "make", "making", "made", "take", "taking", "took",
    "see", "seeing", "saw", "seen", "know", "knowing", "knew", "known",
    "think", "thinking", "thought", "say", "saying", "said", "tell",
    "telling", "told", "give", "giving", "gave", "given", "find",
    "finding", "found", "want", "wanting", "wanted", "look", "looking",
    "looked", "use", "using", "used", "thing", "things", "way", "ways",
    "yeah", "yes", "no", "oh", "well", "okay", "ok", "right", "like",
    "gonna", "wanna", "gotta", "kinda", "let", "lets", "lot", "lots",
}

CACHE_DIR = Path(__file__).parent.parent / "cache"
VOCAB_CACHE_FILE = CACHE_DIR / "vocab_cache.json"
SYNC_META_FILE = CACHE_DIR / "sync_meta.json"


def load_env():
    """从 secrets.env 加载环境变量"""
    secrets_path = Path.home() / ".claude" / "secrets.env"
    if secrets_path.exists():
        with open(secrets_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    if line.startswith("export "):
                        line = line[7:]
                    key, _, value = line.partition("=")
                    value = value.strip('"\'')
                    if key not in os.environ:
                        os.environ[key] = value


def get_supabase_client():
    """获取 Supabase 客户端"""
    load_env()

    try:
        from supabase import create_client
    except ImportError:
        raise ImportError("Please install supabase: pip install supabase")

    url = os.environ.get("AI50_URL")
    key = os.environ.get("AI50_SERVICE_KEY")

    if not url or not key:
        raise ValueError("AI50_URL and AI50_SERVICE_KEY must be set")

    return create_client(url, key)


def sync_vocabulary(force: bool = False) -> dict:
    """
    从 Supabase 同步词汇到本地缓存

    Args:
        force: 强制完全同步

    Returns:
        词汇缓存数据
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # 检查是否需要同步
    meta = load_sync_meta()
    last_sync = meta.get("last_sync")

    if not force and last_sync:
        last_sync_time = datetime.fromisoformat(last_sync)
        if datetime.now() - last_sync_time < timedelta(hours=1):
            # 缓存仍有效
            cache = load_vocab_cache()
            if cache:
                return cache

    print("Syncing vocabulary from Supabase...")
    client = get_supabase_client()

    # 获取 toefl-100 词汇
    toefl_response = client.table("vocab_levels").select("words").eq("level", "toefl-100").execute()
    toefl_words = []
    if toefl_response.data:
        toefl_words = toefl_response.data[0].get("words", [])

    # 获取 user_vocab
    user_response = client.table("user_vocab").select("word, status").eq("is_deleted", False).execute()
    user_known = []
    user_learning = []
    if user_response.data:
        for row in user_response.data:
            word = row.get("word", "").lower()
            status = row.get("status")
            if status == "known":
                user_known.append(word)
            elif status == "learning":
                user_learning.append(word)

    cache = {
        "toefl_100": [w.lower() for w in toefl_words],
        "user_known": user_known,
        "user_learning": user_learning,
        "synced_at": datetime.now().isoformat(),
    }

    # 保存缓存
    save_vocab_cache(cache)
    save_sync_meta({"last_sync": datetime.now().isoformat()})

    print(f"Synced: {len(toefl_words)} toefl-100 words, {len(user_known)} known, {len(user_learning)} learning")

    return cache


def load_vocab_cache() -> Optional[dict]:
    """加载词汇缓存"""
    if VOCAB_CACHE_FILE.exists():
        with open(VOCAB_CACHE_FILE) as f:
            return json.load(f)
    return None


def save_vocab_cache(cache: dict):
    """保存词汇缓存"""
    with open(VOCAB_CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def load_sync_meta() -> dict:
    """加载同步元数据"""
    if SYNC_META_FILE.exists():
        with open(SYNC_META_FILE) as f:
            return json.load(f)
    return {}


def save_sync_meta(meta: dict):
    """保存同步元数据"""
    with open(SYNC_META_FILE, "w") as f:
        json.dump(meta, f, indent=2)


def get_known_words_set() -> set[str]:
    """
    获取用户已知词汇集合

    Returns:
        已知词汇的 set（全小写）
    """
    cache = sync_vocabulary()

    known = set()
    known.update(cache.get("toefl_100", []))
    known.update(cache.get("user_known", []))
    known.update(cache.get("user_learning", []))

    return known


def extract_words(text: str) -> list[str]:
    """
    从文本中提取单词

    Args:
        text: 输入文本

    Returns:
        单词列表
    """
    # 提取字母组成的单词
    words = re.findall(r"[a-zA-Z]+(?:'[a-zA-Z]+)?", text)
    return words


def find_unfamiliar_words(text: str, known_words: set[str]) -> list[str]:
    """
    找出文本中的生词

    Args:
        text: 输入文本
        known_words: 已知词汇集合

    Returns:
        生词列表（保持原始大小写）
    """
    words = extract_words(text)
    unfamiliar = []

    for word in words:
        lower_word = word.lower()
        # 跳过停用词和短词
        if lower_word in STOPWORDS:
            continue
        if len(word) <= 2:
            continue
        # 跳过已知词
        if lower_word in known_words:
            continue
        # 跳过数字相关
        if any(c.isdigit() for c in word):
            continue

        unfamiliar.append(word)

    # 去重但保持顺序
    seen = set()
    result = []
    for w in unfamiliar:
        if w.lower() not in seen:
            seen.add(w.lower())
            result.append(w)

    return result


if __name__ == "__main__":
    import sys

    # 测试词汇同步
    known = get_known_words_set()
    print(f"Total known words: {len(known)}")

    # 测试生词识别
    test_sentences = [
        "This phone has a terabyte of storage and 50 megapixels camera.",
        "The Vertu Agent Q is a luxury smartphone.",
        "It has 5500 milliamp battery with 65 watts charging.",
    ]

    for sentence in test_sentences:
        unfamiliar = find_unfamiliar_words(sentence, known)
        print(f"\nSentence: {sentence}")
        print(f"Unfamiliar words: {unfamiliar}")
