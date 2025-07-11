// full_test.js

import http from 'k6/http';
import { sleep, check, group } from 'k6';

// --- Configuration ---
const BASE_URL = 'http://localhost:8000';
const TOPICS = ['gaming', 'science_&_technology', 'music', 'sports', 'fashion_&_style']; // Some topics to query

// --- k6 Options: Define Scenarios ---
export const options = {
  thresholds: {
    'http_req_failed': ['rate<0.05'], // Global error rate should be less than 5%
    'http_req_duration': ['p(95)<500'], // 95% of requests should be below 500ms
  },
  scenarios: {
    // SCENARIO 1: A constant low-level write load
    // Simulates users constantly creating new texts.
    write_load: {
      executor: 'constant-arrival-rate',
      rate: 10, // Start 10 new iterations every second
      timeUnit: '1s',
      duration: '1m', // Run for 1 minute
      preAllocatedVUs: 5, // Start with 5 VUs, k6 will add more if needed
      maxVUs: 20,
      exec: 'create_text', // This scenario will only run the 'create_text' function
    },
    // SCENARIO 2: A ramping read load
    // Simulates users browsing the content.
    read_load: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '30s', target: 15 }, // Ramp up to 15 users
        { duration: '30s', target: 15 }, // Stay at 15 users
        { duration: '10s', target: 0 },  // Ramp down
      ],
      exec: 'read_endpoints', // This scenario will only run the 'read_endpoints' function
    },
  },
};

// --- Test Functions ---

// Function for the 'write_load' scenario
export function create_text() {
  const url = `${BASE_URL}/texts`;
  const payload = JSON.stringify({
    content: `A new post about ${TOPICS[__VU % TOPICS.length]} from VU ${__VU}`,
    topic: TOPICS[__VU % TOPICS.length] // Assign a topic so we can query it later
  });
  const params = { headers: { 'Content-Type': 'application/json' } };
  
  const res = http.post(url, payload, params);
  
  check(res, { 'POST /texts: status is 202': (r) => r.status === 202 });
  sleep(1);
}

// Function for the 'read_load' scenario
export function read_endpoints() {
  group('Read Endpoints', function () {
    // 1. Test the /stats endpoint
    group('GET /stats', function () {
      const res = http.get(`${BASE_URL}/stats`);
      check(res, { 'status is 200': (r) => r.status === 200 });
    });

    sleep(0.5); // Small pause between different types of reads

    // 2. Test the /texts/topic/{topic} endpoint
    group('GET /texts/topic', function () {
      const randomTopic = TOPICS[Math.floor(Math.random() * TOPICS.length)];
      const res = http.get(`${BASE_URL}/texts/topic/${randomTopic}`);
      check(res, { 'status is 200': (r) => r.status === 200 });
    });

    sleep(0.5); // Small pause

    // 3. Test the /texts/period endpoint (optional, as dates can be tricky)
    // For simplicity, we'll query the last 60 seconds.
    group('GET /texts/period', function () {
      const endDate = new Date().toISOString();
      const startDate = new Date(Date.now() - 60000).toISOString(); // 60 seconds ago
      const url = `${BASE_URL}/texts/period?start_date=${startDate}&end_date=${endDate}`;
      const res = http.get(url);
      check(res, { 'status is 200': (r) => r.status === 200 });
    });
  });

  sleep(1); // Each virtual user waits 1 second before starting the next iteration of reads
}