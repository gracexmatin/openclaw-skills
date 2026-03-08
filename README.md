# OpenClaw Skills

我自定义的 OpenClaw Agent Skills 集合。

🔗 **GitHub**: https://github.com/gracexmatin/openclaw-skills

## 什么是 Skill

Skill 是 OpenClaw 的扩展模块，为 AI Agent 提供特定领域的能力和工作流。

## 已收录 Skills

| Skill | 描述 | 版本 |
|-------|------|------|
| [airport-area-mapper](./airport-area-mapper/) | 机场/地点面积测量：Excel → 高德截图 → 面积测量 → 结果导出 | 1.0.0 |

## 安装方法

### 方法1: 通过 ClawHub（推荐）

```bash
openclaw skill install airport-area-mapper
```

### 方法2: 手动安装

```bash
# 1. 下载 .skill 文件
wget https://github.com/gracexmatin/openclaw-skills/raw/main/airport-area-mapper.skill

# 2. 放置到 skills 目录
mkdir -p ~/.openclaw/skills/airport-area-mapper
unzip airport-area-mapper.skill -d ~/.openclaw/skills/airport-area-mapper
```

## 开发新 Skill

```bash
# 1. 创建新 skill
cd /root/.openclaw/workspace/skills
python3 /usr/lib/node_modules/openclaw/skills/skill-creator/scripts/init_skill.py my-skill --path . --resources scripts

# 2. 编辑 SKILL.md 和脚本

# 3. 打包
python3 /usr/lib/node_modules/openclaw/skills/skill-creator/scripts/package_skill.py my-skill

# 4. 推送到 GitHub
/root/.openclaw/workspace/tools/sync-skills-to-github.sh my-skill
```

## 自动同步

当 Kimi Claw 生成新的 skill 后，运行以下命令推送到 GitHub：

```bash
# 同步特定 skill
/root/.openclaw/workspace/tools/sync-skills-to-github.sh airport-area-mapper

# 同步所有 skills
/root/.openclaw/workspace/tools/sync-skills-to-github.sh
```

---

*由 Kimi Claw 自动维护*
