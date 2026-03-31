---
name: api-deploy-obsidian
description: Use when publishing an Obsidian plugin to the community plugin store, creating GitHub Releases for Obsidian plugins, or submitting PRs to obsidianmd/obsidian-releases
---

# Obsidian Plugin Store 发布

将 Obsidian 插件发布到社区插件商店。覆盖从预检到 PR 提交的完整流程。

## 前提条件

| 条件 | 说明 |
|------|------|
| GitHub 仓库 | 公开仓库，包含源码 |
| manifest.json | 插件根目录，包含 id/name/version/minAppVersion/description/author |
| README.md | 仓库根目录 |
| LICENSE | 仓库根目录（推荐 MIT） |
| GitHub Release | tag 名 = 版本号（**不带 `v` 前缀**），附带 main.js + manifest.json + styles.css |

## 关键陷阱

- **Release tag 不带 `v`**：必须是 `1.0.0` 而非 `v1.0.0`，Obsidian 按此匹配版本
- **manifest.json 的 id**：全小写，用连字符，与 community-plugins.json 中的 id 一致
- **minAppVersion**：设为 `0.15.0` 以覆盖大多数用户
- **Release 附件**：必须包含 main.js、manifest.json，styles.css 可选
- **PR 必须用官方模板**：必须使用 `plugin.md` 模板，否则自动验证会失败

## 完整流程

### 1. 预检

```bash
# 检查必需文件
cat manifest.json   # 确认 id, name, version, minAppVersion, description, author
ls README.md LICENSE

# 构建
npm run build
ls main.js          # 确认产物存在
```

### 2. 创建 GitHub Release

```bash
VERSION=$(python3 -c "import json; print(json.load(open('manifest.json'))['version'])")

gh release create "$VERSION" \
  main.js \
  manifest.json \
  styles.css \
  --title "$VERSION" \
  --notes "Release $VERSION"
```

### 3. 提交到社区插件商店

```bash
# 读取插件信息
PLUGIN_ID=$(python3 -c "import json; print(json.load(open('manifest.json'))['id'])")
PLUGIN_NAME=$(python3 -c "import json; print(json.load(open('manifest.json'))['name'])")
PLUGIN_DESC=$(python3 -c "import json; print(json.load(open('manifest.json'))['description'])")
PLUGIN_AUTHOR=$(python3 -c "import json; print(json.load(open('manifest.json'))['author'])")
REPO=$(gh repo view --json nameWithOwner -q '.nameWithOwner')

# Fork obsidian-releases（幂等）
gh repo fork obsidianmd/obsidian-releases --clone=false

# 获取 community-plugins.json 的 SHA（用于 API 提交）
SHA=$(gh api repos/Leoyishou/obsidian-releases/contents/community-plugins.json --jq '.sha')

# 下载、修改、上传
gh api repos/obsidianmd/obsidian-releases/contents/community-plugins.json --jq '.content' \
  | base64 -d > /tmp/community-plugins.json

python3 -c "
import json
with open('/tmp/community-plugins.json') as f:
    plugins = json.load(f)
new_entry = {
    'id': '$PLUGIN_ID',
    'name': '$PLUGIN_NAME',
    'author': '$PLUGIN_AUTHOR',
    'description': '$PLUGIN_DESC',
    'repo': '$REPO'
}
plugins.append(new_entry)
with open('/tmp/community-plugins.json', 'w') as f:
    json.dump(plugins, f, indent='\t', ensure_ascii=False)
    f.write('\n')
"

# 推送到 fork
CONTENT=$(base64 -i /tmp/community-plugins.json)
gh api repos/Leoyishou/obsidian-releases/contents/community-plugins.json \
  -X PUT \
  -f message="Add $PLUGIN_ID plugin" \
  -f content="$CONTENT" \
  -f sha="$SHA" \
  -f branch="master"

# 创建 PR（必须使用官方 plugin.md 模板，否则自动验证失败）
gh pr create \
  --repo obsidianmd/obsidian-releases \
  --head Leoyishou:master \
  --base master \
  --title "Add $PLUGIN_NAME plugin" \
  --body "$(cat <<EOF
# I am submitting a new Community Plugin

- [x] I attest that I have done my best to deliver a high-quality plugin, am proud of the code I have written, and would recommend it to others. I commit to maintaining the plugin and being responsive to bug reports. If I am no longer able to maintain it, I will make reasonable efforts to find a successor maintainer or withdraw the plugin from the directory.

## Repo URL

Link to my plugin: https://github.com/$REPO

## Release Checklist
- [x] I have tested the plugin on
  - [x]  macOS
  - [ ]  Windows
  - [ ]  Linux
  - [ ]  Android _(if applicable)_
  - [ ]  iOS _(if applicable)_
- [x] My GitHub release contains all required files (as individual files, not just in the source.zip / source.tar.gz)
  - [x] \`main.js\`
  - [x] \`manifest.json\`
  - [x] \`styles.css\` _(optional)_
- [x] GitHub release name matches the exact version number specified in my manifest.json (_**Note:** Use the exact version number, don't include a prefix \`v\`_)
- [x] The \`id\` in my \`manifest.json\` matches the \`id\` in the \`community-plugins.json\` file.
- [x] My README.md describes the plugin's purpose and provides clear usage instructions.
- [x] I have read the developer policies at https://docs.obsidian.md/Developer+policies, and have assessed my plugin's adherence to these policies.
- [x] I have read the tips in https://docs.obsidian.md/Plugins/Releasing/Plugin+guidelines and have self-reviewed my plugin to avoid these common pitfalls.
- [x] I have added a license in the LICENSE file.
- [x] My project respects and is compatible with the original license of any code from other plugins that I'm using.
      I have given proper attribution to these other projects in my \`README.md\`.
EOF
)"
```

### 4. 审核后

Obsidian 团队审核通常需要 1-2 周。通过后插件会出现在 Settings > Community plugins。

## 版本更新流程（后续版本）

只需更新版本号并创建新 Release，无需再提交 PR：

```bash
# 1. 更新 manifest.json 和 package.json 中的版本号
# 2. 构建
npm run build
# 3. 提交并推送
git add -A && git commit -m "bump to X.Y.Z" && git push
# 4. 创建 Release
gh release create "X.Y.Z" main.js manifest.json styles.css --title "X.Y.Z"
```

## 本地安装测试

```bash
VAULT_DIR="$HOME/path-to-vault/.obsidian/plugins"
PLUGIN_ID=$(python3 -c "import json; print(json.load(open('manifest.json'))['id'])")
mkdir -p "$VAULT_DIR/$PLUGIN_ID"
cp main.js manifest.json styles.css "$VAULT_DIR/$PLUGIN_ID/"
# 重启 Obsidian 或在设置中重新启用插件
```
