# Skills Bar

个人跨客户端 Agent Skills 仓库：一个 Skill 一个独立目录，一份正文，同时供 Codex、Claude Code、Gemini CLI、OpenCode、Grok Build、Hermes Agent 等支持 [Agent Skills](https://agentskills.io/specification) 的客户端使用。

## 可用 Skills

<!-- skills-catalog:start -->

| Skill | 简介 | 版本 | 安装入口 |
|---|---|---|---|
| [decision-model-builder](skills/decision-model-builder/SKILL.md) | 把复杂选择转化为透明、可复核、可更新的决策模型 | 1.0.0 | [GitHub / 手机](https://github.com/HeiBai-Star/skills-bar/tree/main/skills/decision-model-builder) · [CC Switch](docs/cc-switch-links.md#decision-model-builder) |

<!-- skills-catalog:end -->

手机或其他支持 GitHub URL 的客户端，请使用表中的 **GitHub / 手机** 子目录链接。请安装完整 Skill 目录；只下载 SKILL.md 的导入器可能缺少 references 和 scripts，届时需要补齐资源。

## 使用 CC Switch

在 Skills → 仓库管理中添加：

| 字段 | 值 |
|---|---|
| Owner | HeiBai-Star |
| Repository / Name | skills-bar |
| Branch | main |
| Subdirectory（如果该版本显示） | skills |

添加后刷新列表，找到 Skill 并选择安装、启用的客户端。后续更新仓库后，再刷新并检查更新。

完整说明见 [CC Switch 接入规范](docs/cc-switch.md)，包括 [可复制的导入链接](docs/cc-switch-links.md)。深度链接用于导入仓库，之后仍需选择安装；registry.json 不是 CC Switch 的必需文件。

## 直接安装

Gemini CLI：

~~~bash
gemini skills install https://github.com/HeiBai-Star/skills-bar.git --path skills/decision-model-builder
~~~

Hermes Agent，安装单个 Skill 或订阅整个仓库：

~~~bash
hermes skills install HeiBai-Star/skills-bar/skills/decision-model-builder
hermes skills tap add HeiBai-Star/skills-bar
~~~

也可克隆仓库，然后运行本地安装器。Windows PowerShell：

~~~powershell
git clone https://github.com/HeiBai-Star/skills-bar.git
Set-Location skills-bar
./scripts/install.ps1 -Skill decision-model-builder -Target all
~~~

macOS / Linux：

~~~bash
git clone https://github.com/HeiBai-Star/skills-bar.git
cd skills-bar
sh scripts/install.sh decision-model-builder all
~~~

目标可选 all、codex、claude、gemini、grok、opencode、hermes。all 写入下面三个不重复的目录。安装器默认拒绝覆盖；明确使用 -Force 或 --force 才会替换已有目录。后续更新先 git pull，再重新安装所需 Skill；已有个人修改请自行保留。

## 客户端适配

| 客户端 | 本地安装器使用的目录 | 官方依据 |
|---|---|---|
| Codex | ~/.agents/skills | [Skills](https://learn.chatgpt.com/docs/build-skills) |
| Claude Code | ~/.claude/skills | [Skills](https://code.claude.com/docs/en/skills) |
| Gemini CLI | ~/.agents/skills | [Agent Skills](https://geminicli.com/docs/cli/skills/) |
| OpenCode | ~/.agents/skills | [Skills](https://opencode.ai/docs/skills/) |
| Grok Build | ~/.agents/skills | [Skills](https://docs.x.ai/build/features/skills-plugins-marketplaces) |
| Hermes Agent | ~/.hermes/skills | [Skills System](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills) |

适配依据为上述宿主的 Skill 格式和发现路径。CI 验证文件、安装脚本和打包，不等同于在所有客户端执行真实任务的验收。宿主版本、工具权限和依赖仍会影响运行。

agents/openai.yaml 是可选的 Codex UI 元数据，通用指令仍在 SKILL.md 中。这里的 Grok 指 **Grok Build**；普通聊天网页或手机应用能否导入 Skill，取决于该应用自身提供的功能。其他支持 Agent Skills 的宿主可安装同一完整目录；本仓库没有为 OpenClaw 提供专用安装目标。

## 仓库结构

~~~text
skills-bar/
├── skills/decision-model-builder/   # 唯一的正式 Skill 源
│   ├── SKILL.md
│   ├── agents/openai.yaml
│   ├── references/
│   └── scripts/
├── templates/skill-template/        # .tmpl 文件，避免被误发现
├── scripts/                        # 新建、校验、索引、打包、安装
├── tests/                          # 格式与打包行为测试
├── docs/                           # CC Switch 接入与自动生成的链接
├── registry.json                   # 自动生成的结构化索引
├── skills.sh.json                  # 自动生成的分类
├── .github/workflows/validate-skills.yml
├── AGENTS.md                       # 后续维护此仓库的统一约定
└── LICENSE
~~~

## 新增与更新 Skill

维护工具需要 Python 3.10+、Git 和 PyYAML；使用 Skill 本身不需要安装这组开发依赖。

~~~bash
python -m pip install -r requirements-dev.txt
python scripts/new_skill.py learning-assistant --title "学习助手" --description "围绕学习目标制定练习、复习与评估方案，适用于系统学习和阶段复盘。" --category learning
~~~

新建命令只生成草稿。完成正文、删除所有 TODO 占位符，根据实际需要添加 references、scripts、assets，并在 SKILL.md 中链接需要的资源。模板不创建空资源目录。

版本、分类、短简介只在 SKILL.md 的 metadata 中维护；正文或辅助文件有变更时更新 version。参考现有 Skill 的格式。

~~~bash
python scripts/validate_skills.py
python scripts/build_skills.py
python scripts/build_skills.py --check
python -m unittest discover -s tests -v
~~~

build_skills.py 自动更新 registry.json、skills.sh.json、README 目录和 CC Switch 链接。--check 只检查是否过期，不写入文件。检查通过后，将 Skill 和生成文件一并提交、推送，再到 CC Switch 刷新。

## 打包与自动检查

~~~bash
python scripts/build_skills.py --package
~~~

dist/ 中会生成独立 Skill ZIP 和 checksums.json。每个 ZIP 包含完整 Skill 目录及许可证，可复现生成，不加入 Git。GitHub Actions 在 Windows、macOS、Linux 上检查，并上传三个平台的 ZIP 作为工作流产物；目前不自动创建 GitHub Release。

校验覆盖 YAML 类型与重复键、名称、版本、分类、相对文件链接、Python 语法、模板残留及常见密钥格式。密钥检查是本地规则匹配，不能保证识别所有敏感信息，且不会把匹配值输出到日志。

registry.json 的 content_sha256 是本仓库对排序后的相对路径和文件 SHA-256 清单计算的摘要，不是 CC Switch 内部哈希，也不是数字签名。README 和索引不参与 Skill 摘要；辅助文件的变化会改变摘要。跨系统 Git 检出统一使用 LF。

本仓库原创内容采用 [MIT License](LICENSE)。第三方内容需保留其各自许可及归属。
