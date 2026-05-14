import assert from 'node:assert/strict';
import fs from 'node:fs';

const detailPage = fs.readFileSync('src/app/pages/TaskDetailPage.tsx', 'utf8');
const uploadServer = fs.readFileSync('server/upload-server.mjs', 'utf8');

assert.match(
  detailPage,
  /import \{ deriveMineruProgressLine, deriveTaskDisplayStatus \} from '..\/utils\/taskView';/,
  'TaskDetailPage should import the same task progress view helpers used by the task list'
);

assert.match(
  detailPage,
  /const mineruProgressLine = deriveMineruProgressLine\(task as any\);/,
  'TaskDetailPage should derive a MinerU progress line from task metadata'
);

assert.match(
  detailPage,
  /\{mineruProgressLine \|\| taskDisplayStatus \|\| task\.message\}/,
  'TaskDetailPage overview should prefer semantic MinerU progress over generic lifecycle text'
);

assert.match(
  detailPage,
  /当前进展/,
  'TaskDetailPage overview should expose current progress as operator-visible text'
);

const statusRouteStart = uploadServer.indexOf("app.get('/ops/dependency-repair/status'");
const actionRouteStart = uploadServer.indexOf("app.post('/ops/dependency-repair'");
assert.notEqual(statusRouteStart, -1, 'dependency-repair status route should exist');
assert.notEqual(actionRouteStart, -1, 'dependency-repair action route should exist');

const statusRoute = uploadServer.slice(statusRouteStart, actionRouteStart);
assert.match(
  statusRoute,
  /code: 'SUPERVISOR_UNAVAILABLE'/,
  'status route should still report supervisor-unavailable semantics'
);
assert.doesNotMatch(
  statusRoute,
  /res\.status\(503\)/,
  'read-only supervisor status route should not produce repeated browser 503 resource noise'
);

const actionRoute = uploadServer.slice(actionRouteStart);
assert.match(
  actionRoute,
  /res\.status\(503\)/,
  'repair action route should keep HTTP 503 for real action failures'
);

console.log('task detail progress and supervisor status smoke passed');
