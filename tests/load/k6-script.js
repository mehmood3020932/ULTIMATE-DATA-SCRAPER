// tests/load/k6-script.js
// Load testing with k6

import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 100 },  // Ramp up
    { duration: '5m', target: 100 },  // Stay at 100 users
    { duration: '2m', target: 200 },  // Ramp to 200
    { duration: '5m', target: 200 },  // Stay at 200
    { duration: '2m', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],  // 95% under 500ms
    http_req_failed: ['rate<0.1'],     // Error rate under 10%
  },
};

const BASE_URL = 'http://localhost:8000';

export default function () {
  // Health check
  const healthRes = http.get(`${BASE_URL}/health`);
  check(healthRes, {
    'health status is 200': (r) => r.status === 200,
  });

  // API check
  const apiRes = http.get(`${BASE_URL}/api/v1/health`);
  check(apiRes, {
    'api status is 200': (r) => r.status === 200,
  });

  sleep(1);
}