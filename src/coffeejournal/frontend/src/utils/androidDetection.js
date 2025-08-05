// Android tablet dropdown fix utilities
// Addresses known issues with Headless UI dropdowns on Android tablets

export const isAndroid = () => {
  return /Android/i.test(navigator.userAgent);
};

export const isAndroidTablet = () => {
  const userAgent = navigator.userAgent.toLowerCase();
  return isAndroid() && !userAgent.includes('mobile');
};

// Enhanced Android tablet detection that works even in desktop mode
export const isAndroidTabletEnhanced = () => {
  // Method 1: Standard user agent detection
  if (isAndroidTablet()) {
    return true;
  }
  
  // Method 2: Check for Android-specific properties even in desktop mode
  const userAgent = navigator.userAgent.toLowerCase();
  if (userAgent.includes('android')) {
    return true;
  }
  
  // Method 3: Touch capabilities + screen size (tablets typically have larger screens)
  const hasTouchScreen = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
  const hasLargeScreen = window.screen.width >= 768 && window.screen.height >= 768;
  
  // Method 4: Platform detection (some Android devices report Linux)
  const platform = navigator.platform.toLowerCase();
  const isLinuxArm = platform.includes('linux') && (platform.includes('arm') || platform.includes('aarch'));
  
  // Method 5: Check for Android-specific browser features
  const hasAndroidFeatures = (
    'connection' in navigator || // Network Information API more common on Android
    'getBattery' in navigator || // Battery API more common on mobile
    window.DeviceMotionEvent !== undefined // Motion sensors
  );
  
  // Method 6: Viewport characteristics typical of tablets
  const screenRatio = Math.max(window.screen.width, window.screen.height) / Math.min(window.screen.width, window.screen.height);
  const isTabletRatio = screenRatio >= 1.2 && screenRatio <= 2.0; // Typical tablet aspect ratios
  
  // Method 7: Check for Brave browser specifically (has unique properties)
  const isBrave = navigator.brave && navigator.brave.isBrave;
  
  // Combine multiple signals for robust detection
  const touchAndScreen = hasTouchScreen && hasLargeScreen;
  const platformHints = isLinuxArm || hasAndroidFeatures;
  const viewportHints = isTabletRatio && window.screen.width >= 768;
  
  // If we have multiple positive signals, likely an Android tablet in desktop mode
  const confidenceScore = [
    touchAndScreen,
    platformHints, 
    viewportHints,
    isBrave // Brave on Android often uses desktop mode
  ].filter(Boolean).length;
  
  return confidenceScore >= 2;
};

// Get the most reliable Android tablet detection
export const isDefinitelyAndroidTablet = () => {
  const standardDetection = isAndroidTablet();
  const enhancedDetection = isAndroidTabletEnhanced();
  const result = standardDetection || enhancedDetection;
  
  // Debug logging for testing
  if (typeof window !== 'undefined' && window.console) {
    console.log('Android Tablet Detection:', {
      userAgent: navigator.userAgent,
      platform: navigator.platform,
      screenSize: `${window.screen.width}x${window.screen.height}`,
      touchScreen: 'ontouchstart' in window,
      maxTouchPoints: navigator.maxTouchPoints,
      brave: !!(navigator.brave && navigator.brave.isBrave),
      standardDetection,
      enhancedDetection,
      finalResult: result
    });
  }
  
  return result;
};

export const getBrowserInfo = () => {
  const userAgent = navigator.userAgent.toLowerCase();
  
  if (userAgent.includes('chrome') && !userAgent.includes('edg')) {
    return 'chrome';
  } else if (userAgent.includes('brave')) {
    return 'brave';
  } else if (userAgent.includes('firefox')) {
    return 'firefox';
  } else if (userAgent.includes('safari') && !userAgent.includes('chrome')) {
    return 'safari';
  }
  
  return 'unknown';
};

export const hasVirtualKeyboardAPI = () => {
  return 'virtualKeyboard' in navigator;
};

export const getViewportHeight = () => {
  // Try to get the most accurate viewport height
  if (window.visualViewport) {
    return window.visualViewport.height;
  }
  return window.innerHeight;
};

export const isVirtualKeyboardOpen = () => {
  if (window.visualViewport) {
    // If visual viewport is significantly smaller than window height, keyboard is likely open
    return window.visualViewport.height < window.innerHeight * 0.8;
  }
  
  // Fallback: check if viewport height changed significantly
  const currentHeight = window.innerHeight;
  const screenHeight = window.screen.height;
  return currentHeight < screenHeight * 0.8;
};

export const shouldDisableDropdownSearch = () => {
  // Disable searchable dropdowns on Android tablets in problematic browsers
  if (!isAndroidTablet()) return false;
  
  const browser = getBrowserInfo();
  
  // Known problematic combinations
  if (browser === 'chrome' || browser === 'brave') {
    return true;
  }
  
  return false;
};