#!/usr/bin/env python3
"""
WebFetchPlus - 智能网页内容抓取工具
根据URL类型自动选择最佳抓取策略
"""

import re
import json
import os
import sys
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlparse
import requests
from datetime import datetime

# ==================== 配置加载 ====================
class FetchStrategy(Enum):
    """抓取策略枚举"""
    TWITTER_API = "twitter_api"       # Twitter/X专用API
    FIRECRAWL = "firecrawl"           # 通用网页抓取
    DOUYIN = "douyin"                 # 抖音下载
    BILIBILI = "bilibili"             # B站下载
    XIAOHONGSHU = "xiaohongshu"       # 小红书
    YOUTUBE = "youtube"               # YouTube
    ZHIHU = "zhihu"                   # 知乎
    GENERIC = "generic"               # 通用HTTP抓取

@dataclass
class FetchConfig:
    """抓取配置"""
    twitter_api_key: str = ""
    firecrawl_api_key: str = ""
    proxy: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    save_path: str = "~/webfetch_downloads"
    debug: bool = False

class URLDetector:
    """URL类型检测器"""

    PATTERNS = {
        FetchStrategy.TWITTER_API: [
            r'(?:twitter|x)\.com/[\w]+/status/\d+',
            r'(?:twitter|x)\.com/[\w]+$',
            r'(?:twitter|x)\.com/[\w]+/.*'
        ],
        FetchStrategy.DOUYIN: [
            r'douyin\.com/',
            r'iesdouyin\.com/',
            r'v\.douyin\.com/'
        ],
        FetchStrategy.BILIBILI: [
            r'bilibili\.com/video/',
            r'b23\.tv/',
            r'bilibili\.com/bangumi/'
        ],
        FetchStrategy.XIAOHONGSHU: [
            r'xiaohongshu\.com/',
            r'xhslink\.com/'
        ],
        FetchStrategy.YOUTUBE: [
            r'youtube\.com/watch',
            r'youtu\.be/',
            r'youtube\.com/shorts/'
        ],
        FetchStrategy.ZHIHU: [
            r'zhihu\.com/question/\d+',      # 问题页
            r'zhihu\.com/answer/\d+',        # 回答直链
            r'zhuanlan\.zhihu\.com/p/\d+',   # 专栏文章
            r'zhihu\.com/p/\d+',             # 新版文章
            r'zhihu\.com/people/[\w-]+',     # 用户主页
            r'zhihu\.com/column/[\w-]+'      # 专栏
        ]
    }

    @classmethod
    def detect(cls, url: str) -> FetchStrategy:
        """检测URL类型并返回对应策略"""
        for strategy, patterns in cls.PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    return strategy
        return FetchStrategy.GENERIC

