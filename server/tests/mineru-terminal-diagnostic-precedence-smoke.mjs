import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import ts from 'typescript';

const sourcePath = path.join(process.cwd(), 'src', 'app', 'utils', 'taskView.ts');
const source = fs.readFileSync(sourcePath, 'utf8')
  .replace(/^import type .*;\n/m, '')
  .replace("import { TASK_STATUS_TERMS } from './taskTerms';", "const TASK_STATUS_TERMS = { failed: '失败', completed: '已完成', 'review-pending': '解析完成，待人工复核' };");

const transpiled = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.ES2022,
    target: ts.ScriptTarget.ES2022,
    esModuleInterop: true
  }
}).outputText;

const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'luceon-taskview-'));
const tempModulePath = path.join(tempDir, 'taskView.mjs');
fs.writeFileSync(tempModulePath, transpiled);

try {
  const { deriveMineruProgressLine, deriveTaskDisplayStatus } = await import(pathToFileURL(tempModulePath).href);

  const task90Shape = {
    id: 'task-1778655375028',
    state: 'failed',
    stage: 'ai',
    message: 'AI 识别完成: failed',
    metadata: {
      mineruStatus: 'completed',
      parsedFilesCount: 21,
      markdownObjectName: 'parsed/validation-postfix-1778655374/full.md',
      mineruObservedProgress: {
        activityLevel: 'log-observation-unreadable',
        progressSemantics: {
          activityLevel: 'log-observation-unreadable',
          message: 'MinerU 已提交/正在处理，但暂无可归因业务日志'
        },
        logSource: {
          logSourceExists: true,
          logSourceReadable: false
        }
      }
    }
  };

  const terminalLine = deriveMineruProgressLine(task90Shape);
  assert.equal(terminalLine, 'MinerU 已完成，但本次未捕获可归因业务进度日志');
  assert.equal(terminalLine.includes('已提交/正在处理'), false);
  assert.equal(terminalLine.includes('页 '), false);
  assert.equal(terminalLine.includes('批次 '), false);
  assert.equal(deriveTaskDisplayStatus(task90Shape), '失败');

  const activeProgressTask = {
    id: 'task-active-progress',
    state: 'running',
    stage: 'mineru-processing',
    metadata: {
      mineruStatus: 'processing',
      mineruObservedProgress: {
        activityLevel: 'active-progress',
        stage: { rawPhase: 'Predict', current: 14, total: 27 },
        window: { index: 1, total: 1, pageCurrent: 14, pageTotal: 27 }
      }
    }
  };

  const activeLine = deriveMineruProgressLine(activeProgressTask);
  assert.ok(activeLine.includes('Predict 14/27'));
  assert.ok(activeLine.includes('批次 1/1'));
  assert.ok(activeLine.includes('页 14/27'));

  const terminalWithoutArtifacts = {
    id: 'task-terminal-no-artifacts',
    state: 'failed',
    stage: 'ai',
    metadata: {
      mineruStatus: 'completed',
      mineruObservedProgress: {
        activityLevel: 'log-observation-unreadable',
        progressSemantics: {
          message: 'MinerU 已提交/正在处理，但暂无可归因业务日志'
        }
      }
    }
  };

  assert.equal(
    deriveMineruProgressLine(terminalWithoutArtifacts),
    'MinerU 已提交/正在处理，但暂无可归因业务日志',
    'terminal precedence requires parsed artifact evidence'
  );

  console.log('MinerU terminal diagnostic precedence smoke passed');
} finally {
  fs.rmSync(tempDir, { recursive: true, force: true });
}
