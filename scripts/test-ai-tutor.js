/**
 * Local smoke test for api/ai-tutor.js (no Vercel CLI needed).
 *
 *   npm run test:ai                       # uses GEMINI_API_KEY from .env
 *   npm run test:ai -- "Explain two sum"  # custom question
 *
 * Auth is disabled for this local run only.
 */
require('dotenv').config();
process.env.REQUIRE_AUTH = 'false';

const handler = require('../api/ai-tutor');

function mockRes() {
  return {
    statusCode: 200,
    headers: {},
    setHeader(k, v) { this.headers[k.toLowerCase()] = v; },
    end(body) {
      console.log(`Status: ${this.statusCode}`);
      try {
        const data = JSON.parse(body);
        console.log(data.reply ? `Model: ${data.model}\n\n${data.reply}` : data);
      } catch {
        if (body) console.log(body);
      }
    },
  };
}

const question = process.argv[2] || 'What is the time complexity of my code, and can it be improved?';

handler(
  {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: {
      mode: 'complexity',
      language: 'python',
      problem: { title: 'Two Sum' },
      code: 'def twoSum(nums, target):\n    for i in range(len(nums)):\n        for j in range(i + 1, len(nums)):\n            if nums[i] + nums[j] == target:\n                return [i, j]',
      question,
    },
  },
  mockRes()
);
