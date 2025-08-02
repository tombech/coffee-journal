import { test, expect } from '@playwright/test';

test('debug API calls', async ({ page }) => {
  // Navigate to the app first
  await page.goto('/');
  
  // Test API call from browser context
  const response = await page.evaluate(async () => {
    try {
      const res = await fetch('/api/brew_sessions');
      const data = await res.text();
      return {
        ok: res.ok,
        status: res.status,
        statusText: res.statusText,
        headers: Object.fromEntries(res.headers.entries()),
        data: data
      };
    } catch (error) {
      return {
        error: error.message,
        name: error.name
      };
    }
  });
  
  console.log('API Response:', JSON.stringify(response, null, 2));
  
  // Also test direct backend call
  const directResponse = await page.evaluate(async () => {
    try {
      const res = await fetch('http://localhost:5000/api/brew_sessions');
      const data = await res.text();
      return {
        ok: res.ok,
        status: res.status,
        statusText: res.statusText,
        headers: Object.fromEntries(res.headers.entries()),
        data: data.substring(0, 200) + '...' // Truncate for readability
      };
    } catch (error) {
      return {
        error: error.message,
        name: error.name
      };
    }
  });
  
  console.log('Direct Backend Response:', JSON.stringify(directResponse, null, 2));
});