/**
 * base.mjs - AI Provider 抽象基类
 * 
 * 定义所有 AI 元数据提取提供者必须遵循的契约。
 */

export function repairInvalidJsonStringEscapes(candidate) {
  const text = String(candidate || '');
  let repaired = '';
  let inString = false;
  let escaped = false;

  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];

    if (!inString) {
      repaired += char;
      if (char === '"') inString = true;
      continue;
    }

    if (escaped) {
      if (char === 'u') {
        const hex = text.slice(i + 1, i + 5);
        if (/^[0-9a-fA-F]{4}$/.test(hex)) {
          repaired += char;
          escaped = false;
          continue;
        }
        repaired += `\\${char}`;
        escaped = false;
        continue;
      }

      if ('"\\/bfnrt'.includes(char)) {
        repaired += char;
        escaped = false;
        continue;
      }

      repaired += `\\${char}`;
      escaped = false;
      continue;
    }

    if (char === '\\') {
      repaired += char;
      escaped = true;
      continue;
    }

    repaired += char;
    if (char === '"') inString = false;
  }

  if (escaped) repaired += '\\';
  return repaired;
}

export class BaseProvider {
  /**
   * @param {object} config - 配置信息（端点、模型、API Key、超时等）
   */
  constructor(config = {}) {
    this.config = config;
    this.timeoutMs = Number(config.timeoutMs || 120000); // 默认 120s
  }

  /**
   * 核心识别方法
   * @param {string} markdownContent - 输入的 Markdown 内容
   * @param {object} options - 额外选项（系统提示词、温度等）
   * @returns {Promise<{result: object, rawResponse: string, usage: object, provider: string, model: string}>}
   */
  async extractMetadata(markdownContent, options = {}) {
    throw new Error('Method extractMetadata() must be implemented');
  }

  /**
   * 健康检查
   * @returns {Promise<boolean>}
   */
  async healthCheck() {
    throw new Error('Method healthCheck() must be implemented');
  }

  /**
   * 获取 Provider 唯一标识
   */
  get id() {
    throw new Error('Getter id must be implemented');
  }

  /**
   * 过滤 Qwen 等模型输出中的 <think> 标签内容
   * @param {string} text 
   * @returns {string}
   */
  filterThinking(text) {
    if (!text) return '';
    return text.replace(/<think>[\s\S]*?(?:<\/think>|$)/gi, '').trim();
  }

  /**
   * 容错解析 JSON（PRD 10.5.2）
   * @param {string} text 
   * @returns {object|null}
   */
  parseJsonRobust(text) {
    let cleaned = this.filterThinking(text);
    if (!cleaned) return null;

    const tryParse = (candidate) => {
      try {
        return JSON.parse(candidate);
      } catch {}

      const repaired = repairInvalidJsonStringEscapes(candidate);
      if (repaired !== candidate) {
        try {
          return JSON.parse(repaired);
        } catch {}
      }

      return null;
    };

    // 1. 尝试直接解析
    const direct = tryParse(cleaned);
    if (direct) return direct;

    // 2. 尝试提取 ```json ... ``` 或 ``` ... ``` 甚至只是不带标签的 code fence
    const mdJsonMatch = cleaned.match(/```(?:json)?\s*([\s\S]*?)\s*```/);
    if (mdJsonMatch && mdJsonMatch[1]) {
      const parsed = tryParse(mdJsonMatch[1].trim());
      if (parsed) return parsed;
    }

    // 3. 寻找第一个 { 和最后一个 }
    const startIndex = cleaned.indexOf('{');
    const endIndex = cleaned.lastIndexOf('}');
    if (startIndex !== -1 && endIndex !== -1 && endIndex >= startIndex) {
      const jsonStr = cleaned.slice(startIndex, endIndex + 1);
      const parsed = tryParse(jsonStr);
      if (parsed) return parsed;
    }
    
    return null;
  }
}
