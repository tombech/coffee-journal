/**
 * Playwright Helper Functions
 * 
 * Replaces brittle waitForTimeout calls with proper wait strategies
 */

/**
 * Wait for element to be visible and stable (no more re-renders)
 */
async function waitForStableElement(page, selector, timeout = 5000) {
  await page.waitForSelector(selector, { state: 'visible', timeout });
  
  // Wait for element to be stable (not changing)
  let previousText = '';
  let stableCount = 0;
  const maxStableChecks = 10;
  
  while (stableCount < maxStableChecks) {
    const currentText = await page.locator(selector).textContent();
    if (currentText === previousText) {
      stableCount++;
    } else {
      stableCount = 0;
      previousText = currentText;
    }
    await page.waitForTimeout(50); // Small delay between stability checks
  }
}

/**
 * Wait for form submission to complete
 */
async function waitForFormSubmission(page, formSelector = 'form') {
  // Wait for form to be present
  await page.waitForSelector(formSelector);
  
  // Wait for any loading states to clear
  await page.waitForFunction(
    () => !document.querySelector('[aria-busy="true"]'),
    { timeout: 5000 }
  );
  
  // Wait for network to be idle (no ongoing requests)
  await page.waitForLoadState('networkidle', { timeout: 5000 });
}

/**
 * Wait for navigation to complete with proper URL validation
 */
async function waitForNavigation(page, expectedUrlPattern, timeout = 5000) {
  await page.waitForURL(expectedUrlPattern, { timeout });
  await page.waitForLoadState('networkidle');
}

/**
 * Wait for table to load with expected minimum row count
 */
async function waitForTableRows(page, tableSelector, minimumRows = 1, timeout = 5000) {
  await page.waitForSelector(tableSelector, { timeout });
  
  await page.waitForFunction(
    ({ tableSelector, minimumRows }) => {
      const table = document.querySelector(tableSelector);
      if (!table) return false;
      
      const rows = table.querySelectorAll('tbody tr');
      return rows.length >= minimumRows;
    },
    { tableSelector, minimumRows },
    { timeout }
  );
}

/**
 * Wait for API call to complete (better than arbitrary timeouts)
 */
async function waitForApiCall(page, apiEndpoint, timeout = 5000) {
  const responsePromise = page.waitForResponse(
    response => response.url().includes(apiEndpoint) && response.status() < 400,
    { timeout }
  );
  
  return responsePromise;
}

/**
 * Fill form field and wait for validation
 */
async function fillAndValidate(page, selector, value, timeout = 2000) {
  await page.fill(selector, value);
  
  // Wait for any validation to complete
  await page.waitForFunction(
    (selector) => {
      const field = document.querySelector(selector);
      return field && !field.matches(':invalid');
    },
    selector,
    { timeout }
  );
}

/**
 * Click button and wait for action to complete
 */
async function clickAndWaitForAction(page, buttonSelector, expectedChange, timeout = 5000) {
  // Handle both Locator objects and string selectors
  const button = typeof buttonSelector === 'string' ? page.locator(buttonSelector) : buttonSelector;
  await button.waitFor({ state: 'visible' });
  await button.click();
  
  // Wait for the expected change (e.g., navigation, element appearance)
  if (typeof expectedChange === 'string') {
    // If it's a URL pattern
    if (expectedChange.startsWith('/')) {
      await waitForNavigation(page, new RegExp(expectedChange));
    } else {
      // If it's a selector
      await page.waitForSelector(expectedChange, { timeout });
    }
  } else if (typeof expectedChange === 'function') {
    // If it's a custom condition
    await page.waitForFunction(expectedChange, {}, { timeout });
  } else if (expectedChange && expectedChange.constructor && expectedChange.constructor.name === 'RegExp') {
    // If it's a regex for URL
    await waitForNavigation(page, expectedChange);
  }
}

/**
 * Wait for toast/notification to appear and disappear
 */
async function waitForNotification(page, messagePattern, timeout = 5000) {
  // Wait for notification to appear
  const notification = page.locator('text=' + messagePattern).or(
    page.locator(`[role="alert"]:has-text("${messagePattern}")`)
  );
  
  await notification.waitFor({ state: 'visible', timeout });
  
  // Optionally wait for it to disappear (some notifications auto-hide)
  try {
    await notification.waitFor({ state: 'hidden', timeout: 3000 });
  } catch {
    // Notification might not auto-hide, that's okay
  }
}

/**
 * Safely interact with modal dialogs
 */
async function handleModal(page, triggerSelector, modalSelector, actionSelector) {
  // Click trigger
  await page.click(triggerSelector);
  
  // Wait for modal to appear
  await page.waitForSelector(modalSelector, { state: 'visible' });
  
  // Perform action in modal
  await page.click(actionSelector);
  
  // Wait for modal to close
  await page.waitForSelector(modalSelector, { state: 'hidden' });
}

/**
 * Wait for select/dropdown to be populated
 */
async function waitForSelectOptions(page, selectSelector, minimumOptions = 1, timeout = 5000) {
  await page.waitForSelector(selectSelector, { timeout });
  
  await page.waitForFunction(
    ({ selectSelector, minimumOptions }) => {
      const select = document.querySelector(selectSelector);
      if (!select) return false;
      
      const options = select.querySelectorAll('option');
      return options.length >= minimumOptions;
    },
    { selectSelector, minimumOptions },
    { timeout }
  );
}

/**
 * Generic retry mechanism for flaky operations
 */
async function retryOperation(operation, maxRetries = 3, delay = 1000) {
  let lastError;
  
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error;
      if (i < maxRetries - 1) {
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }
  
  throw lastError;
}

module.exports = {
  waitForStableElement,
  waitForFormSubmission,
  waitForNavigation,
  waitForTableRows,
  waitForApiCall,
  fillAndValidate,
  clickAndWaitForAction,
  waitForNotification,
  handleModal,
  waitForSelectOptions,
  retryOperation
};