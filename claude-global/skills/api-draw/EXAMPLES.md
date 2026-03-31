# Nanobanana 画图示例

本文档提供各种场景下的画图示例和最佳实践。

## 基础示例

### 简单描述

```bash
python scripts/nanobanana_draw.py "画一只猫"
```

### 详细描述

```bash
python scripts/nanobanana_draw.py "画一只橘色的小猫,坐在窗台上,阳光洒在它身上,温馨的午后氛围"
```

## 不同风格示例

### 写实风格

```bash
python scripts/nanobanana_draw.py "一只金毛犬的特写照片,专业摄影,柔和光线,高清画质"
```

### 卡通/动漫风格

```bash
python scripts/nanobanana_draw.py "可爱的动漫风格小女孩,大眼睛,粉色头发,穿着校服,樱花飘落的背景"
```

### 赛博朋克风格

```bash
python scripts/nanobanana_draw.py "赛博朋克风格的未来城市夜景,霓虹灯闪烁,高楼林立,紫色和蓝色主色调"
```

### 水彩风格

```bash
python scripts/nanobanana_draw.py "水彩画风格的山水画,远山若隐若现,小溪流淌,柔和的色彩"
```

### 油画风格

```bash
python scripts/nanobanana_draw.py "梵高风格的星空,旋转的云朵,明亮的星星,浓烈的色彩对比"
```

## 不同主题示例

### 人物画像

```bash
python scripts/nanobanana_draw.py "年轻女性肖像,长发,温柔的笑容,柔和的背景光,专业摄影风格"
```

### 风景画

```bash
python scripts/nanobanana_draw.py "日落时分的海滩,金色的阳光洒在海面上,几只海鸥飞过,浪漫的氛围"
```

### 建筑设计

```bash
python scripts/nanobanana_draw.py "现代简约风格的别墅外观,大落地窗,几何线条,周围是精心设计的花园"
```

### 产品设计

```bash
python scripts/nanobanana_draw.py "未来感的智能手表设计图,流线型外观,全息显示屏,科技感十足"
```

### 插画

```bash
python scripts/nanobanana_draw.py "儿童绘本风格的森林场景,小动物们在开派对,色彩明亮,充满童趣"
```

## 使用系统提示词

### 专业摄影师视角

```bash
python scripts/nanobanana_draw.py \
  --system "你是获奖无数的专业摄影师,擅长捕捉光影和情感" \
  "拍一张城市街头的黑白照片"
```

### 概念设计师视角

```bash
python scripts/nanobanana_draw.py \
  --system "你是顶尖的概念设计师,为科幻电影设计场景和道具" \
  "设计一艘星际飞船"
```

### 插画师视角

```bash
python scripts/nanobanana_draw.py \
  --system "你是专业插画师,擅长创作细节丰富的手绘插画" \
  "画一个魔法森林的场景"
```

## 管道输入示例

### 从文件读取

```bash
cat prompt.txt | python scripts/nanobanana_draw.py
```

### 结合其他命令

```bash
echo "画一只猫" | python scripts/nanobanana_draw.py
```

## 保存和处理输出

### 保存完整 JSON 响应

```bash
python scripts/nanobanana_draw.py \
  "画一只狗" \
  --output result.json
```

### 打印 JSON 到控制台

```bash
python scripts/nanobanana_draw.py \
  "画一只狗" \
  --print-json
```

## 在 Claude Code 中使用

### 直接对话

```
用户: 画一只可爱的柴犬
Claude: [调用 nanobanana-draw skill 生成图片]
```

### 复杂需求

```
用户: 帮我设计一个现代风格的咖啡厅logo,简约,用咖啡色和米色
Claude: [理解需求后调用 skill,传入详细的 prompt]
```

### 迭代优化

```
用户: 画一只猫
Claude: [生成第一版]
用户: 能不能改成橘色的,要在草地上
Claude: [调整 prompt 重新生成]
```

## 最佳实践

### 1. 明确主体

```bash
# 好
"一只金毛犬坐在草地上"

# 不好
"一个场景"
```

### 2. 添加细节

```bash
# 好
"一只橘色的小猫,绿色的眼睛,蹲在红色的沙发上,温暖的室内光线"

# 不好
"一只猫"
```

### 3. 指定风格

```bash
# 好
"水彩画风格的花园,柔和的色彩,梦幻的氛围"

# 不好
"一个花园"
```

### 4. 描述氛围

```bash
# 好
"日落时分的海边,温暖的橘色天空,宁静祥和的氛围"

# 不好
"海边"
```

## 提示词模板

### 人物类

```
[主体描述] + [外貌特征] + [服装/造型] + [姿态/动作] + [背景环境] + [风格] + [光线/氛围]

例: 年轻女性,长发飘逸,穿着白色连衣裙,站在花田中,动漫风格,柔和的阳光
```

### 场景类

```
[场景类型] + [时间] + [天气/季节] + [主要元素] + [色调] + [风格] + [氛围]

例: 城市街道,黄昏时分,下着小雨,霓虹灯闪烁,蓝紫色调,赛博朋克风格,神秘氛围
```

### 物品类

```
[物品名称] + [材质] + [颜色] + [形状/设计] + [用途/场景] + [风格] + [视角]

例: 智能手表,金属材质,黑色,圆形表盘,科技感设计,极简风格,45度角俯视
```

## 常见问题的解决方案

### 生成的图片不够详细

增加描述的细节:
```bash
# 改进前
"一个房间"

# 改进后
"温馨的卧室,米色墙壁,大床上铺着白色床单,窗帘半开透进柔和的阳光,木质地板,一盆绿植放在窗台"
```

### 风格不符合预期

明确指定风格:
```bash
# 改进前
"一只猫"

# 改进后
"一只猫,吉卜力工作室动画风格,柔和的色彩,手绘质感"
```

### 氛围不够强烈

增加情绪和氛围描述:
```bash
# 改进前
"一个森林"

# 改进后
"神秘的森林,薄雾弥漫,阳光透过树叶洒下斑驳的光影,幽静而深邃的氛围"
```
