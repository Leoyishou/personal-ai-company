---
name: 3b1b-video
description: |
  根据用户给出的命题/概念，生成 3Blue1Brown 风格的数学动画视频。
  端到端流程：理解命题 → 设计叙事 → 生成 Manim 代码 → 渲染视频。
  使用 Manim Community Edition (from manim import *)。

  触发条件：用户要求"画个视频讲讲"、"用动画解释"、"3b1b 风格"、
  "白板动画"、"可视化讲解"等。

  画幅规则：
  - 用户提到 "xhs"、"小红书"、"竖屏"、"抖音"、"短视频" → 9:16 竖屏（1080x1920）
  - 其他情况 → 默认 16:9 横屏（1920x1080）
---

## 画幅配置

### 竖屏模式（9:16，用于小红书/抖音/短视频）

当用户提到 xhs / 小红书 / 竖屏时，自动使用竖屏配置：

```python
from manim import *

# 在文件顶部设置竖屏
config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 9
config.frame_height = 16
```

**竖屏布局注意事项**：
- 所有内容纵向排列（`arrange(DOWN)` 为主）
- 标题字号可以更大（60-72）
- 正文字号 28-36（竖屏可视面积窄，字要大）
- 避免横向并排超过 2 列
- 元素靠中间放置，左右留边距 ≥ 0.8
- 每屏信息量减少（竖屏高度大但宽度有限）
- 渲染命令加 `-r 1080,1920`

**竖屏渲染命令**：
```bash
manim -r 1080,1920 -ql scene.py ClassName    # 预览
manim -r 1080,1920 -qm scene.py ClassName    # 中等质量
```

### 横屏模式（16:9，默认）

标准设置，不需要额外配置。

---

## 工作流程

### Phase 1: 理解命题

1. **分析用户给出的命题**
   - 核心概念是什么？
   - 有哪些直觉上不明显的点？
   - "aha moment" 在哪里？

2. **如有需要，搜索补充知识**
   - 用 WebSearch 了解概念的准确定义
   - 找到最佳的可视化角度

3. **确定叙事模式**（选一个或组合）：
   - **Mystery → Resolution**: 先抛出悬念，再揭示答案
   - **Build Up → Payoff**: 从简单积木搭建到惊人结果
   - **Two Perspectives → Unity**: 两种视角最终统一
   - **Specific → General**: 从具体例子推广到一般原理

### Phase 2: 设计场景

规划 3-6 个场景，每个场景包含：
- 目的（这个场景让观众理解什么）
- 视觉元素（形状、公式、图表）
- 动画序列（如何逐步展现）
- 过渡（如何连接到下一场景）

### Phase 3: 生成代码

在用户项目目录下创建 `.py` 文件，遵循以下规范：

#### 文件结构
```python
from manim import *

class TopicExplainer(Scene):
    def construct(self):
        # Scene 1: Hook / Opening
        self.scene_hook()

        # Scene 2-N: Main content
        self.scene_core_concept()
        self.scene_build_intuition()
        self.scene_aha_moment()

        # Final: Summary
        self.scene_summary()

    def scene_hook(self):
        """开场：抛出问题或展示令人好奇的结果"""
        ...

    def scene_core_concept(self):
        """核心概念的可视化"""
        ...
```

#### 3b1b 视觉风格规范

**颜色方案**（暗背景 + 高对比）：
```python
# 主要颜色
PRIMARY = BLUE        # 主要对象
SECONDARY = YELLOW    # 次要/对比对象
HIGHLIGHT = GREEN     # 强调/结论
WARNING = RED         # 错误/注意
ACCENT = TEAL         # 辅助元素

# 文字颜色
TEXT_COLOR = WHITE
SUBTLE_TEXT = GREY_B
```

**字体大小规范**：
```python
TITLE_SIZE = 48       # 标题
SUBTITLE_SIZE = 36    # 副标题
BODY_SIZE = 28        # 正文说明
LABEL_SIZE = 24       # 标签
SMALL_SIZE = 20       # 小字注释
```

**动画节奏**：
```python
# 标准节奏
self.wait(0.5)        # 短暂停顿
self.wait(1)          # 正常停顿（让观众看清）
self.wait(2)          # 重要信息停顿
self.wait(3)          # 关键 insight 停顿

# 动画时长
run_time=0.5          # 快速动画（辅助元素）
run_time=1            # 标准动画
run_time=1.5          # 重要动画
run_time=2            # 关键变换
```

#### 核心动画模式

**1. 渐进式揭示（Progressive Revelation）**
```python
# 不要一次性展示所有内容
# 好：逐步构建
self.play(Write(title))
self.wait(0.5)
self.play(FadeIn(subtitle, shift=UP * 0.3))
self.wait(1)
self.play(Create(diagram))

# 坏：一次全出现
self.add(title, subtitle, diagram)
```

