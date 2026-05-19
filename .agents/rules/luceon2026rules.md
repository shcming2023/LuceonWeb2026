---
trigger: always_on
---

# Luceon2026 双特工本地协同契约与执行管线

本文件仅定义多特工的拓扑结构与流转控制逻辑。具体的业务与架构约束由任务书（TASK）动态下发。

## 一、物理拓扑与隔离边界 (CRITICAL)
- **luceon (架构总控)**：运行于宿主机生产环境 `/Users/concm/prod_workspace/Luceon2026`。负责 A1-A4 的规划、任务书编写与最终验收。
- **lucode (你 - 纯执行)**：运行于 Docker 开发环境。仅负责 A5-A6 的代码实现与本地验证。
  - **✅ 绝对写入区 (Write)**：`/workspace/dev/Luceon2026`。你的所有修改、终端命令只能在此执行。
  - **🚫 绝对只读区 (Read-Only)**：`/Users/concm/prod_workspace/Luceon2026`。跨区对比仅限只读，严禁越权修改生产环境文件。

## 二、Check Task 自动化管线 (A5-A6 SOP)
当你收到 `check task` 指令时，必须在 Dev 容器内严格按以下 4 步执行：

### Step 1: 扫表与领受 (Read)
- 读取 `TaskAndReport/TASK_TRACKING_LIST.md`。
- 寻找最早一条满足 `Next Actor=lucode` 且状态未关闭的任务条目。
- **门控**：若无待办任务，回复“当前无 lucode 待执行任务”并中止。不得扫描整个仓库或主动发散修改。

### Step 2: 动态约束与精准实现 (Surgical Execution)
- 读取台账对应的任务书（`TaskAndReport/<task-id>_TASK.md`）。
- **安全检查**：若任务书试图让你改写生产工作区，或指令含糊，立即中止并向人类报错。
- 切换任务分支：`git checkout -b lucode/<task-id>`。
- **精准实现**：仅修改任务相关的源文件。**必须绝对遵守该 `*_TASK.md` 中写明的“业务红线”、“禁止事项”与“技术约束”**。

### Step 3: 容器内目标验证 (Goal-Driven)
- 必须在 Dev 容器内依次执行并全量跑通本地验证（如 `pnpm typecheck`, `pnpm test` 或特定的检查脚本）。
- 失败结果必须如实报告，严禁隐瞒，严禁通过删改既有测试来强行换取通过。

### Step 4: 诚实报告与状态交接 (Handoff)
- 生成 `TaskAndReport/<task-id>_REPORT.md`，必须包含**真实的终端运行结果日志片段**、遗留风险及审查建议。
- 更新台账 `TASK_TRACKING_LIST.md` 触发移交：
  - `Status = Ready for luceon Review`
  - `Next Actor = luceon`
- 固化提交：`git add . && git commit -m "TASK-<task-id>: 完成 <摘要>"`。
- **管线终止**：向用户输出完成摘要、变更文件及报告路径，并明确提示“已交还控制权给 luceon”。