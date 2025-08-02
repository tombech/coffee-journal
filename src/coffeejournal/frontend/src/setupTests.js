// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

// Mock ResizeObserver which is used by Headless UI v2 - REQUIRED for v2
class ResizeObserverMock {
  constructor(callback) {
    this.callback = callback;
  }
  
  observe = jest.fn();
  unobserve = jest.fn();
  disconnect = jest.fn();
}

global.ResizeObserver = ResizeObserverMock;

// Mock scrollIntoView which is not available in test environment
Element.prototype.scrollIntoView = jest.fn();

// Mock matchMedia which is not available in test environment
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock IntersectionObserver with proper constructor and methods
class IntersectionObserverMock {
  constructor(callback, options = {}) {
    this.callback = callback;
    this.options = options;
  }
  
  observe = jest.fn();
  unobserve = jest.fn();
  disconnect = jest.fn();
}

// Ensure the mock is available globally and behaves like a proper class
global.IntersectionObserver = IntersectionObserverMock;
window.IntersectionObserver = IntersectionObserverMock;

// Mock MutationObserver for HeadlessUI
class MutationObserverMock {
  constructor(callback) {
    this.callback = callback;
  }
  
  observe = jest.fn();
  disconnect = jest.fn();
  takeRecords = jest.fn(() => []);
}

global.MutationObserver = MutationObserverMock;
window.MutationObserver = MutationObserverMock;

// Store original getComputedStyle
const originalGetComputedStyle = window.getComputedStyle;

// Mock getComputedStyle for @testing-library/user-event and dom-accessibility-api
// This comprehensive mock ensures dom-accessibility-api can properly check element visibility
window.getComputedStyle = jest.fn().mockImplementation((element, pseudoElt) => {
  // Create a robust CSSStyleDeclaration mock that satisfies dom-accessibility-api requirements
  const createRobustStyleObject = () => {
    // Default style values that make elements visible and accessible
    const defaultStyles = {
      'pointer-events': 'auto',
      'visibility': 'visible',
      'display': 'block',
      'opacity': '1',
      'overflow': 'visible',
      'position': 'static',
      'transform': 'none',
      'width': '100px',
      'height': '100px',
      'clip': 'auto',
      'clip-path': 'none',
      'left': '0px',
      'top': '0px',
      'right': 'auto',
      'bottom': 'auto'
    };
    
    // Create style object with proper method implementations
    const styleObject = {
      // Core CSSStyleDeclaration methods
      getPropertyValue: jest.fn((prop) => {
        // Normalize property name (handle both camelCase and kebab-case)
        const normalizedProp = prop.replace(/([A-Z])/g, '-$1').toLowerCase();
        
        // Return value from defaults or from the object itself
        if (defaultStyles[normalizedProp] !== undefined) {
          return defaultStyles[normalizedProp];
        }
        if (styleObject[prop] !== undefined) {
          return String(styleObject[prop]);
        }
        if (styleObject[normalizedProp] !== undefined) {
          return String(styleObject[normalizedProp]);
        }
        
        // Default to empty string for unknown properties
        return '';
      }),
      
      setProperty: jest.fn((property, value, priority) => {
        styleObject[property] = value;
      }),
      
      removeProperty: jest.fn((property) => {
        const oldValue = styleObject[property] || '';
        delete styleObject[property];
        return String(oldValue);
      }),
      
      getPropertyPriority: jest.fn((property) => ''),
      
      // Length property for iteration
      get length() {
        return Object.keys(this).filter(key => 
          typeof this[key] !== 'function' && 
          !['length'].includes(key)
        ).length;
      },
      
      // Item method for accessing by index
      item: jest.fn((index) => {
        const keys = Object.keys(styleObject).filter(key => 
          typeof styleObject[key] !== 'function' && 
          !['length'].includes(key)
        );
        return keys[index] || '';
      })
    };
    
    // Add default styles as direct properties (for direct property access)
    Object.assign(styleObject, defaultStyles);
    
    // Add common CSS properties with default values to prevent undefined access
    const commonCssProps = [
      'alignContent', 'alignItems', 'alignSelf', 'background', 'backgroundColor', 
      'border', 'borderColor', 'borderStyle', 'borderWidth', 'borderRadius',
      'boxShadow', 'color', 'cursor', 'font', 'fontFamily', 'fontSize', 'fontWeight',
      'lineHeight', 'margin', 'marginTop', 'marginRight', 'marginBottom', 'marginLeft',
      'padding', 'paddingTop', 'paddingRight', 'paddingBottom', 'paddingLeft',
      'textAlign', 'textDecoration', 'zIndex'
    ];
    
    commonCssProps.forEach(prop => {
      if (!(prop in styleObject)) {
        styleObject[prop] = '';
      }
    });
    
    return styleObject;
  };

  // Handle pseudo-elements properly (this is often where the undefined error occurs)
  if (pseudoElt) {
    // Return a complete style object for pseudo-elements too
    // This prevents the "Cannot read properties of undefined" error
    const pseudoStyleObject = {
      getPropertyValue: jest.fn((prop) => {
        // For pseudo-elements, return appropriate defaults
        switch (prop) {
          case 'content': return '""';
          case 'display': return 'inline';
          case 'visibility': return 'visible';
          case 'opacity': return '1';
          default: return '';
        }
      }),
      setProperty: jest.fn(),
      removeProperty: jest.fn(() => ''),
      getPropertyPriority: jest.fn(() => ''),
      length: 0,
      item: jest.fn(() => ''),
      // Add some basic properties for pseudo-elements
      content: '""',
      display: 'inline',
      visibility: 'visible',
      opacity: '1'
    };
    
    return pseudoStyleObject;
  }
  
  return createRobustStyleObject();
});

