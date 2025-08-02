const path = require('path');

module.exports = {
  // Override Jest configuration to use Happy-DOM
  jest: (config) => {
    console.log('Jest config override called');
    console.log('Original testEnvironment:', config.testEnvironment);
    
    // Set Happy-DOM as the test environment
    config.testEnvironment = '@happy-dom/jest-environment';
    
    // Keep existing Jest configuration
    config.transformIgnorePatterns = [
      "node_modules/(?!(dom-accessibility-api)/)"
    ];
    
    config.moduleNameMapper = {
      ...config.moduleNameMapper,
      "\\.(css|less|scss|sass)$": "identity-obj-proxy"
    };
    
    console.log('New testEnvironment:', config.testEnvironment);
    
    return config;
  }
};