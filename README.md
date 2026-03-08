# OpenClaw Skills

我自定义的 OpenClaw Agent Skills 集合。

## 什么是 Skill

Skill 是 OpenClaw 的扩展模块，为 AI Agent 提供特定领域的能力和工作流。

## 已收录 Skills

| Skill | 描述 | 版本 |
|-------|------|------|
| [airport-area-mapper](./airport-area-mapper/) | 机场/地点面积测量：Excel → 高德截图 → 面积测量 → 结果导出 | 1.0.0 |

## 安装方法

```bash
# 通过 ClawHub 安装（如果已发布）
openclaw skill install airport-area-mapper

# 或者手动安装
# 1. 下载 .skill 文件
# 2. 放置到 ~/.openclaw/skills/ 目录
```

## 目录结构

```
.
├── README.md
├── airport-area-mapper/
│   ├── SKILL.md              # Skill 主文档
│   ├── scripts/              # 执行脚本
│   ├── references/           # 参考资料
│   └── airport-area-mapper.skill  # 打包文件
└── ...
```

## 如何创建新 Skill

参考 [skill-creator](https://docs.openclaw.ai/skills/creating-skills) 文档。

## 自动更新

当 Kimi Claw 生成新的 skill 时，会自动推送到此仓库。

---

*由 Kimi Claw 自动维护*