// Ensure document.defaultView also has the mock
if (document.defaultView) {
  document.defaultView.getComputedStyle = window.getComputedStyle;
}

// Happy-DOM provides a more complete DOM implementation, so we can remove accessibility API mocking

// Mock getBoundingClientRect comprehensively for HeadlessUI v2
const mockBoundingClientRect = jest.fn(() => ({
  width: 120,
  height: 40,
  top: 0,
  left: 0,
  bottom: 40,
  right: 120,
  x: 0,
  y: 0,
  toJSON: jest.fn()
}));

// Apply to all possible element types and ensure they never return undefined
Element.prototype.getBoundingClientRect = mockBoundingClientRect;
HTMLElement.prototype.getBoundingClientRect = mockBoundingClientRect;
HTMLDivElement.prototype.getBoundingClientRect = mockBoundingClientRect;
HTMLInputElement.prototype.getBoundingClientRect = mockBoundingClientRect;
HTMLButtonElement.prototype.getBoundingClientRect = mockBoundingClientRect;
HTMLUListElement.prototype.getBoundingClientRect = mockBoundingClientRect;
HTMLLIElement.prototype.getBoundingClientRect = mockBoundingClientRect;

// Additional mock for floating-ui compatibility
global.Element.prototype.getBoundingClientRect = mockBoundingClientRect;

// Mock animation frame methods - required for HeadlessUI components
global.requestAnimationFrame = jest.fn((callback) => setTimeout(callback, 0));
global.cancelAnimationFrame = jest.fn(clearTimeout);

// Mock HTMLElement.offsetParent
Object.defineProperty(HTMLElement.prototype, 'offsetParent', {
  get: jest.fn(() => null),
});

// Mock floating-ui dependencies for HeadlessUI v2
global.DOMRect = jest.fn().mockImplementation(() => ({
  width: 120,
  height: 40,
  top: 0,
  left: 0,
  bottom: 40,
  right: 120,
  x: 0,
  y: 0,
  toJSON: jest.fn()
}));

// getComputedStyle is already mocked above

// Set up global DOM mocks for HeadlessUI v2 compatibility
beforeAll(() => {
  // Mock document.createRange for HeadlessUI
  if (!document.createRange) {
    document.createRange = () => {
      const range = new Range();
      range.getBoundingClientRect = mockBoundingClientRect;
      range.getClientRects = () => ({
        item: () => null,
        length: 0,
        [Symbol.iterator]: jest.fn()
      });
      return range;
    };
  }
  
  // Mock element style property comprehensively for dom-accessibility-api
  const createStyleObject = () => ({
    // Style properties for dom-accessibility-api
    pointerEvents: 'auto',
    display: 'block',
    visibility: 'visible',
    opacity: '1',
    transform: 'none',
    position: 'static',
    overflow: 'visible',
    clip: 'auto',
    clipPath: 'none',
    width: '100px',
    height: '100px',
    left: '0px',
    top: '0px',
    right: 'auto',
    bottom: 'auto',
    margin: '0px',
    padding: '0px',
    border: '0px',
    fontSize: '16px',
    fontFamily: 'Arial',
    color: 'rgb(0, 0, 0)',
    backgroundColor: 'rgba(0, 0, 0, 0)',
    zIndex: 'auto',
    
    // Essential CSSStyleDeclaration methods that React needs
    setProperty: jest.fn((property, value, priority) => {
      // Dynamically set the property on this object
      this[property] = value;
    }),
    removeProperty: jest.fn((property) => {
      delete this[property];
      return '';
    }),
    getPropertyValue: jest.fn((property) => {
      return this[property] || '';
    }),
    getPropertyPriority: jest.fn(() => '')
  });

  // Apply comprehensive style mocking to all element prototypes
  const elementPrototypes = [
    Element.prototype,
    HTMLElement.prototype,
    HTMLImageElement.prototype,
    HTMLDivElement.prototype,
    HTMLSpanElement.prototype,
    HTMLInputElement.prototype,
    HTMLButtonElement.prototype,
    HTMLAnchorElement.prototype
  ];

  elementPrototypes.forEach(prototype => {
    if (prototype) {
      Object.defineProperty(prototype, 'style', {
        value: createStyleObject(),
        writable: true,
        configurable: true
      });
    }
  });
});

// Suppress console logs during tests for cleaner output
const originalConsoleError = console.error;
const originalConsoleWarn = console.warn;

beforeEach(() => {
  console.error = jest.fn();
  console.warn = jest.fn();
});

afterEach(() => {
  console.error = originalConsoleError;
  console.warn = originalConsoleWarn;
});
