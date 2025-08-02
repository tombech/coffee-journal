# 🧪 **Comprehensive Testing Guide for Coffee Journal Frontend**

## 📋 **Testing Strategy Overview**

### **Testing Pyramid**
```
    🔺 E2E Tests (Cypress)
   🟨🟨 Integration Tests 
  🟩🟩🟩🟩 Unit Tests
```

### **Testing Layers**
1. **Unit Tests**: Individual components, utilities, hooks
2. **Integration Tests**: Component + API interactions
3. **E2E Tests**: Full user workflows

---

## 🎯 **Test Selectors Priority**

### **1. ✅ PREFERRED: data-testid**
```javascript
// ✅ BEST - Stable, semantic, resistant to changes
screen.getByTestId('add-product-btn')
screen.getByTestId('product-name-input')
screen.getByTestId('roaster-autocomplete')
```

### **2. ✅ GOOD: Accessibility Selectors**
```javascript
// ✅ GOOD - Tests accessibility compliance
screen.getByLabelText('Product Name')
screen.getByRole('button', { name: /add product/i })
screen.getByPlaceholderText('Enter product name')
```

### **3. ⚠️ ACCEPTABLE: Semantic Queries**
```javascript
// ⚠️ OK - But can break with text changes
screen.getByText('Add Product')
screen.getByDisplayValue('Current Value')
```

### **4. ❌ AVOID: Implementation Details**
```javascript
// ❌ BAD - Breaks with structure changes
document.querySelector('.product-form')
container.firstChild
```

---

## 🛠️ **Component Testing Patterns**

### **Form Components**
```javascript
// ✅ Test form accessibility
test('form labels are properly associated', () => {
  render(<ProductForm />);
  
  const nameLabel = screen.getByText(/product name/i);
  const nameInput = screen.getByTestId('product-name-input');
  
  expect(nameLabel).toBeInTheDocument();
  expect(nameInput).toHaveAccessibleName(/product name/i);
});

// ✅ Test form validation
test('validates required fields', async () => {
  render(<ProductForm />);
  
  const submitBtn = screen.getByTestId('add-product-btn');
  fireEvent.click(submitBtn);
  
  await waitFor(() => {
    expect(screen.getByText(/name is required/i)).toBeInTheDocument();
  });
});

// ✅ Test form submission
test('submits form with correct data', async () => {
  const mockSubmit = jest.fn();
  render(<ProductForm onSubmit={mockSubmit} />);
  
  testUtils.fillInput('product-name-input', 'Test Product');
  testUtils.clickButton('add-product-btn');
  
  await waitFor(() => {
    expect(mockSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        product_name: 'Test Product'
      })
    );
  });
});
```

### **List/Table Components**
```javascript
// ✅ Test table rendering
test('displays items in table', async () => {
  setupMocks.lookupManager([
    mockData.product({ name: 'Product 1' }),
    mockData.product({ name: 'Product 2' })
  ]);
  
  render(<ProductList />);
  
  await waitFor(() => {
    expect(screen.getByTestId('item-row-1')).toBeInTheDocument();
    expect(screen.getByTestId('item-row-2')).toBeInTheDocument();
  });
});

// ✅ Test item actions
test('edit button opens edit mode', async () => {
  render(<ProductList />);
  
  await waitFor(() => {
    testUtils.clickEditButton('Product 1');
  });
  
  expect(screen.getByTestId('update-item-btn')).toBeInTheDocument();
});
```

### **Autocomplete/Search Components**
```javascript
// ✅ Test search functionality
test('searches and displays results', async () => {
  const mockResults = [mockData.roaster({ name: 'Blue Bottle' })];
  testUtils.mockFetchSuccess(mockResults);
  
  render(<HeadlessAutocomplete lookupType="roasters" />);
  
  const input = screen.getByTestId('roaster-autocomplete');
  fireEvent.change(input, { target: { value: 'blue' } });
  
  await waitFor(() => {
    expect(screen.getByText('Blue Bottle')).toBeInTheDocument();
  });
});
```

---

## 🔧 **Testing Utilities Usage**

### **Basic Interactions**
```javascript
import { testUtils, renderWithProviders } from '../test-utils';

// Render with providers
renderWithProviders(<Component />);

// Form interactions
testUtils.fillInput('name-input', 'Test Value');
testUtils.checkCheckbox('decaf-checkbox');
testUtils.clickButton('submit-btn');

// Wait for elements
await testUtils.waitForElement('success-message');
await testUtils.waitForText('Product created');

// Mock API responses
testUtils.mockFetchSuccess({ id: 1, name: 'Test' });
testUtils.mockFetchError('Validation failed');
```

### **Complex Scenarios**
```javascript
// Test complete workflow
test('creates product end-to-end', async () => {
  // 1. Setup
  testUtils.mockFetchSuccess(mockData.product());
  
  // 2. Render
  renderWithProviders(<ProductForm />);
  
  // 3. Fill form
  testUtils.fillInput('product-name-input', 'New Coffee');
  testUtils.fillInput('roaster-autocomplete', 'Blue Bottle');
  testUtils.checkCheckbox('decaf-checkbox');
  
  // 4. Submit
  await testUtils.submitForm('add-product-btn');
  
  // 5. Verify
  await testUtils.waitForText('Product created successfully');
});
```

