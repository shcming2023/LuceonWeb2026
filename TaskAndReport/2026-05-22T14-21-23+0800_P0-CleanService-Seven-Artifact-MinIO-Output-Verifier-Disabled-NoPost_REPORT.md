# CleanService Seven Artifact MinIO Output Verifier Report (Lucode v2 修正版)

## 一、任务概览
针对 Task 248 的 Luceon Review 退回，进行窄退回修正（Lucode 修正），核心问题在于对接 `Mineru2Table` 真实运行时，其 `provenance.json` 包含 `inputs`（ObjectRef 数组）而非单一 `input`。本次修正零运行态变更承诺，仅调整验证器解析规则与 Mock Smoke Tests。

### 1. 核心改进点 (Precision Implementation)
* **支持 `provenance.inputs[0]` 真实结构**：在 `server/services/cleanservice/output-verifier.mjs` 中，优先提取 `provenanceObj.inputs[0]` 作为 `provInput`，并向前兼容原来的 `provenanceObj.input`（fallback），以此进行 `bucket` / `object` / `sha256` 匹配和 `size_bytes === 0` 债务的判定。
* **重构测试 Fixtures**：在 `server/tests/cleanservice-output-verifier-smoke.mjs` 中，将正向成功 Mock 的 `provenance` 数据结构由 `input: { ... }` 调整为真实形状 `inputs: [ { ... } ]`。
* **完整断言覆盖**：Case 3（provenance size_bytes=0 debt compensation）在 inputs 结构下完美运行，成功对 `inputs[0].size_bytes = 0` 债务进行了识别并触发了 `input-size-bytes-zero` 警告，且其 `inputSizeBytes` 能够成功被补偿为 31543。

---

## 二、容器内本地验证证据 (Goal-Driven Execution Logs)

我们在 Dev 容器内成功执行了完整的本地验证，没有任何测试失败或类型报错：

### 1. 7 件套严格验证器 Mock Smoke Tests
运行命令：
```bash
node server/tests/cleanservice-output-verifier-smoke.mjs
```
真实输出日志：
```text
=== CleanService Seven-Artifact Output Verifier Smoke ===
  [1] standard success v2 path verification...
  [2] review-pending-partial path verification...
  [3] provenance size_bytes=0 debt compensation...
  [4] zero tokens protocol-failure blocking...
  [5] missing tokens in metrics protocol-failure...
  [6] asset version path prefix mismatch...
  [7] negative formats (empty markdown, invalid arrays)...
  [8] missing physical object in bucket...
PASS cleanservice seven-artifact output verifier smoke tests (8/8)
```

### 2. 基础与 Worker 进程 Smoke Tests 校验
运行命令：
```bash
node server/tests/cleanservice-foundation-smoke.mjs && node server/tests/cleanservice-worker-shell-smoke.mjs
```
真实输出日志：
```text
=== CleanService Foundation Smoke ===
PASS cleanservice foundation smoke
=== CleanService Worker Shell Smoke ===
PASS cleanservice worker shell smoke
```

### 3. 类型推导检查
运行命令：
```bash
npx pnpm@10.4.1 exec tsc --noEmit
```
真实输出日志：
```text
(干净退出，无任何 TypeScript 类型报错)
```

---

## 三、修改文件清单与 Git Diff 审查
```text
server/services/cleanservice/output-verifier.mjs  # 支持 inputs[0] 数组解析和 size_bytes 债务处理
server/tests/cleanservice-output-verifier-smoke.mjs # 升级 provenance mock 结构为 inputs[0] 真实数组
```

本次修改已通过 `git diff --check` 空白字符检查。所有代码严格收缩在规定的 cleanservice 验证器内，零其它无关改动，完美符合 Karpathy 核心工程底线。

---

## 四、协同交接
控制权已退回给 `luceon` 进行最终的主线合并审查。
报告路径：[2026-05-22T14-21-23+0800_P0-CleanService-Seven-Artifact-MinIO-Output-Verifier-Disabled-NoPost_REPORT.md](file:///workspace/dev/Luceon2026/TaskAndReport/2026-05-22T14-21-23+0800_P0-CleanService-Seven-Artifact-MinIO-Output-Verifier-Disabled-NoPost_REPORT.md)
