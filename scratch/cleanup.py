import re
import sys

filepath = "src/app/pages/SettingsPage.tsx"
with open(filepath, "r", encoding="utf-8") as f:
    text = f.read()

# 1. Hide AI multi-provider UI
text = text.replace(
    '<h2 className="font-semibold text-gray-800">AI 提供商（按优先级依次尝试）</h2>',
    '<h2 className="font-semibold text-gray-800">AI 提供商配置</h2>'
)

# Remove the "Add Provider" button
text = re.sub(
    r'<button[^>]*onClick=\{\(\) => \{[^}]*const newProvider[\s\S]*?新增提供商\s*</button>',
    '',
    text
)

# Remove moveUp, moveDown, remove buttons
text = re.sub(
    r'<button type="button" onClick=\{moveUp\}[^>]*>[\s\S]*?</button>\s*<button type="button" onClick=\{moveDown\}[^>]*>[\s\S]*?</button>',
    '',
    text
)
text = re.sub(
    r'<button type="button" onClick=\{remove\} className="p-1 text-red-400 hover:text-red-600" title="删除">\s*<Trash2 size=\{14\} />\s*</button>',
    '',
    text
)

# 2. Hide high-risk restore/import/replace controls
# We can find the "备份与恢复" section and remove the "导入元数据 JSON", "导入完整资产" buttons
text = re.sub(
    r'<button\s*onClick=\{\(\) => jsonImportInputRef\.current\?\.click\(\)\}[\s\S]*?导入元数据 JSON\s*</button>',
    '',
    text
)
text = re.sub(
    r'<button\s*onClick=\{\(\) => fullImportInputRef\.current\?\.click\(\)\}[\s\S]*?导入完整资产\s*</button>',
    '',
    text
)

# Remove the "replace / merge" radio buttons
text = re.sub(
    r'<div className="flex gap-4 text-sm text-gray-600">\s*<label className="flex items-center gap-2">[\s\S]*?<span>merge 仅补缺失</span>\s*</label>\s*</div>',
    '',
    text
)

# Optional: Add a message in the backup section about import being disabled.
text = text.replace(
    '<p className="font-medium text-gray-800">JSON 元数据备份</p>',
    '<p className="font-medium text-gray-800">JSON 元数据备份 (导入功能已归档)</p>'
)
text = text.replace(
    '<p className="font-medium text-gray-800">完整资产备份</p>',
    '<p className="font-medium text-gray-800">完整资产备份 (导入功能已归档)</p>'
)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(text)
print("Done")