---

## 🚀 **Advanced Testing Techniques**

### **Custom Hooks Testing**
```javascript
import { renderHook, act } from '@testing-library/react';

test('useProductForm hook manages state correctly', () => {
  const { result } = renderHook(() => useProductForm());
  
  act(() => {
    result.current.updateField('name', 'Test Product');
  });
  
  expect(result.current.formData.name).toBe('Test Product');
});
```

### **Context/Provider Testing**
```javascript
test('ToastProvider displays toast messages', async () => {
  const TestComponent = () => {
    const { addToast } = useToast();
    return (
      <button onClick={() => addToast('Success!', 'success')}>
        Add Toast
      </button>
    );
  };
  
  renderWithProviders(<TestComponent />);
  
  fireEvent.click(screen.getByText('Add Toast'));
  
  await waitFor(() => {
    expect(screen.getByText('Success!')).toBeInTheDocument();
  });
});
```

### **Error Boundary Testing**
```javascript
test('error boundary catches component errors', () => {
  const ThrowError = () => {
    throw new Error('Test error');
  };
  
  render(
    <ErrorBoundary>
      <ThrowError />
    </ErrorBoundary>
  );
  
  expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
});
```

---

## 📊 **Testing Metrics & Goals**

### **Coverage Targets**
- **Unit Tests**: 90%+ line coverage
- **Integration Tests**: All critical user paths
- **E2E Tests**: Main workflows (create, edit, delete, search)

### **Performance Testing**
```javascript
test('component renders within performance budget', () => {
  const startTime = performance.now();
  
  render(<ComplexComponent />);
  
  const endTime = performance.now();
  expect(endTime - startTime).toBeLessThan(100); // 100ms budget
});
```

### **Accessibility Testing**
```javascript
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

test('component has no accessibility violations', async () => {
  const { container } = render(<Component />);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

---

## 🎯 **Test Organization**

### **File Structure**
```
src/
├── components/
│   ├── ProductForm.js
│   └── __tests__/
│       ├── ProductForm.test.js
│       ├── ProductForm.integration.test.js
│       └── ProductForm.accessibility.test.js
├── test-utils/
│   ├── index.js                    # Main utilities
│   ├── managerTestTemplate.js      # Reusable templates
│   ├── mockData.js                # Mock data generators
│   └── testingGuide.md            # This guide
└── cypress/
    └── e2e/
        └── product-management.cy.js
```

### **Test Naming Conventions**
```javascript
// ✅ GOOD - Descriptive, behavior-focused
test('displays validation error when required field is empty')
test('submits form and redirects to product list on success')
test('filters products by roaster when dropdown changes')

// ❌ BAD - Implementation-focused
test('calls handleSubmit')
test('sets state correctly')
```

---

## 🚦 **CI/CD Integration**

### **Test Scripts**
```json
{
  "scripts": {
    "test": "react-scripts test",
    "test:coverage": "npm test -- --coverage --watchAll=false",
    "test:ci": "npm run test:coverage -- --ci",
    "cypress:run": "cypress run",
    "test:e2e": "start-server-and-test start http://localhost:3000 cypress:run"
  }
}
```

### **GitHub Actions Example**
```yaml
name: Frontend Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npm run test:ci
      - run: npm run test:e2e
```

---

## 📚 **Resources & Tools**

### **Essential Libraries**
- `@testing-library/react` - Component testing
- `@testing-library/jest-dom` - Custom matchers
- `@testing-library/user-event` - User interactions
- `jest-axe` - Accessibility testing
- `cypress` - E2E testing

### **VS Code Extensions**
- Jest Test Explorer
- Testing Library Snippets
- ES6 Mocha Snippets

### **Debugging Tips**
```javascript
// 🔍 Debug rendered component
screen.debug(); // Prints entire DOM
screen.debug(screen.getByTestId('my-element')); // Prints specific element

// 🔍 Check what queries are available
screen.logTestingPlaygroundURL(); // Opens Testing Playground

// 🔍 Pause test execution
await screen.findByText('Loading...'); // Wait for async operations
```

---

## ✅ **Quick Checklist**

### **Before Writing Tests**
- [ ] Component has proper `data-testid` attributes
- [ ] Form labels have `htmlFor` attributes
- [ ] Buttons have descriptive titles/ARIA labels
- [ ] Loading/error states are testable

### **Test Quality Checklist**
- [ ] Tests focus on user behavior, not implementation
- [ ] Tests use stable selectors (testid, accessibility)
- [ ] Tests are isolated and don't depend on each other
- [ ] Mock data is realistic and consistent
- [ ] Async operations are properly awaited
- [ ] Error scenarios are tested

### **Before Deployment**
- [ ] All tests pass (`npm run test:ci`)
- [ ] Coverage meets targets (`npm run test:coverage`)
- [ ] E2E tests pass (`npm run test:e2e`)
- [ ] No accessibility violations
- [ ] Performance budgets met

---

**🎯 Remember: Good tests give you confidence to refactor and ship features quickly!**