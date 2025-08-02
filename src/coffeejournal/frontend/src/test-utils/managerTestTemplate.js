import '@testing-library/jest-dom';
import { renderWithProviders, testUtils, mockData, setupMocks, screen, waitFor, fireEvent } from './index';

/**
 * Creates a comprehensive test suite for LookupManager-based components
 * @param {Object} config - Test configuration
 * @param {React.Component} config.Component - The manager component to test
 * @param {String} config.componentName - Name for test descriptions
 * @param {String} config.apiEndpoint - API endpoint (e.g., 'bean_types')
 * @param {String} config.singularName - Singular name (e.g., 'Bean Type')
 * @param {Array} config.customFields - Array of custom fields beyond defaults
 * @param {Function} config.mockDataGenerator - Function to generate mock data
 * @returns {Function} Test suite function
 */
export const createManagerTestSuite = (config) => {
  const {
    Component,
    componentName,
    apiEndpoint,
    singularName,
    customFields = [],
    mockDataGenerator = mockData.beanType
  } = config;

  return () => {
    // Mock fetch for API calls
    global.fetch = jest.fn();

    beforeEach(() => {
      fetch.mockClear();
      
      // Setup default mock data
      const defaultItems = [
        mockDataGenerator({ id: 1, name: 'Item One' }),
        mockDataGenerator({ id: 2, name: 'Item Two' })
      ];
      
      setupMocks.lookupManager(defaultItems);
    });

    describe('Rendering and Navigation', () => {
      test('renders page title and main components', async () => {
        renderWithProviders(<Component />);
        
        await testUtils.testBasicRendering(`${singularName}s`);
      });

      test('displays items in table', async () => {
        renderWithProviders(<Component />);
        
        await testUtils.waitForElement('item-row-1');
        expect(testUtils.getByTestId('item-row-2')).toBeInTheDocument();
        
        // Check content is displayed
        expect(screen.getByText('Item One')).toBeInTheDocument();
        expect(screen.getByText('Item Two')).toBeInTheDocument();
      });

      test('shows empty state when no items', async () => {
        setupMocks.lookupManager([]); // Empty array
        
        renderWithProviders(<Component />);
        
        await testUtils.waitForText(`No ${singularName.toLowerCase()}s found`);
      });
    });

    describe('Form Interactions', () => {
      test('shows form when add button is clicked', async () => {
        renderWithProviders(<Component />);
        
        await testUtils.waitForElement('add-item-btn');
        testUtils.openAddForm();
        
        // Check form is displayed
        expect(screen.getByLabelText(/Name/)).toBeInTheDocument();
        expect(testUtils.getByTestId(`${apiEndpoint}-name-input`)).toBeInTheDocument();
        expect(testUtils.getByTestId('create-item-btn')).toBeInTheDocument();
      });

      test('creates new item with form data', async () => {
        const newItem = mockDataGenerator({ id: 3, name: 'New Item' });
        setupMocks.createItem(newItem);
        
        renderWithProviders(<Component />);
        
        await testUtils.waitForElement('add-item-btn');
        testUtils.openAddForm();
        
        // Fill in required fields
        await testUtils.testFormInteraction(`${apiEndpoint}-name-input`, 'New Item');
        
        // Fill custom fields if they exist
        for (const field of customFields) {
          if (field.required) {
            testUtils.fillInput(`${apiEndpoint}-${field.name}-input`, `Test ${field.label}`);
          }
        }
        
        await testUtils.submitForm('create-item-btn');
        
        await waitFor(() => {
          expect(fetch).toHaveBeenCalledWith(
            `/api/${apiEndpoint}`,
            expect.objectContaining({
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: expect.stringContaining('New Item')
            })
          );
        });
      });

      test('validates required fields', async () => {
        renderWithProviders(<Component />);
        
        await testUtils.waitForElement('add-item-btn');
        testUtils.openAddForm();
        
        // Try to submit without filling required fields
        testUtils.clickButton('create-item-btn');
        
        // Should show validation error
        await testUtils.waitForText('Name is required');
      });
    });

    describe('Item Management', () => {
      test('enters edit mode when edit button is clicked', async () => {
        renderWithProviders(<Component />);
        
        await testUtils.waitForElement('edit-item-one-btn');
        testUtils.clickEditButton('Item One');
        
        // Form should show in edit mode with pre-filled data
        expect(screen.getByDisplayValue('Item One')).toBeInTheDocument();
        expect(testUtils.getByTestId('update-item-btn')).toBeInTheDocument();
      });

      test('updates item successfully', async () => {
        const updatedItem = mockDataGenerator({ id: 1, name: 'Updated Item' });
        setupMocks.updateItem(updatedItem);
        
        renderWithProviders(<Component />);
        
        await testUtils.waitForElement('edit-item-one-btn');
        testUtils.clickEditButton('Item One');
        
        // Modify the name
        testUtils.fillInput(`${apiEndpoint}-name-input`, 'Updated Item');
        await testUtils.submitForm('update-item-btn');
        
        await waitFor(() => {
          expect(fetch).toHaveBeenCalledWith(
            `/api/${apiEndpoint}/1`,
            expect.objectContaining({
              method: 'PUT',
              body: expect.stringContaining('Updated Item')
            })
          );
        });
      });

      test('handles delete confirmation flow', async () => {
        setupMocks.deleteItem();
        
        renderWithProviders(<Component />);
        
        await testUtils.waitForElement('delete-item-one-btn');
        testUtils.clickDeleteButton('Item One');
        
        // Should trigger usage check API call
        await waitFor(() => {
          expect(fetch).toHaveBeenCalledWith(`/api/${apiEndpoint}/1/usage`);
        });
      });

      test('prevents deletion when item is in use', async () => {
        setupMocks.deleteItem({ in_use: true, usage_count: 5 });
        
        renderWithProviders(<Component />);
        
        await testUtils.waitForElement('delete-item-one-btn');
        testUtils.clickDeleteButton('Item One');
        
        // Should show usage warning
        await testUtils.waitForText('This item is currently being used');
      });
    });

    describe('Accessibility', () => {
      test('form labels are properly associated with inputs', async () => {
        renderWithProviders(<Component />);
        
        await testUtils.waitForElement('add-item-btn');
        testUtils.openAddForm();
        
        // Test proper label association for all fields
        const allFields = [
          { name: 'name', label: 'Name' },
          { name: 'short_form', label: 'Short Form' },
          { name: 'description', label: 'Description' },
          ...customFields
        ];
        
        for (const field of allFields) {
          const labelElement = screen.getByText(new RegExp(field.label));
          const inputElement = testUtils.getByTestId(`${apiEndpoint}-${field.name}-input`);
          
          expect(labelElement).toBeInTheDocument();
          expect(inputElement).toBeInTheDocument();
          expect(inputElement.id).toBe(`${apiEndpoint}-${field.name}`);
        }
      });

      test('buttons have proper ARIA labels', async () => {
        renderWithProviders(<Component />);
        
        await testUtils.testBasicRendering(`${singularName}s`);
        
        // Check button accessibility
        const addButton = testUtils.getByTestId('add-item-btn');
        const backButton = testUtils.getByTestId('back-to-settings-btn');
        
        expect(addButton).toHaveAttribute('title', `Add ${singularName}`);
        expect(backButton).toHaveAttribute('title', 'Back to Settings');
      });
    });

    describe('Error Handling', () => {
      test('displays error when API call fails', async () => {
        fetch.mockRejectedValueOnce(new Error('Network error'));
        
        renderWithProviders(<Component />);
        
        await testUtils.waitForText(`Failed to fetch ${singularName.toLowerCase()}s`);
      });

      test('handles form submission errors', async () => {
        testUtils.mockFetchError('Validation failed');
        
        renderWithProviders(<Component />);
        
        await testUtils.waitForElement('add-item-btn');
        testUtils.openAddForm();
        testUtils.fillInput(`${apiEndpoint}-name-input`, 'Test Item');
        await testUtils.submitForm('create-item-btn');
        
        await testUtils.waitForText('Failed to create');
      });
    });

    describe('Loading States', () => {
      test('shows loading state during data fetch', () => {
        // Mock slow API response
        fetch.mockImplementation(() => new Promise(() => {}));
        
        renderWithProviders(<Component />);
        
        expect(screen.getByText(`Loading ${singularName.toLowerCase()}s...`)).toBeInTheDocument();
      });

      test('shows loading state during form submission', async () => {
        // Mock slow submission
        fetch.mockImplementation(() => 
          new Promise(resolve => 
            setTimeout(() => resolve(mockData.apiResponse({ id: 3 })), 100)
          )
        );
        
        renderWithProviders(<Component />);
        
        await testUtils.waitForElement('add-item-btn');
        testUtils.openAddForm();
        testUtils.fillInput(`${apiEndpoint}-name-input`, 'Test');
        testUtils.clickButton('create-item-btn');
        
        // Should show loading button
        const submitButton = testUtils.getByTestId('create-item-btn');
        expect(submitButton).toBeDisabled();
      });
    });
  };
};

/**
 * Utility to quickly generate test files for manager components
 */
export const generateManagerTest = (config) => {
  const { componentName, importPath } = config;
  
  return `
import ${componentName} from '${importPath}';
import { createManagerTestSuite } from '../test-utils/managerTestTemplate';

describe('${componentName} Component', createManagerTestSuite({
  Component: ${componentName},
  componentName: '${componentName}',
  ...${JSON.stringify(config, null, 2)}
}));
  `.trim();
};