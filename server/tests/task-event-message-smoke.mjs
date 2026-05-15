import assert from 'node:assert/strict';
import { buildTaskEventLogMessage } from '../services/queue/task-worker.mjs';

async function main() {
  console.log('=== Task Event Message Smoke ===');

  assert.equal(
    buildTaskEventLogMessage({ metadata: { mineruObservedProgress: { activityLevel: 'active-progress' } } }, 'progress-update'),
    'Progress metadata updated',
  );
  assert.notEqual(
    buildTaskEventLogMessage({ metadata: { mineruObservedProgress: { activityLevel: 'active-progress' } } }, 'progress-update'),
    'Status changed to undefined',
  );
  assert.equal(
    buildTaskEventLogMessage({ state: 'review-pending' }, 'stage-changed'),
    'Status changed to review-pending',
  );
  assert.equal(
    buildTaskEventLogMessage({ stage: 'ai' }, 'stage-changed'),
    'Stage changed to ai',
  );

  console.log('PASS task event message smoke');
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