**2. 变换而非替换（Transform, Don't Replace）**
```python
# 好：对象变换保持视觉连续性
self.play(Transform(circle, square))

# 或者用 ReplacementTransform 当需要保留引用时
self.play(ReplacementTransform(old_eq, new_eq))

# 坏：直接移除再添加
self.remove(circle)
self.add(square)
```

**3. 聚焦引导（Focus Guidance）**
```python
# 用高亮/缩放引导注意力
self.play(
    target.animate.set_color(YELLOW).scale(1.2),
    *[other.animate.set_opacity(0.3) for other in others]
)
self.wait(1)
# 恢复
self.play(
    target.animate.set_color(WHITE).scale(1/1.2),
    *[other.animate.set_opacity(1) for other in others]
)
```

**4. 场景过渡（Scene Transitions）**
```python
# 方式 A：淡出所有 → 淡入新内容
self.play(*[FadeOut(mob) for mob in self.mobjects])

# 方式 B：旧内容缩小移到角落
self.play(old_group.animate.scale(0.3).to_corner(UL))

# 方式 C：旧内容向一侧滑出
self.play(FadeOut(old_group, shift=LEFT * 2))
```

**5. 公式动画**
```python
# 写公式
formula = MathTex(r"E = mc^2")
self.play(Write(formula))

# 公式变换（对齐相同部分）
eq1 = MathTex(r"a^2 + b^2", r"=", r"c^2")
eq2 = MathTex(r"c", r"=", r"\sqrt{a^2 + b^2}")
self.play(TransformMatchingTex(eq1, eq2))

# 框选强调
box = SurroundingRectangle(formula, color=YELLOW, buff=0.2)
self.play(Create(box))
```

**6. 图表与坐标系**
```python
axes = Axes(
    x_range=[-3, 3, 1],
    y_range=[-2, 2, 1],
    x_length=7,
    y_length=4,
    axis_config={"include_numbers": True}
)
labels = axes.get_axis_labels(x_label="x", y_label="y")

graph = axes.plot(lambda x: x**2, color=BLUE)
graph_label = axes.get_graph_label(graph, label="x^2")

self.play(Create(axes), Write(labels))
self.play(Create(graph), Write(graph_label))
```

**7. 对比展示**
```python
# 左右对比
left_group = VGroup(left_title, left_content).arrange(DOWN)
right_group = VGroup(right_title, right_content).arrange(DOWN)
comparison = VGroup(left_group, right_group).arrange(RIGHT, buff=2)

divider = DashedLine(UP * 2, DOWN * 2, color=GREY)
divider.move_to(comparison.get_center())
```

#### 结构模板

**短视频（3-5 场景，~1分钟）**：
1. Hook: 提出问题（5-10s）
2. Setup: 建立基础（15-20s）
3. Core: 核心推导/演示（20-30s）
4. Aha: 揭示关键 insight（10-15s）
5. Summary: 总结（5-10s）

**中等视频（5-8 场景，~2-3分钟）**：
1. Hook: 吸引注意力
2. Context: 为什么这个问题重要
3. Foundation: 必要的基础知识
4. Exploration: 探索和尝试
5. Key Insight: 核心突破
6. Proof/Demonstration: 严格证明或完整演示
7. Implications: 这意味着什么
8. Summary: 回顾和升华

### Phase 4: 渲染视频

```bash
# 低质量预览（快速检查）
manim -pql scene.py ClassName

# 中等质量（最终预览）
manim -pqm scene.py ClassName

# 高质量输出
manim -pqh scene.py ClassName
```

渲染完成后告知用户视频路径。

## 注意事项

0. **首帧不能黑屏** - 社媒平台取第一帧做封面，第一个 Scene 必须用 `self.add(title)` 让标题立即显示，再做动画效果，不能从空白开始 `Write()`
1. **不要过度复杂** - 每个场景聚焦一个概念
2. **代码可运行** - 确保生成的代码无语法错误，可直接渲染
3. **数学准确** - LaTeX 公式必须正确
4. **视觉清晰** - 避免屏幕太拥挤，留白很重要
5. **节奏适当** - wait() 给观众消化时间
6. **颜色一致** - 同一概念在整个视频中用同一颜色
7. **先低质量预览** - 用 `-ql` 确认无误后再高质量渲染

## 输出规范

- 文件命名: `{topic}_explainer.py`
- 类命名: `{Topic}Explainer`
- 默认渲染质量: medium (720p30)
- 输出目录: `./media/videos/`
