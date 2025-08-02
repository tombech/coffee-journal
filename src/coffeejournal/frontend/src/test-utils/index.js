import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ToastProvider } from '../components/Toast';

/**
 * Custom render function that includes all providers needed for testing
 * @param {React.Component} ui - Component to render
 * @param {Object} options - Additional options
 * @param {String} options.route - Initial route for MemoryRouter
 * @param {Array} options.routes - Array of routes for MemoryRouter
 * @returns {Object} RTL render result
 */
export const renderWithProviders = (ui, { route = '/', routes = [route], ...options } = {}) => {
  function Wrapper({ children }) {
    return (
      <MemoryRouter initialEntries={routes} initialIndex={0}>
        <ToastProvider>
          {children}
        </ToastProvider>
      </MemoryRouter>
    );
  }

  return render(ui, { wrapper: Wrapper, ...options });
};

/**
 * Testing utilities for common patterns
 */
export const testUtils = {
  // Selector utilities
  getByTestId: (testId) => screen.getByTestId(testId),
  queryByTestId: (testId) => screen.queryByTestId(testId),
  findByTestId: async (testId) => await screen.findByTestId(testId),
  
  // Form utilities
  fillInput: (testId, value) => {
    const input = screen.getByTestId(testId);
    fireEvent.change(input, { target: { value } });
    return input;
  },
  
  checkCheckbox: (testId) => {
    const checkbox = screen.getByTestId(testId);
    fireEvent.click(checkbox);
    return checkbox;
  },
  
  clickButton: (testId) => {
    const button = screen.getByTestId(testId);
    fireEvent.click(button);
    return button;
  },
  
  // Wait utilities
  waitForElement: async (testId, timeout = 1000) => {
    return await waitFor(() => {
      expect(screen.getByTestId(testId)).toBeInTheDocument();
    }, { timeout });
  },
  
  waitForText: async (text, timeout = 1000) => {
    return await waitFor(() => {
      expect(screen.getByText(text)).toBeInTheDocument();
    }, { timeout });
  },
  
  // Table utilities
  getTableRow: (itemId) => screen.getByTestId(`item-row-${itemId}`),
  clickEditButton: (itemName) => {
    const slug = itemName.toLowerCase().replace(/\\s+/g, '-');
    return testUtils.clickButton(`edit-${slug}-btn`);
  },
  clickDeleteButton: (itemName) => {
    const slug = itemName.toLowerCase().replace(/\\s+/g, '-');
    return testUtils.clickButton(`delete-${slug}-btn`);
  },
  
  // Form submission utilities
  submitForm: async (formTestId = 'create-item-btn') => {
    testUtils.clickButton(formTestId);
    await waitFor(() => {
      // Wait for any loading states to clear
    });
  },
  
  // Mock utilities
  mockFetchSuccess: (data) => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => data
    });
  },
  
  mockFetchError: (error = 'Network error') => {
    global.fetch.mockRejectedValueOnce(new Error(error));
  },
  
  // Lookup manager utilities
  openAddForm: () => testUtils.clickButton('add-item-btn'),
  closeForm: () => testUtils.clickButton('cancel-form-btn'),
  backToSettings: () => testUtils.clickButton('back-to-settings-btn'),
  
  // Common test patterns
  testBasicRendering: async (expectedTitle, expectedTable = true) => {
    await testUtils.waitForText(expectedTitle);
    expect(screen.getByTestId('add-item-btn')).toBeInTheDocument();
    expect(screen.getByTestId('back-to-settings-btn')).toBeInTheDocument();
    if (expectedTable) {
      expect(screen.getByTestId('items-table')).toBeInTheDocument();
    }
  },
  
  testFormInteraction: async (inputTestId, value) => {
    testUtils.openAddForm();
    await testUtils.waitForElement(inputTestId);
    testUtils.fillInput(inputTestId, value);
    const input = screen.getByTestId(inputTestId);
    expect(input).toHaveValue(value);
  }
};

/**
 * Custom matchers for common testing patterns
 */
export const customMatchers = {
  toBeVisibleAndEnabled: (element) => {
    expect(element).toBeInTheDocument();
    expect(element).toBeVisible();
    expect(element).toBeEnabled();
  },
  
  toHaveProperFormLabel: (labelText, inputTestId) => {
    const label = screen.getByText(new RegExp(labelText));
    const input = screen.getByTestId(inputTestId);
    expect(label).toBeInTheDocument();
    expect(input).toBeInTheDocument();
    // Check that label has proper htmlFor attribute
    const expectedId = inputTestId.replace('-input', '').replace(/-/g, '-');
    expect(input.id).toBeTruthy();
  }
};

/**
 * Mock data generators for consistent testing
 */
export const mockData = {
  beanType: (overrides = {}) => ({
    id: 1,
    name: 'Arabica',
    short_form: 'AR',
    description: 'High quality coffee beans',
    species: 'Coffea arabica',
    ...overrides
  }),
  
  roaster: (overrides = {}) => ({
    id: 1,
    name: 'Blue Bottle Coffee',
    short_form: 'BBC',
    description: 'Premium coffee roaster',
    ...overrides
  }),
  
  product: (overrides = {}) => ({
    id: 1,
    product_name: 'Test Coffee',
    roaster: mockData.roaster(),
    bean_type: [mockData.beanType()],
    rating: 4.5,
    ...overrides
  }),
  
  // Mock API responses
  apiResponse: (data, ok = true) => ({
    ok,
    json: async () => data
  }),
  
  apiError: (message = 'API Error', status = 500) => ({
    ok: false,
    status,
    json: async () => ({ message })
  })
};

/**
 * Setup helpers for common test scenarios
 */
export const setupMocks = {
  // Setup standard lookup manager mocks
  lookupManager: (items = []) => {
    global.fetch.mockResolvedValueOnce(mockData.apiResponse(items));
  },
  
  // Setup CRUD operation mocks
  createItem: (item) => {
    global.fetch.mockResolvedValueOnce(mockData.apiResponse(item));
  },
  
  updateItem: (item) => {
    global.fetch.mockResolvedValueOnce(mockData.apiResponse(item));
  },
  
  deleteItem: (usageInfo = { in_use: false, usage_count: 0 }) => {
    // First call - usage check
    global.fetch.mockResolvedValueOnce(mockData.apiResponse(usageInfo));
    // Second call - actual deletion
    global.fetch.mockResolvedValueOnce(mockData.apiResponse({ success: true }));
  }
};

// Re-export commonly used testing library functions
export {
  render,
  screen,
  fireEvent,
  waitFor,
  within
} from '@testing-library/react';

export { default as userEvent } from '@testing-library/user-event';