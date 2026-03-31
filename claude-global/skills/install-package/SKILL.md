---
name: install-python-package
description: 安装python工程环境依赖
allowed-tools: Bash(python:*), Read, Write
---

# A. 创建虚拟环境

首先创建一个虚拟环境（比 `python -m venv` 快得多）：

Bash

```
uv venv
```

- 激活环境 (macOS/Linux): `source .venv/bin/activate`
- 激活环境 (Windows): `.venv\Scripts\activate`

# B. 安装依赖 (`uv pip install`)

激活虚拟环境后，命令与标准 `pip` 几乎一样：

Bash

```
# 安装单个包
uv pip install pandas

# 从 requirements.txt 安装
uv pip install -r requirements.txt

# 升级包
uv pip install --upgrade pandas
```
