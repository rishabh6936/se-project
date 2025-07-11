// load_test.js

import http from 'k6/http';
import { sleep, check } from 'k6';

// This section defines the load pattern for the test.
export const options = {
  stages: [
    { duration: '20s', target: 20 }, // 1. Ramp-up: Go from 0 to 20 virtual users over 20 seconds.
    { duration: '30s', target: 20 }, // 2. Steady Load: Stay at 20 virtual users for 30 seconds.
    { duration: '10s', target: 0 },  // 3. Ramp-down: Go back down to 0 users.
  ],
  thresholds: {
    // We want to ensure that 95% of requests are successful (status 202).
    'http_req_failed': ['rate<0.05'], // http errors should be less than 5%
    'checks': ['rate>0.95'], // the 'check' below should pass for >95% of requests
  },
};

// This is the main function that each virtual user will run in a loop.
export default function () {
  // --- THE FIX ---
  // The URL now correctly points to the '/texts' endpoint defined in your main.py
  const url = 'http://localhost:8000/texts'; 
  
  // The payload your API expects.
  const payload = JSON.stringify({
    content: `k6 virtual user ${__VU} is sending a test text for analysis. Iteration number is ${__ITER}.`,
    // topic is optional, so we don't need to send it.
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  // Send the POST request.
  const res = http.post(url, payload, params);

  // Check the result of the request. The endpoint should return 202 Accepted.
  check(res, {
    'is status 202 (Accepted)': (r) => r.status === 202,
  });

  // Each virtual user will wait for 1 second before sending the next request.
  sleep(1); 
}