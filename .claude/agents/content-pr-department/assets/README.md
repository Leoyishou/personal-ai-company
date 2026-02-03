# 内容与公关部素材库

## 快速使用

```bash
# 素材库路径
ASSETS_DIR=~/.claude/agents/content-pr-department/assets

# 复制 BGM 到项目
cp $ASSETS_DIR/audio/bgm/tech/xxx.mp3 ./public/audio/

# 查看所有素材
ls -la $ASSETS_DIR/audio/bgm/
```

## 添加新素材

1. 将文件放入对应目录
2. 更新 `index.json` 索引
3. 命名规范：`{描述}_{时长}_{来源}.{格式}`
   - 例：`upbeat_energy_30s_pixabay.mp3`

## 素材来源推荐

### BGM（免费可商用）
- [Pixabay Music](https://pixabay.com/music/)
- [Mixkit](https://mixkit.co/free-stock-music/)
- [Uppbeat](https://uppbeat.io/)

### 音效
- [Pixabay Sound Effects](https://pixabay.com/sound-effects/)
- [Freesound](https://freesound.org/)

### 字体
- [Google Fonts](https://fonts.google.com/)
- [字体天下](https://www.fonts.net.cn/)（注意授权）

## 版权说明

- 所有素材需确保可商用
- 记录来源和授权信息
- 优先使用 CC0 或免版税素材
