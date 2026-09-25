# Skills Bar

面向多种 AI 编程助手的 Agent Skills 仓库。每个 Skill 只维护一份标准源文件：

```text
skills/<skill-name>/SKILL.md
```

仓库遵循 [Agent Skills 开放规范](https://agentskills.io/specification)，不为不同客户端复制多份正文。客户端专用文件只能作为可选增强；例如 `agents/openai.yaml` 会改善 Codex 中的显示，但不影响其他宿主读取同一个 Skill。

## 可用 Skills

| Skill | 说明 | 可直接粘贴的子目录 URL |
|---|---|---|
| `decision-model-builder` | 把复杂选择转化为透明、可复核、可更新的决策模型 | <https://github.com/HeiBai-Star/skills-bar/tree/main/skills/decision-model-builder> |

如果客户端提示“输入仓库 URL，并自动读取 `SKILL.md`”，请粘贴表格中的**子目录 URL**，不要只粘贴仓库首页。这样一个仓库可以继续容纳多个 Skill。

## 兼容性

| 客户端 | 兼容方式 | 本仓库安装器使用的用户目录 |
|---|---|---|
| Codex | 原生 Agent Skills；支持 `SKILL.md` 及可选 `agents/openai.yaml` | `~/.agents/skills` |
| Claude Code | 原生 Agent Skills | `~/.claude/skills` |
| Gemini CLI | 原生 Agent Skills；同时识别共享别名目录 | `~/.agents/skills` |
| OpenCode | 原生 Agent Skills；识别共享目录 | `~/.agents/skills` |
| Grok Build | 原生 Skills / Claude Code Skills 兼容层 | `~/.agents/skills` |
| Hermes Agent | 原生 Agent Skills | `~/.hermes/skills` |
| 其他宿主 | 只要支持 Agent Skills 规范，即可指向对应 Skill 子目录 | 由宿主决定 |

这里的 “Grok” 特指支持本地 Skills 的 **Grok Build**。普通 Grok 网页或手机聊天应用目前不提供本地 Skill 目录；也可以在 OpenCode 或 Hermes 中选用 Grok 模型，再加载本仓库的 Skill。

相关官方文档：

- [Codex](https://learn.chatgpt.com/docs/build-skills)
- [Claude Code](https://code.claude.com/docs/en/skills)
- [Gemini CLI](https://geminicli.com/docs/cli/skills/)
- [OpenCode](https://opencode.ai/docs/skills/)
- [Grok Build](https://docs.x.ai/build/features/skills-plugins-marketplaces)
- [Hermes Agent](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills)

## 安装

### 方式一：让客户端从 GitHub 安装

向支持 GitHub URL 的客户端提供：

```text
https://github.com/HeiBai-Star/skills-bar/tree/main/skills/decision-model-builder
```

Gemini CLI 也可以直接安装仓库中的子目录：

```bash
gemini skills install https://github.com/HeiBai-Star/skills-bar.git --path skills/decision-model-builder
```

Hermes Agent 可以安装单个 Skill，或把整个仓库加入 tap：

```bash
hermes skills install HeiBai-Star/skills-bar/skills/decision-model-builder
hermes skills tap add HeiBai-Star/skills-bar
```

### 方式二：克隆后安装到本机

Windows PowerShell：

```powershell
git clone https://github.com/HeiBai-Star/skills-bar.git
Set-Location skills-bar
.\scripts\install.ps1 -Skill decision-model-builder -Target all
```

macOS / Linux：

```bash
git clone https://github.com/HeiBai-Star/skills-bar.git
cd skills-bar
./scripts/install.sh decision-model-builder all
```

`all` 只写入三个不重复的目录：`~/.agents/skills`、`~/.claude/skills` 和 `~/.hermes/skills`。也可以把目标改成 `codex`、`claude`、`gemini`、`grok`、`opencode` 或 `hermes`。如果目标已存在，显式添加 `-Force`（PowerShell）或 `--force`（shell）才会替换。

## 仓库结构

```text
skills-bar/
├── .github/workflows/validate-skills.yml
├── scripts/
│   ├── install.ps1
│   ├── install.sh
│   └── validate_skills.py
├── skills/
│   └── decision-model-builder/
│       ├── SKILL.md
│       ├── agents/                 # 可选的 Codex UI 元数据
│       ├── references/
│       └── scripts/
└── skills.sh.json
```

## 添加新 Skill

1. 将完整目录放入 `skills/<skill-name>/`。
2. 确保目录名与 `SKILL.md` frontmatter 中的 `name` 一致。
3. 只在该目录维护一份正文；不要为不同客户端复制 `SKILL.md`。
4. 运行 `python scripts/validate_skills.py` 后再提交。GitHub Actions 也会在 Windows、macOS 和 Linux 上自动检查。
