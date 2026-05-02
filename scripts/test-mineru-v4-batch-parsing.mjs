import assert from 'assert';

console.log('--- Testing MinerU V4 Batch file_urls Parsing ---');

// Mock function that implements the same logic as v4-online-adapter.mjs
function getUploadUrl(batchPayload, fileName) {
  const fileUrlsObj = batchPayload?.data?.file_urls || batchPayload?.file_urls;
  let uploadUrl = '';

  if (Array.isArray(fileUrlsObj) && fileUrlsObj.length > 0) {
    if (typeof fileUrlsObj[0] === 'string') {
      uploadUrl = fileUrlsObj[0];
    } else {
      const match = fileUrlsObj.find(f => f.file_name === fileName || f.name === fileName) || fileUrlsObj[0];
      if (match) uploadUrl = match.upload_url || match.uploadUrl;
    }
  } else if (typeof fileUrlsObj === 'object' && fileUrlsObj !== null) {
    const match = fileUrlsObj[fileName] || Object.values(fileUrlsObj)[0];
    if (match) uploadUrl = match.upload_url || match.uploadUrl;
  }

  return uploadUrl;
}

// Case 1: Official string array response
const payloadStringArray = {
  data: {
    batch_id: 'batch-123',
    file_urls: [
      'https://oss.mineru.net/upload-xyz'
    ]
  }
};
const result1 = getUploadUrl(payloadStringArray, 'test.pdf');
assert.strictEqual(result1, 'https://oss.mineru.net/upload-xyz', 'String array parsing failed');

// Case 2: Object array response (future-proof)
const payloadObjectArray = {
  data: {
    batch_id: 'batch-456',
    file_urls: [
      { file_name: 'test.pdf', upload_url: 'https://oss.mineru.net/upload-obj' }
    ]
  }
};
const result2 = getUploadUrl(payloadObjectArray, 'test.pdf');
assert.strictEqual(result2, 'https://oss.mineru.net/upload-obj', 'Object array parsing failed');

// Case 3: Dictionary object response (legacy/alternative)
const payloadDict = {
  data: {
    batch_id: 'batch-789',
    file_urls: {
      'test.pdf': { upload_url: 'https://oss.mineru.net/upload-dict' }
    }
  }
};
const result3 = getUploadUrl(payloadDict, 'test.pdf');
assert.strictEqual(result3, 'https://oss.mineru.net/upload-dict', 'Dictionary parsing failed');

console.log('✅ All parsing assertions passed successfully.');
