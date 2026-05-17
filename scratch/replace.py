import sys

filepath = "docs/codex/PROJECT_HISTORY.md"
with open(filepath, "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace(
    '| **Overleaf 备份系统** | `/backup/*` | 当前仓库仅保留 LaTeX 工具入口，未接入独立备份后端页面 |',
    '| **Overleaf 备份系统** | `/backup/*` | 已归档，不再活跃维护 |'
)
text = text.replace(
    '| **LaTeX 工具集** | `/backup/latex` | 浏览器本地处理，不依赖后端 |',
    '| **LaTeX 工具集** | `/backup/latex` | 已归档移除，不再作为前端主功能 |'
)
text = text.replace(
    '| `/backup/latex` | `LatexToolPage` | LaTeX 工具集 | ✅ 完成（纯浏览器端） |',
    '| `/backup/latex` | `LatexToolPage` | LaTeX 工具集 | 已归档移除 |'
)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(text)
print("Done")
