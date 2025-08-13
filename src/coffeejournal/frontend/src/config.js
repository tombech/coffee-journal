// API Configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

/**
 * Add user_id parameter to URL if running in test mode or production
 */
function addUserIdToUrl(url) {
  // Add user_id during E2E tests when window.TEST_USER_ID is set
  if (typeof window !== 'undefined' && window.TEST_USER_ID) {
    const separator = url.includes('?') ? '&' : '?';
    return `${url}${separator}user_id=${window.TEST_USER_ID}`;
  }
  
  // In production/development, always pass user_id=default for consistency
  const separator = url.includes('?') ? '&' : '?';
  return `${url}${separator}user_id=default`;
}

/**
 * Enhanced fetch that automatically adds user_id for E2E tests
 */
function apiFetch(url, options = {}) {
  const fullUrl = url.startsWith('http') ? url : `${API_BASE_URL}${url.startsWith('/') ? url : '/' + url}`;
  const urlWithUserId = addUserIdToUrl(fullUrl);
  return fetch(urlWithUserId, options);
}

export { API_BASE_URL, apiFetch, addUserIdToUrl };