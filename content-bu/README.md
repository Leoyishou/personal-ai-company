# 内容事业部 - 媒体杠杆

> 将灵感变为社媒内容，提高互联网影响力

## 一、核心信息

| 字段 | 值 |
|------|-----|
| Linear Team | C (内容事业部) |
| Initiative | 媒体杠杆 |
| 启动命令 | `cd ~/usr/pac/content-bu && claude --dangerously-skip-permissions` |

## 二、内容系列（Linear Project）

| 系列 | 说明 | 状态 |
|------|------|------|
| n张图系列 | 图文科普对比 | active |
| 人物语录系列 | 名人名言配图 | active |
| 技术科普系列 | 编程/AI 科普 | active |
| 知乎高赞系列 | 知乎高赞回答改编小红书图文 | active |
| 随机探索系列 | 兜底，不属于其他系列 | active |
| 小红书封面系统 | 工具类 | active |

## 三、标签流程

```
灵感 --> 做图/文案 --> 策划 --> 发布 --> 后评估
                        |
                        +--> 废弃/搁置（不发也没关系）
```

| 标签 | 说明 |
|------|------|
| 灵感 | 选题、素材收集 |
| 做图 | 封面图、配图制作 |
| 文案 | 文案撰写 |
| 策划 | 已制作但未决定是否发布 |
| 发布 | 已发布到平台 |
| 后评估 | 数据复盘、优化 |

## 四、目录结构

```
content-bu/
├── .claude/               # Claude Code 项目配置 + skills
├── hooks/                 # 项目级 hooks
├── inbox/                 # 临时项目
└── output/                # 内容产出（按日期组织）
    └── 20260213-xhs-zhihu-hot/   # 示例：知乎高赞系列
        ├── 文案.md
        ├── post1-money/
        ├── post2-traits/
        └── post3-ai-class/
```

## 五、自动化

### 5.1 Session 结束自动上报

全局 `SessionEnd` hook --> PMO Agent 分析 --> 创建 Linear Issue

PMO 根据工具调用自动推断标签：
- `api-draw` / `nanobanana-draw` --> 做图
- `xiaohongshu` / `x-post` --> 发布
- 有产出但未发布 --> 策划

### 5.2 小红书发布自动追踪

发布成功 --> 立即创建 Issue --> 3 分钟后回填笔记链接 + 初始数据

### 5.3 新系列检测

批量同主题产出 --> PMO 建议创建新 Project（而非塞进「随机探索系列」）

## 六、常用 Skills

| Skill | 用途 |
|-------|------|
| `api-draw` | AI 生图 + 后处理 |
| `xiaohongshu` | 发布到小红书 |
| `x-post` | 发推文 |
| `social-media` | 统一入口 |
| `video` | 视频制作 |
| `nanobanana-draw` | Gemini 生图 |