# ==================== Twitter API 抓取器 ====================
class TwitterFetcher:
    """使用 docs.twitterapi.io 抓取Twitter/X内容"""

    BASE_URL = "https://api.twitterapi.io"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }

    def fetch_tweet(self, url: str) -> Dict[str, Any]:
        """获取推文详情"""
        # 从URL提取tweet_id
        tweet_id = self._extract_tweet_id(url)
        if not tweet_id:
            return {"error": "无法从URL提取推文ID"}

        # 使用正确的API端点格式
        endpoint = f"{self.BASE_URL}/twitter/tweets"
        params = {
            "tweet_ids": tweet_id  # API接受tweet_ids参数
        }

        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            return self._parse_tweet_response(response.json())
        except Exception as e:
            return {"error": f"获取推文失败: {str(e)}"}

    def fetch_user(self, url: str) -> Dict[str, Any]:
        """获取用户信息"""
        username = self._extract_username(url)
        if not username:
            return {"error": "无法从URL提取用户名"}

        # 使用正确的API端点格式
        endpoint = f"{self.BASE_URL}/twitter/users"
        params = {
            "usernames": username  # API接受usernames参数
        }

        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            return self._parse_user_response(response.json())
        except Exception as e:
            return {"error": f"获取用户信息失败: {str(e)}"}

    def fetch_timeline(self, username: str, max_results: int = 10) -> Dict[str, Any]:
        """获取用户时间线"""
        # 首先获取用户ID
        user_data = self.fetch_user(f"https://x.com/{username}")
        if "error" in user_data:
            return user_data

        user_id = user_data.get("id")
        if not user_id:
            return {"error": "无法获取用户ID"}

        endpoint = f"{self.BASE_URL}/2/users/{user_id}/tweets"
        params = {
            "max_results": max_results,
            "tweet.fields": "created_at,text,public_metrics,attachments",
            "media.fields": "url,preview_image_url,type"
        }

        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            return self._parse_timeline_response(response.json())
        except Exception as e:
            return {"error": f"获取时间线失败: {str(e)}"}

    def search_tweets(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """搜索推文"""
        # TwitterAPI.io 的搜索端点
        endpoint = f"{self.BASE_URL}/twitter/search"
        params = {
            "query": query,
            "limit": min(max_results, 100)  # API限制
        }

        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            return self._parse_search_response(response.json())
        except Exception as e:
            return {"error": f"搜索失败: {str(e)}"}

    def _extract_tweet_id(self, url: str) -> Optional[str]:
        """从URL提取推文ID"""
        match = re.search(r'/status/(\d+)', url)
        return match.group(1) if match else None

    def _extract_username(self, url: str) -> Optional[str]:
        """从URL提取用户名"""
        match = re.search(r'(?:twitter|x)\.com/(@?[\w]+)', url)
        if match:
            username = match.group(1)
            return username.lstrip('@')
        return None

    def _parse_tweet_response(self, data: Dict) -> Dict[str, Any]:
        """解析推文响应 - 适配TwitterAPI.io的响应格式"""
        # TwitterAPI.io 返回格式: {"tweets": [{tweet_object}]}
        if "tweets" in data and isinstance(data["tweets"], list) and len(data["tweets"]) > 0:
            tweet = data["tweets"][0]
        elif isinstance(data, list) and len(data) > 0:
            tweet = data[0]
        else:
            return {"error": "未找到推文数据"}

        # 提取核心信息 - 基于实际的TwitterAPI.io响应格式
        author_info = tweet.get("author", {})

        return {
            "id": tweet.get("id"),
            "text": tweet.get("text"),
            "created_at": tweet.get("createdAt"),
            "author": {
                "id": author_info.get("id"),
                "name": author_info.get("name"),
                "username": author_info.get("userName"),
                "verified": author_info.get("isVerified", False),
                "blue_verified": author_info.get("isBlueVerified", False),
                "profile_picture": author_info.get("profilePicture"),
                "description": author_info.get("description"),
                "followers": author_info.get("followers", 0),
                "following": author_info.get("following", 0)
            },
            "metrics": {
                "like_count": tweet.get("likeCount", 0),
                "retweet_count": tweet.get("retweetCount", 0),
                "reply_count": tweet.get("replyCount", 0),
                "quote_count": tweet.get("quoteCount", 0),
                "view_count": tweet.get("viewCount", 0),
                "bookmark_count": tweet.get("bookmarkCount", 0)
            },
            "media": tweet.get("media", []),
            "url": tweet.get("url"),
            "is_reply": tweet.get("isReply", False),
            "is_pinned": tweet.get("isPinned", False),
            "lang": tweet.get("lang")
        }

    def _parse_user_response(self, data: Dict) -> Dict[str, Any]:
        """解析用户响应"""
        if "data" not in data:
            return {"error": "响应中没有数据"}

        user = data["data"]
        return {
            "id": user.get("id"),
            "name": user.get("name"),
            "username": user.get("username"),
            "description": user.get("description"),
            "created_at": user.get("created_at"),
            "verified": user.get("verified"),
            "metrics": user.get("public_metrics"),
            "profile_image": user.get("profile_image_url"),
            "url": f"https://x.com/{user.get('username')}"
        }

    def _parse_timeline_response(self, data: Dict) -> Dict[str, Any]:
        """解析时间线响应"""
        tweets = data.get("data", [])
        return {
            "tweets": [
                {
                    "id": tweet.get("id"),
                    "text": tweet.get("text"),
                    "created_at": tweet.get("created_at"),
                    "metrics": tweet.get("public_metrics")
                }
                for tweet in tweets
            ],
            "count": len(tweets)
        }

    def _parse_search_response(self, data: Dict) -> Dict[str, Any]:
        """解析搜索响应"""
        tweets = data.get("data", [])
        includes = data.get("includes", {})
        users = {user["id"]: user for user in includes.get("users", [])}

        results = []
        for tweet in tweets:
            author_id = tweet.get("author_id")
            author = users.get(author_id, {})

            results.append({
                "id": tweet.get("id"),
                "text": tweet.get("text"),
                "created_at": tweet.get("created_at"),
                "author": {
                    "name": author.get("name"),
                    "username": author.get("username"),
                    "verified": author.get("verified", False)
                },
                "metrics": tweet.get("public_metrics")
            })

        return {
            "results": results,
            "count": len(results)
        }

# ==================== 通用抓取器基类 ====================
class BaseFetcher:
    """抓取器基类"""

    def fetch(self, url: str, **kwargs) -> Dict[str, Any]:
        """抓取内容"""
        raise NotImplementedError

    def download(self, url: str, save_path: str = None) -> Dict[str, Any]:
        """下载内容到本地"""
        raise NotImplementedError

# ==================== 社交媒体抓取器 ====================
class SocialMediaFetcher(BaseFetcher):
    """社交媒体内容抓取器"""

    def __init__(self):
        self.douyin_cookies = self._load_douyin_cookies()

    def _load_douyin_cookies(self):
        """加载抖音cookies"""
        cookie_path = os.path.expanduser("~/.claude/douyin_cookies.txt")
        if os.path.exists(cookie_path):
            with open(cookie_path) as f:
                return f.read().strip()
        return None

    def fetch_douyin(self, url: str) -> Dict[str, Any]:
        """抓取抖音内容"""
        # 这里调用现有的social-media-download脚本
        import subprocess

        script_path = os.path.expanduser("~/.claude/skills/social-media-download/scripts/social_download.py")

        try:
            result = subprocess.run(
                [sys.executable, script_path, url, "--json"],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                return {"error": f"抖音抓取失败: {result.stderr}"}
        except Exception as e:
            return {"error": f"调用抖音抓取脚本失败: {str(e)}"}

    def fetch_bilibili(self, url: str) -> Dict[str, Any]:
        """抓取B站内容"""
        # TODO: 实现B站抓取
        return {"message": "B站抓取功能待实现"}

    def fetch_xiaohongshu(self, url: str) -> Dict[str, Any]:
        """抓取小红书内容"""
        # TODO: 实现小红书抓取
        return {"message": "小红书抓取功能待实现"}

# ==================== 知乎抓取器 ====================
class ZhihuFetcher(BaseFetcher):
    """知乎内容抓取器"""

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Referer": "https://www.zhihu.com/",
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def fetch(self, url: str, **kwargs) -> Dict[str, Any]:
        """根据URL类型自动分发"""
        url_type = self._detect_url_type(url)

        if url_type == "question":
            return self.fetch_question(url)
        elif url_type == "answer":
            return self.fetch_answer(url)
        elif url_type == "article":
            return self.fetch_article(url)
        elif url_type == "people":
            return self.fetch_user(url)
        elif url_type == "column":
            return self.fetch_column(url)
        else:
            return {"error": f"未知的知乎URL类型: {url}"}

    def _detect_url_type(self, url: str) -> str:
        """检测知乎URL类型"""
        if "/question/" in url and "/answer/" in url:
            return "answer"
        elif "/question/" in url:
            return "question"
        elif "/answer/" in url:
            return "answer"
        elif "/p/" in url or "zhuanlan.zhihu.com" in url:
            return "article"
        elif "/people/" in url:
            return "people"
        elif "/column/" in url:
            return "column"
        return "unknown"

    def _extract_id(self, url: str, pattern: str) -> Optional[str]:
        """从URL提取ID"""
        match = re.search(pattern, url)
        return match.group(1) if match else None

    def fetch_question(self, url: str) -> Dict[str, Any]:
        """抓取知乎问题"""
        question_id = self._extract_id(url, r'/question/(\d+)')
        if not question_id:
            return {"error": "无法提取问题ID"}

        # 使用知乎API获取问题信息
        api_url = f"https://www.zhihu.com/api/v4/questions/{question_id}"
        params = {"include": "data[*].answer_count,follower_count,visit_count,comment_count"}

        try:
            response = self.session.get(api_url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            # 获取热门回答
            answers_url = f"https://www.zhihu.com/api/v4/questions/{question_id}/answers"
            answers_params = {
                "include": "data[*].content,author.name,author.headline,voteup_count,comment_count,created_time",
                "limit": 5,
                "sort_by": "default"
            }
            answers_resp = self.session.get(answers_url, params=answers_params, timeout=15)
            answers_data = answers_resp.json() if answers_resp.status_code == 200 else {}

            return {
                "type": "question",
                "id": question_id,
                "title": data.get("title"),
                "detail": self._clean_html(data.get("detail", "")),
                "created": data.get("created"),
                "updated": data.get("updated_time"),
                "answer_count": data.get("answer_count", 0),
                "follower_count": data.get("follower_count", 0),
                "visit_count": data.get("visit_count", 0),
                "topics": [t.get("name") for t in data.get("topics", [])],
                "url": f"https://www.zhihu.com/question/{question_id}",
                "top_answers": self._parse_answers(answers_data.get("data", []))
            }
        except Exception as e:
            return {"error": f"获取问题失败: {str(e)}"}

    def fetch_answer(self, url: str) -> Dict[str, Any]:
        """抓取知乎回答"""
        # 支持两种URL格式
        answer_id = self._extract_id(url, r'/answer/(\d+)')
        if not answer_id:
            return {"error": "无法提取回答ID"}

        api_url = f"https://www.zhihu.com/api/v4/answers/{answer_id}"
        params = {"include": "data[*].content,author.name,author.headline,author.avatar_url,voteup_count,comment_count,created_time,updated_time,question.title"}

        try:
            response = self.session.get(api_url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            author = data.get("author", {})
            question = data.get("question", {})

            return {
                "type": "answer",
                "id": answer_id,
                "content": self._clean_html(data.get("content", "")),
                "excerpt": data.get("excerpt", ""),
                "voteup_count": data.get("voteup_count", 0),
                "comment_count": data.get("comment_count", 0),
                "created_time": data.get("created_time"),
                "updated_time": data.get("updated_time"),
                "author": {
                    "name": author.get("name"),
                    "headline": author.get("headline"),
                    "avatar": author.get("avatar_url"),
                    "url_token": author.get("url_token")
                },
                "question": {
                    "id": question.get("id"),
                    "title": question.get("title")
                },
                "url": url
            }
        except Exception as e:
            return {"error": f"获取回答失败: {str(e)}"}

    def fetch_article(self, url: str) -> Dict[str, Any]:
        """抓取知乎专栏文章"""
        article_id = self._extract_id(url, r'/p/(\d+)')
        if not article_id:
            return {"error": "无法提取文章ID"}

        api_url = f"https://www.zhihu.com/api/v4/articles/{article_id}"

        try:
            response = self.session.get(api_url, timeout=15)
            response.raise_for_status()
            data = response.json()

            author = data.get("author", {})

            return {
                "type": "article",
                "id": article_id,
                "title": data.get("title"),
                "content": self._clean_html(data.get("content", "")),
                "excerpt": data.get("excerpt", ""),
                "voteup_count": data.get("voteup_count", 0),
                "comment_count": data.get("comment_count", 0),
                "created": data.get("created"),
                "updated": data.get("updated"),
                "image_url": data.get("image_url"),
                "author": {
                    "name": author.get("name"),
                    "headline": author.get("headline"),
                    "avatar": author.get("avatar_url"),
                    "url_token": author.get("url_token")
                },
                "topics": [t.get("name") for t in data.get("topics", [])],
                "url": f"https://zhuanlan.zhihu.com/p/{article_id}"
            }
        except Exception as e:
            return {"error": f"获取文章失败: {str(e)}"}

    def fetch_user(self, url: str) -> Dict[str, Any]:
        """抓取知乎用户信息"""
        url_token = self._extract_id(url, r'/people/([\w-]+)')
        if not url_token:
            return {"error": "无法提取用户标识"}

        api_url = f"https://www.zhihu.com/api/v4/members/{url_token}"
        params = {"include": "follower_count,following_count,answer_count,articles_count,voteup_count,thanked_count,description,headline,badge"}

        try:
            response = self.session.get(api_url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            return {
                "type": "user",
                "id": data.get("id"),
                "url_token": url_token,
                "name": data.get("name"),
                "headline": data.get("headline"),
                "description": data.get("description"),
                "avatar": data.get("avatar_url"),
                "gender": data.get("gender"),  # 0未知 1男 2女
                "follower_count": data.get("follower_count", 0),
                "following_count": data.get("following_count", 0),
                "answer_count": data.get("answer_count", 0),
                "articles_count": data.get("articles_count", 0),
                "voteup_count": data.get("voteup_count", 0),
                "thanked_count": data.get("thanked_count", 0),
                "badges": [b.get("description") for b in data.get("badge", [])],
                "url": f"https://www.zhihu.com/people/{url_token}"
            }
        except Exception as e:
            return {"error": f"获取用户信息失败: {str(e)}"}

    def fetch_column(self, url: str) -> Dict[str, Any]:
        """抓取知乎专栏信息"""
        column_id = self._extract_id(url, r'/column/([\w-]+)')
        if not column_id:
            return {"error": "无法提取专栏标识"}

        api_url = f"https://www.zhihu.com/api/v4/columns/{column_id}"

        try:
            response = self.session.get(api_url, timeout=15)
            response.raise_for_status()
            data = response.json()

            author = data.get("author", {})

            # 获取最新文章
            articles_url = f"https://www.zhihu.com/api/v4/columns/{column_id}/items"
            articles_params = {"limit": 10}
            articles_resp = self.session.get(articles_url, params=articles_params, timeout=15)
            articles_data = articles_resp.json() if articles_resp.status_code == 200 else {}

            return {
                "type": "column",
                "id": column_id,
                "title": data.get("title"),
                "description": data.get("description"),
                "intro": data.get("intro"),
                "image_url": data.get("image_url"),
                "articles_count": data.get("articles_count", 0),
                "followers_count": data.get("followers", 0),
                "author": {
                    "name": author.get("name"),
                    "headline": author.get("headline"),
                    "url_token": author.get("url_token")
                },
                "recent_articles": self._parse_column_articles(articles_data.get("data", [])),
                "url": f"https://www.zhihu.com/column/{column_id}"
            }
        except Exception as e:
            return {"error": f"获取专栏失败: {str(e)}"}

    def _parse_answers(self, answers: List[Dict]) -> List[Dict]:
        """解析回答列表"""
        result = []
        for ans in answers[:5]:
            author = ans.get("author", {})
            result.append({
                "id": ans.get("id"),
                "excerpt": ans.get("excerpt", "")[:200],
                "voteup_count": ans.get("voteup_count", 0),
                "comment_count": ans.get("comment_count", 0),
                "author": {
                    "name": author.get("name"),
                    "headline": author.get("headline")
                }
            })
        return result

    def _parse_column_articles(self, articles: List[Dict]) -> List[Dict]:
        """解析专栏文章列表"""
        result = []
        for art in articles[:10]:
            result.append({
                "id": art.get("id"),
                "title": art.get("title"),
                "excerpt": art.get("excerpt", "")[:100],
                "voteup_count": art.get("voteup_count", 0),
                "comment_count": art.get("comment_count", 0),
                "created": art.get("created")
            })
        return result

    def _clean_html(self, html: str) -> str:
        """清理HTML标签，保留纯文本"""
        if not html:
            return ""
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', html)
        # 清理多余空白
        text = re.sub(r'\s+', ' ', text).strip()
        return text

# ==================== 主控制器 ====================
class WebFetchPlus:
    """WebFetchPlus主控制器"""

    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.twitter_fetcher = TwitterFetcher(self.config.twitter_api_key) if self.config.twitter_api_key else None
        self.social_fetcher = SocialMediaFetcher()
        self.zhihu_fetcher = ZhihuFetcher()
        self.stats = {"total_fetches": 0, "success": 0, "failed": 0}

    def _load_config(self, config_path: str = None) -> FetchConfig:
        """加载配置"""
        config = FetchConfig()

        # 从环境变量加载
        config.twitter_api_key = os.environ.get("TWITTER_API_KEY", "new1_0a63d55aad214ca990884b2b6637419f")
        config.firecrawl_api_key = os.environ.get("FIRECRAWL_API_KEY", "")

        # 从配置文件加载
        if config_path and os.path.exists(config_path):
            with open(config_path) as f:
                data = json.load(f)
                for key, value in data.items():
                    if hasattr(config, key):
                        setattr(config, key, value)

        return config

    def fetch(self, url: str, strategy: Optional[FetchStrategy] = None, **kwargs) -> Dict[str, Any]:
        """
        智能抓取内容

        Args:
            url: 要抓取的URL
            strategy: 指定策略（可选，默认自动检测）
            **kwargs: 额外参数

        Returns:
            抓取结果字典
        """
        self.stats["total_fetches"] += 1

        # 自动检测策略
        if strategy is None:
            strategy = URLDetector.detect(url)

        print(f"[WebFetchPlus] URL: {url}")
        print(f"[WebFetchPlus] 策略: {strategy.value}")

        try:
            result = self._dispatch_fetch(url, strategy, **kwargs)

            if "error" not in result:
                self.stats["success"] += 1
                result["_metadata"] = {
                    "url": url,
                    "strategy": strategy.value,
                    "timestamp": datetime.now().isoformat(),
                    "success": True
                }
            else:
                self.stats["failed"] += 1
                result["_metadata"] = {
                    "url": url,
                    "strategy": strategy.value,
                    "timestamp": datetime.now().isoformat(),
                    "success": False
                }

            return result

        except Exception as e:
            self.stats["failed"] += 1
            return {
                "error": f"抓取失败: {str(e)}",
                "_metadata": {
                    "url": url,
                    "strategy": strategy.value,
                    "timestamp": datetime.now().isoformat(),
                    "success": False
                }
            }

    def _dispatch_fetch(self, url: str, strategy: FetchStrategy, **kwargs) -> Dict[str, Any]:
        """分发到具体的抓取器"""

        if strategy == FetchStrategy.TWITTER_API:
            if not self.twitter_fetcher:
                return {"error": "Twitter API未配置"}

            # 判断是推文还是用户页面
            if "/status/" in url:
                return self.twitter_fetcher.fetch_tweet(url)
            else:
                return self.twitter_fetcher.fetch_user(url)

        elif strategy == FetchStrategy.DOUYIN:
            return self.social_fetcher.fetch_douyin(url)

        elif strategy == FetchStrategy.BILIBILI:
            return self.social_fetcher.fetch_bilibili(url)

        elif strategy == FetchStrategy.XIAOHONGSHU:
            return self.social_fetcher.fetch_xiaohongshu(url)

        elif strategy == FetchStrategy.ZHIHU:
            return self.zhihu_fetcher.fetch(url)

        elif strategy == FetchStrategy.FIRECRAWL:
            return self._fetch_with_firecrawl(url, **kwargs)

        else:
            return self._fetch_generic(url, **kwargs)

    def _fetch_with_firecrawl(self, url: str, **kwargs) -> Dict[str, Any]:
        """使用Firecrawl抓取"""
        if not self.config.firecrawl_api_key:
            return self._fetch_generic(url, **kwargs)  # 降级到通用抓取

        # TODO: 实现Firecrawl API调用
        return {"message": "Firecrawl集成待完善", "url": url}

    def _fetch_generic(self, url: str, **kwargs) -> Dict[str, Any]:
        """通用HTTP抓取"""
        headers = kwargs.get("headers", {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=self.config.timeout,
                proxies={"http": self.config.proxy, "https": self.config.proxy} if self.config.proxy else None
            )
            response.raise_for_status()

            # 判断内容类型
            content_type = response.headers.get("content-type", "")

            if "json" in content_type:
                return {"content": response.json(), "type": "json"}
            elif "html" in content_type or "text" in content_type:
                return {"content": response.text[:10000], "type": "html"}  # 限制长度
            else:
                return {"content": f"二进制内容 ({len(response.content)} bytes)", "type": "binary"}

        except Exception as e:
            return {"error": f"HTTP请求失败: {str(e)}"}

    def batch_fetch(self, urls: List[str], **kwargs) -> List[Dict[str, Any]]:
        """批量抓取"""
        results = []
        for url in urls:
            result = self.fetch(url, **kwargs)
            results.append(result)
        return results

    def search_twitter(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """搜索Twitter"""
        if not self.twitter_fetcher:
            return {"error": "Twitter API未配置"}
        return self.twitter_fetcher.search_tweets(query, max_results)

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "success_rate": f"{self.stats['success'] / max(self.stats['total_fetches'], 1) * 100:.1f}%"
        }

# ==================== CLI入口 ====================
def main():
    import argparse

    parser = argparse.ArgumentParser(description="WebFetchPlus - 智能网页内容抓取工具")
    parser.add_argument("url", nargs="?", help="要抓取的URL")
    parser.add_argument("-s", "--search", help="搜索Twitter")
    parser.add_argument("-b", "--batch", help="批量抓取（文件路径）")
    parser.add_argument("--strategy", choices=["auto", "twitter", "firecrawl", "douyin", "bilibili", "zhihu"],
                       default="auto", help="指定抓取策略")
    parser.add_argument("--json", action="store_true", help="输出JSON格式")
    parser.add_argument("--stats", action="store_true", help="显示统计信息")
    parser.add_argument("--config", help="配置文件路径")

    args = parser.parse_args()

    # 初始化
    fetcher = WebFetchPlus(config_path=args.config)

    # 处理不同命令
    if args.stats:
        print(json.dumps(fetcher.get_stats(), indent=2, ensure_ascii=False))

    elif args.search:
        result = fetcher.search_twitter(args.search)
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            if "results" in result:
                for tweet in result["results"]:
                    print(f"\n@{tweet['author']['username']}: {tweet['text'][:100]}...")
                    print(f"  ❤️ {tweet['metrics']['like_count']} 🔁 {tweet['metrics']['retweet_count']}")
            else:
                print(result)

    elif args.batch:
        with open(args.batch) as f:
            urls = [line.strip() for line in f if line.strip()]
        results = fetcher.batch_fetch(urls)
        print(json.dumps(results, indent=2, ensure_ascii=False))

    elif args.url:
        # 映射策略
        strategy_map = {
            "twitter": FetchStrategy.TWITTER_API,
            "firecrawl": FetchStrategy.FIRECRAWL,
            "douyin": FetchStrategy.DOUYIN,
            "bilibili": FetchStrategy.BILIBILI,
            "zhihu": FetchStrategy.ZHIHU
        }
        strategy = strategy_map.get(args.strategy) if args.strategy != "auto" else None

        result = fetcher.fetch(args.url, strategy=strategy)

        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            if "error" in result:
                print(f"❌ 错误: {result['error']}")
            else:
                print(f"✅ 抓取成功!")
                print(json.dumps(result, indent=2, ensure_ascii=False)[:1000] + "...")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()