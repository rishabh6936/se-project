import http from 'k6/http';
import { sleep, check } from 'k6';

// This section defines the load pattern
export const options = {
  stages: [
    { duration: '30s', target: 50 }, // Ramp up to 50 virtual users over 30s
    { duration: '1m', target: 50 },  // Stay at 50 users for 1 minute
    { duration: '10s', target: 0 },   // Ramp down to 0
  ],
};

// This is the main function that each virtual user runs repeatedly
export default function () {
  // Replace with your API's Kubernetes service IP or NodePort
  const url = 'http://<YOUR_API_SERVICE_IP>/texts'; 
  
  const payload = JSON.stringify({
    content: `This is a test text from k6 user ${__VU} at ${new Date().toISOString()}`,
  });

  const params = {
    headers: { 'Content-Type': 'application/json' },
  };

  const res = http.post(url, payload, params);

  // Check if the request was successful (HTTP 202 Accepted)
  check(res, { 'status was 202': (r) => r.status === 202 });
  sleep(1); // Wait for 1 second before the next request
}