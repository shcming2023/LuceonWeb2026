/**
 * CleanService Worker Factory
 *
 * Provides a bounded factory function that constructs a production-shaped
 * CleanServiceWorker with the appropriate transport layer based on config.
 *
 * Behavior:
 * - CLEANSERVICE_ENABLED=false (default): worker returns disabled-noop
 * - CLEANSERVICE_ENABLED=true + endpoint: wires Mineru2Table HTTP transport
 * - CLEANSERVICE_ENABLED=true, no endpoint: transport reports explicit failure
 *
 * This factory does NOT activate scheduling, timers, or runtime dispatch.
 * It only constructs the worker/client stack for future callers.
 *
 * @module cleanservice/worker-factory
 */

import { loadCleanServiceConfig } from './config.mjs';
import { createCleanServiceClient } from './protocol.mjs';
import { CleanServiceWorker } from './cleanservice-worker.mjs';
import { createMineru2TableHttpTransport } from './http-transport.mjs';

/**
 * Creates a production-shaped CleanServiceWorker with HTTP transport wiring.
 *
 * @param {object} options
 * @param {object} [options.config] - CleanService config; defaults to loadCleanServiceConfig()
 * @param {object} [options.taskSource] - Task source adapter (must implement listTasks)
 * @param {object} [options.persistence] - Persistence adapter (must implement persistMetadataPatch)
 * @param {function} [options.now] - Clock function for timestamps
 * @returns {CleanServiceWorker}
 */
export function createCleanServiceWorker({
  config = loadCleanServiceConfig(),
  taskSource,
  persistence,
  now,
} = {}) {
  let transport = null;

  if (config.enabled && config.endpoint) {
    transport = createMineru2TableHttpTransport({
      endpoint: config.endpoint,
      apiKey: config.apiKey,
      timeoutMs: config.timeoutMs,
    });
  }

  const client = createCleanServiceClient({ config, transport });

  return new CleanServiceWorker({
    config,
    taskSource,
    client,
    persistence,
    now,
  });
}

/**
 * Creates a CleanServiceClient with HTTP transport wiring (no worker layer).
 *
 * Useful for direct client operations without the worker tick loop.
 *
 * @param {object} [options]
 * @param {object} [options.config] - CleanService config
 * @returns {{ config, submitJob, queryJob }}
 */
export function createCleanServiceClientWithTransport({
  config = loadCleanServiceConfig(),
} = {}) {
  let transport = null;

  if (config.enabled && config.endpoint) {
    transport = createMineru2TableHttpTransport({
      endpoint: config.endpoint,
      apiKey: config.apiKey,
      timeoutMs: config.timeoutMs,
    });
  }

  return createCleanServiceClient({ config, transport });
}
