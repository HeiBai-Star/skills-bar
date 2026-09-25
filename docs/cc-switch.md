# CC Switch 接入规范

本仓库是独立的 Agent Skills 源，CC Switch 是安装和更新它的一种方式。

## 添加仓库

在 Skills → 仓库管理 → 添加仓库中填写：

~~~text
Owner: HeiBai-Star
Repository / Name: skills-bar
Branch: main
Subdirectory（如果界面提供）: skills
~~~

某些官方手册仍列出 Subdirectory 字段；截至 2026-09-25 核对的 main 分支实现中，SkillRepo 使用 owner、name、branch，扫描器会递归寻找 SKILL.md，因此没有子目录输入框时，直接添加仓库即可。

正式入口统一放在 skills/<name>/SKILL.md。templates 下采用 SKILL.md.tmpl，避免递归扫描把示例模板误认为已发布技能。资源必须属于同一个 Skill 目录，不能引用仓库外或相邻 Skill 的文件。

## 安装和更新

1. 添加仓库并刷新技能列表。
2. 选择要安装的 Skill，并在当前 CC Switch 版本支持的客户端中启用。
3. 仓库更新后刷新、检查更新，按需更新已安装 Skill。

CC Switch 官方手册说明它根据内容 SHA-256 检测更新。registry.json 是本仓库自己的索引，不是 CC Switch 的扫描入口，也不要求 CC Switch理解其中的版本或摘要。

文档列出 Claude Code、Codex、Gemini CLI、OpenCode、Hermes；main 分支还存在其他适配代码。具体客户端开关以你安装版本的界面为准，不能从供应商管理功能推断它支持该客户端的 Skill 分发。

## 深度链接

[每个 Skill 的链接](cc-switch-links.md) 由构建脚本生成，参数均进行 URL 编码，逻辑格式为：

~~~text
ccswitch://v1/import?resource=skill&name=<skill-name>&repo=HeiBai-Star/skills-bar&directory=skills/<skill-name>&branch=main
~~~

官方文档给出 directory 参数，但当前后端导入动作保存的是仓库配置，并不直接安装该目录。说明与按钮应使用“导入仓库”或“打开 CC Switch”，不能承诺点击后已完成安装。

GitHub Markdown 可能过滤自定义协议超链接，所以目录表指向可复制链接的说明页。已安装 CC Switch 且注册协议的设备可用完整链接唤起导入确认框；手机若没有协议处理应用，请使用 GitHub 子目录链接。

## 其他安装方式

使用 CC Switch 管理安装时，后续也在 CC Switch 中更新。使用仓库本地脚本安装时，git pull 后重新运行安装器；避免两个管理器交替覆盖同一个 Skill 目录。

配置存储和客户端同步路径由 CC Switch 管理，本仓库不自动修改 CC Switch 数据库或客户端配置。

## 核验来源

以下源码链接固定到本次核验的提交，便于区分文档与实现差异：

- [官方 Skills 手册](https://github.com/farion1231/cc-switch/blob/79bdae477104485665b4bce71a87d6969a086150/docs/user-manual/zh/3-extensions/3.3-skills.md)
- [官方深度链接手册](https://github.com/farion1231/cc-switch/blob/79bdae477104485665b4bce71a87d6969a086150/docs/user-manual/zh/5-faq/5.3-deeplink.md)
- [Skill 扫描和安装实现](https://github.com/farion1231/cc-switch/blob/79bdae477104485665b4bce71a87d6969a086150/src-tauri/src/services/skill.rs)
- [深度链接导入实现](https://github.com/farion1231/cc-switch/blob/79bdae477104485665b4bce71a87d6969a086150/src-tauri/src/deeplink/skill.rs)
