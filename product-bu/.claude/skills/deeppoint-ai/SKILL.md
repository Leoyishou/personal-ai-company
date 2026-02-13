---
name: deeppoint-ai
description: Use when discovering user pain points from social media (Douyin), running pain point clustering analysis, or generating AI product solutions from user feedback
---

# DeepPoint AI - Pain Point Discovery

From social media data to actionable product insights. Collects Douyin comments by keyword, clusters them semantically (DBSCAN + embeddings), and generates AI product solutions.

**Source**: https://github.com/weiyf2/deeppoint-ai

## Quick Reference

| Item | Value |
|------|-------|
| Repo | `~/usr/pac/product-bu/inbox/deeppoint-ai` |
| Stack | Next.js 15 + Python 3.10+ + GLM-4 |
| Port | `3000` |
| API Key | GLM API from https://open.bigmodel.cn/ |

## Setup (First Time)

```bash
# 1. Clone
cd ~/usr/pac/product-bu/inbox
git clone https://github.com/weiyf2/deeppoint-ai.git
cd deeppoint-ai

# 2. Install dependencies
npm install
pip install -r requirements.txt
playwright install chromium

# 3. Configure .env.local
cat > .env.local << 'EOF'
GLM_API_KEY=<from secrets.env GLM_API_KEY>
GLM_MODEL_NAME=glm-4
GLM_EMBEDDING_MODEL=embedding-3
HEADLESS=true
EOF

# 4. Run
npm run dev
```

Load GLM key from `~/.claude/secrets.env` if available (look for `GLM_API_KEY`).

## Usage

1. Open http://localhost:3000
2. Enter keywords (e.g. "英语学习", "AI 工具")
3. System crawls Douyin videos + comments for that keyword
4. Semantic clustering groups similar pain points (DBSCAN)
5. AI analyzes: surface issues -> root causes -> user scenarios -> emotional intensity
6. Generates product solutions with MVP plan

## Data Quality Tiers

| Tier | Data Points | Reliability |
|------|-------------|-------------|
| Exploratory | <50 | Low |
| Preliminary | 50-200 | Medium |
| Reliable | >=200 | High |

## Key Directories

```
src/app/[locale]/     # i18n routes (zh/en)
src/components/       # UI components
lib/services/         # Job management, clustering, AI analysis
lib/crawlers/         # Douyin crawler (Playwright-based)
lib/semantic_clustering.py  # Python DBSCAN clustering
```

## Notes

- Douyin crawler requires QR code login for new sessions
- Xiaohongshu crawler suspended (account ban risk)
- Douyin crawler code (`lib/crawlers/douyin_new/`) is NON-COMMERCIAL LICENSE only
- Export results as CSV for further analysis
