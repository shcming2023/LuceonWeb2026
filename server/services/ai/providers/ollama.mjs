/**
 * ollama.mjs - Ollama AI Provider 实现
 * 
 * 使用 Ollama /api/chat 接口发送系统与用户消息，获取解析后的 JSON 元数据。
 */

import { BaseProvider } from './base.mjs';
import { Agent } from 'undici';

export class OllamaProvider extends BaseProvider {
  constructor(config = {}) {
    super(config);
    this.baseUrl = (config.baseUrl || 'http://localhost:11434').replace(/\/$/, '');
    this.model = config.model || 'qwen3.5:9b';
    this.temperature = config.temperature ?? 0.1;
    this.keepAlive = config.keepAlive || process.env.OLLAMA_KEEP_ALIVE || '24h';
  }

  get id() {
    return 'ollama';
  }

  async healthCheck() {
    try {
      const resp = await fetch(`${this.baseUrl}/api/tags`, {
        signal: AbortSignal.timeout(5000)
      });
      return resp.ok;
    } catch {
      return false;
    }
  }

  async extractMetadata(markdownContent, options = {}) {
    const systemPrompt = options.systemPrompt || 'You are an education resource metadata extractor. Return only valid JSON.';
    
    const body = {
      model: this.model,
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: markdownContent }
      ],
      stream: false,
      keep_alive: this.keepAlive,
      think: false,   // 禁用思考模式（当前 Luceon 生产链路需要稳定 JSON，禁止 thinking 输出污染业务解析）
      options: {
        think: false, // 不允许由外部 settings 覆盖
        temperature: options.temperature ?? this.temperature,
        top_p: options.top_p,
        num_predict: options.num_predict || 1024
      }
    };

    if (options.expectJson !== false) {
      body.format = 'json'; // 强制 Ollama 输出 JSON
    }

    const startTime = Date.now();
    const heartbeatInterval = setInterval(() => {
      const elapsed = Math.round((Date.now() - startTime) / 1000);

      // Phase 1 (0-60s): 正常推理心跳
      if (elapsed <= 60) {
        console.log(`[ai-worker] Ollama ${this.model} 推理中... (已等待 ${elapsed}s)`);
        return;
      }

      // Phase 2 (60-120s): 响应缓慢警告
      if (elapsed <= 120) {
        console.warn(`[ai-worker] Ollama ${this.model} 响应缓慢 (已等待 ${elapsed}s)，可能卡住`);
        return;
      }

      // Phase 3 (>120s): 主动探测 Ollama 存活状态
      // 每 30s 探测一次（120s, 150s, 180s...），避免频繁请求
      if (elapsed % 30 < 10) {
        fetch(`${this.baseUrl}/api/tags`, { signal: AbortSignal.timeout(5000) })
          .then(alive => {
            if (alive.ok) {
              console.warn(`[ai-worker] Ollama API 可达但推理极慢 (已等待 ${elapsed}s)，建议关注`);
            } else {
              console.error(`[ai-worker] Ollama API 返回异常 (已等待 ${elapsed}s, HTTP ${alive.status})`);
            }
          })
          .catch(() => {
            console.error(`[ai-worker] Ollama API 探测失败 (已等待 ${elapsed}s)，可能已挂死`);
          });
      }
    }, 10000);
    const requestTimeoutMs = this.timeoutMs;
    try {
      const dispatcher = new Agent({
        headersTimeout: requestTimeoutMs,
        bodyTimeout: requestTimeoutMs
      });

      const response = await fetch(`${this.baseUrl}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        signal: AbortSignal.timeout(requestTimeoutMs),
        dispatcher
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Ollama API error: HTTP ${response.status} - ${errorText}`);
      }

      const data = await response.json();
      clearInterval(heartbeatInterval);
      const rawContent = data.message?.content || '';
      const rawContainsThinkTag = rawContent.includes('<think>');
      const strippedContent = this.filterThinking(rawContent);
      const duration = Date.now() - startTime;

      let result;
      if (options.expectJson === false) {
        result = strippedContent;
      } else {
        result = this.parseJsonRobust(strippedContent);
        if (!result) {
          if (options.returnRawOnParseFailure) {
            return {
              result: strippedContent,
              rawResponse: strippedContent,
              rawContainsThinkTag,
              parseFailed: true,
              parseError: `Failed to parse JSON from Ollama response, model: ${this.model}`,
              usage: {
                total_duration_ms: duration,
                prompt_tokens: data.prompt_eval_count || 0,
                completion_tokens: data.eval_count || 0
              },
              provider: this.id,
              model: this.model
            };
          }

          const parseErr = new Error(`Failed to parse JSON from Ollama response, model: ${this.model}`);
          const match = strippedContent.match(/```(?:json)?\s*([\s\S]*?)```/);
          const jsonStr = match ? match[1] : strippedContent;
          const rawTrimmed = jsonStr.trim();
          parseErr.rawContentDetails = {
            rawContentPreview: strippedContent.slice(0, 1000),
            rawContentLength: strippedContent.length,
            rawContentHead: strippedContent.slice(0, 300),
            rawContentTail: strippedContent.slice(-300),
            rawLooksTruncated: jsonStr.includes('{') && !rawTrimmed.endsWith('}') && !rawTrimmed.endsWith(']'),
            rawContainsThinkTag,
            responseFormatRequested: options.expectJson !== false,
            expectJson: options.expectJson,
            parseErrorMessage: parseErr.message
          };
          throw parseErr;
        }
      }

      return {
        result,
        rawResponse: strippedContent,
        rawContainsThinkTag,
        usage: {
          total_duration_ms: duration,
          prompt_tokens: data.prompt_eval_count || 0,
          completion_tokens: data.eval_count || 0
        },
        provider: this.id,
        model: this.model
      };
    } catch (err) {
      clearInterval(heartbeatInterval);
      const duration = Date.now() - startTime;
      
      let timeoutKind = 'network-or-fetch-error';
      if (err.name === 'TimeoutError' || err.message.includes('AbortError')) {
        timeoutKind = 'abort-timeout';
      } else if (err.cause?.code === 'UND_ERR_HEADERS_TIMEOUT' || err.message.includes('Headers Timeout') || err.cause?.message?.includes('Headers Timeout')) {
        timeoutKind = 'headers-timeout';
      }

      const errorDetail = {
        provider: this.id,
        name: err.name,
        message: err.message,
        cause: err.cause ? { code: err.cause.code, message: err.cause.message } : null,
        baseUrl: this.baseUrl,
        model: this.model,
        timeoutMs: requestTimeoutMs,
        durationMs: duration,
        timeoutKind,
        headersTimeoutMs: requestTimeoutMs,
        bodyTimeoutMs: requestTimeoutMs,
        ...(err.rawContentDetails || {})
      };
      
      const detailedMessage = `Ollama Provider Error: [${err.name}] ${err.message} (BaseURL: ${this.baseUrl}, Model: ${this.model}, Duration: ${duration}ms, Timeout: ${requestTimeoutMs}ms)`;
      
      const error = new Error(detailedMessage);
      error.details = errorDetail;
      // also put it directly on error for caller flexibility
      error.timeoutKind = timeoutKind;
      error.headersTimeoutMs = requestTimeoutMs;
      error.bodyTimeoutMs = requestTimeoutMs;
      error.cause = err.cause;
      throw error;
    }
  }
}
