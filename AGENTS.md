# Skills Bar 维护约定

本仓库用于维护跨客户端 Agent Skills；新增和修改 Skill 时遵循以下约定。

- 正式技能只放在 `skills/<name>/SKILL.md`，目录名与 frontmatter 的 `name` 一致。每份正文只有一个来源，辅助资源放在同一 Skill 内。
- 保留 Agent Skills 通用字段。版本、分类和短简介放在 `metadata.version`、`metadata.category`、`metadata.short-description`，且所有 metadata 值使用字符串。
- Skill 不依赖本机绝对路径或某个客户端独有的工具。可选脚本需说明运行要求和路径定位方式；用宿主提供的 Skill 根目录定位，不依赖当前工作目录。
- `agents/openai.yaml` 仅提供可选 UI 元数据，不能承载其他宿主必需的正文。
- 使用 `python scripts/new_skill.py <name> --description "用途与触发条件" --title "显示名称" --category <category>` 创建草稿。资源目录按需添加；模板使用 `.tmpl` 后缀以避免被 CC Switch 扫描。
- `registry.json`、`skills.sh.json`、README 的目录区块由 `python scripts/build_skills.py` 生成，不手工维护。更新内容时维护语义版本，再重新生成索引。
- 提交前运行 `python scripts/validate_skills.py`、`python scripts/build_skills.py --check` 和 `python -m unittest discover -s tests -v`。涉及脚本时验证实际行为；不得声称完成未执行的客户端实测。
- 需要 ZIP 时运行 `python scripts/build_skills.py --package`。`dist/` 是生成物，不提交；CI 提供打包产物，不自动创建 GitHub Release。
- 仓库采用 MIT；导入第三方 Skill 时保留其原许可和归属，检查是否允许再分发。
- 仅在任务授权范围内提交与推送，不修改用户的客户端配置或自动替换其已安装 Skill。

CC Switch 当前的仓库发现和深度链接约定见 `docs/cc-switch.md`。不要把目录格式验证等同于所有客户端中的运行测试。
