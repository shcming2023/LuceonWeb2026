/**
 * CleanService Mineru2Table HTTP Transport
 *
 * Provides a Protocol v1-shaped HTTP transport function for submitting
 * toc-rebuild job requests to a Mineru2Table API endpoint.
 *
 * Disabled by default: production runtime does not activate this transport
 * unless CLEANSERVICE_ENABLED=true and CLEANSERVICE_ENDPOINT is configured.
 *
 * @module cleanservice/http-transport
 */

/**
 * Creates an HTTP transport function compatible with createCleanServiceClient.
 *
 * The transport function accepts { action, payload, config } and returns
 * the parsed JSON response from the Mineru2Table API.
 *
 * Supported actions:
 * - 'submitJob': POST /api/v1/jobs with the job request payload
 * - 'queryJob': GET /api/v1/jobs/{jobId}
 *
 * @param {object} options
 * @param {string} options.endpoint - Base URL of the Mineru2Table API (e.g. 'http://127.0.0.1:8000')
 * @param {string} [options.apiKey] - Optional API key for X-API-Key header
 * @param {number} [options.timeoutMs=30000] - Request timeout in milliseconds
 * @returns {function} Transport function for createCleanServiceClient
 */
export function createMineru2TableHttpTransport({
  endpoint,
  apiKey = null,
  timeoutMs = 30_000,
} = {}) {
  if (!endpoint || typeof endpoint !== 'string') {
    throw new Error('cleanservice-http-transport: endpoint is required');
  }

  // Normalize: strip trailing slash
  const baseUrl = endpoint.replace(/\/+$/, '');

  return async function mineru2tableHttpTransport({ action, payload, config }) {
    if (action === 'submitJob') {
      return await httpPost(
        `${baseUrl}/api/v1/jobs`,
        payload,
        { apiKey: apiKey || config?.apiKey, timeoutMs }
      );
    }

    if (action === 'queryJob') {
      const jobId = payload?.jobId || payload?.job_id;
      if (!jobId) {
        throw new Error('cleanservice-http-transport: queryJob requires jobId');
      }
      return await httpGet(
        `${baseUrl}/api/v1/jobs/${encodeURIComponent(jobId)}`,
        { apiKey: apiKey || config?.apiKey, timeoutMs }
      );
    }

    throw new Error(`cleanservice-http-transport: unsupported action '${action}'`);
  };
}

/**
 * Perform an HTTP POST request and return parsed JSON.
 *
 * Uses native fetch (available in Node 18+). Applies timeout via AbortSignal.
 * Non-2xx responses are thrown as explicit errors with status code and body.
 *
 * @param {string} url - Full URL to POST to
 * @param {object} body - JSON body to send
 * @param {object} options
 * @param {string} [options.apiKey] - Optional API key
 * @param {number} [options.timeoutMs] - Timeout in milliseconds
 * @returns {Promise<object>} Parsed JSON response
 */
async function httpPost(url, body, { apiKey, timeoutMs = 30_000 } = {}) {
  const headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  };
  if (apiKey) {
    headers['X-API-Key'] = apiKey;
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
      signal: controller.signal,
    });

    const text = await response.text();

    if (!response.ok) {
      const error = new Error(
        `cleanservice-http-transport: POST ${url} returned ${response.status}: ${text.slice(0, 500)}`
      );
      error.code = 'transport_http_error';
      error.statusCode = response.status;
      error.retriable = response.status >= 500;
      throw error;
    }

    try {
      return JSON.parse(text);
    } catch {
      const error = new Error(
        `cleanservice-http-transport: POST ${url} returned non-JSON: ${text.slice(0, 200)}`
      );
      error.code = 'transport_parse_error';
      throw error;
    }
  } finally {
    clearTimeout(timer);
  }
}

/**
 * Perform an HTTP GET request and return parsed JSON.
 *
 * @param {string} url - Full URL to GET
 * @param {object} options
 * @param {string} [options.apiKey] - Optional API key
 * @param {number} [options.timeoutMs] - Timeout in milliseconds
 * @returns {Promise<object>} Parsed JSON response
 */
async function httpGet(url, { apiKey, timeoutMs = 30_000 } = {}) {
  const headers = { 'Accept': 'application/json' };
  if (apiKey) {
    headers['X-API-Key'] = apiKey;
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      method: 'GET',
      headers,
      signal: controller.signal,
    });

    const text = await response.text();

    if (!response.ok) {
      const error = new Error(
        `cleanservice-http-transport: GET ${url} returned ${response.status}: ${text.slice(0, 500)}`
      );
      error.code = 'transport_http_error';
      error.statusCode = response.status;
      error.retriable = response.status >= 500;
      throw error;
    }

    try {
      return JSON.parse(text);
    } catch {
      const error = new Error(
        `cleanservice-http-transport: GET ${url} returned non-JSON: ${text.slice(0, 200)}`
      );
      error.code = 'transport_parse_error';
      throw error;
    }
  } finally {
    clearTimeout(timer);
  }
}
