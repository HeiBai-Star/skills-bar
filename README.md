# Codex Skills

个人 Codex Skill 集合仓库。每个 Skill 独立存放在 `skills/` 下，可以单独安装和更新。

## Skills

| Skill | 说明 | 安装路径 |
|---|---|---|
| `decision-model-builder` | 把复杂选择转化为透明、可复核、可更新的决策模型 | `skills/decision-model-builder` |

## 仓库结构

```text
codex-skills/
├── README.md
└── skills/
    ├── decision-model-builder/
    │   ├── SKILL.md
    │   ├── agents/
    │   ├── references/
    │   └── scripts/
    └── another-skill/
        └── SKILL.md
```

## 安装

向 Codex 提供仓库和 Skill 路径：

```text
仓库：HeiBai-Star/codex-skills
路径：skills/decision-model-builder
```

私有仓库需要使用者拥有仓库权限，并已配置 GitHub 凭据。

## 添加新 Skill

将新的 Skill 文件夹放入 `skills/<skill-name>/`，确保文件夹名称与 `SKILL.md` 中的 `name` 一致，并在发布前运行 Skill 校验器。
