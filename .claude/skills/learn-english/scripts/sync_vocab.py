#!/usr/bin/env python3
"""
词汇同步脚本 - 独立运行以更新本地缓存

使用方法：
    python sync_vocab.py          # 增量同步
    python sync_vocab.py --force  # 强制完全同步
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from vocab_matcher import sync_vocabulary, get_known_words_set, VOCAB_CACHE_FILE


def main():
    parser = argparse.ArgumentParser(description="词汇同步工具")
    parser.add_argument("--force", "-f", action="store_true", help="强制完全同步")
    parser.add_argument("--stats", "-s", action="store_true", help="只显示统计信息")

    args = parser.parse_args()

    if args.stats:
        known = get_known_words_set()
        print(f"Total known words: {len(known)}")
        print(f"Cache file: {VOCAB_CACHE_FILE}")
        return

    if args.force:
        # 删除缓存文件强制重新同步
        if VOCAB_CACHE_FILE.exists():
            VOCAB_CACHE_FILE.unlink()
            print("Cache cleared.")

    cache = sync_vocabulary(force=args.force)

    print(f"\nVocabulary cache updated:")
    print(f"  toefl-100: {len(cache.get('toefl_100', []))} words")
    print(f"  user_known: {len(cache.get('user_known', []))} words")
    print(f"  user_learning: {len(cache.get('user_learning', []))} words")
    print(f"  Synced at: {cache.get('synced_at')}")


if __name__ == "__main__":
    main()
