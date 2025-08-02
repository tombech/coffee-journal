// Standardized icon configuration for consistent UI
export const ICONS = {
  // Actions
  SAVE: '💾',      // Save/Update (disk icon - universally recognized)
  CREATE: '➕',     // Create new item
  EDIT: '✏️',      // Edit existing item
  DELETE: '🗑️',   // Delete item
  CANCEL: '❌',    // Cancel operation
  
  // Navigation
  BACK: '←',       // Go back (simple arrow)
  FORWARD: '→',    // Go forward
  
  // Status
  LOADING: '⏳',   // Loading/Processing
  SUCCESS: '✅',   // Success state
  ERROR: '❌',     // Error state
  WARNING: '⚠️',   // Warning state
  
  // Content
  SETTINGS: '⚙️',  // Settings/Configuration
  STATS: '📊',     // Statistics/Charts
  STAR: '⭐',      // Default/Favorite
  SEARCH: '🔍',    // Search functionality
  FILTER: '🔽',    // Filter dropdown
  VIEW: '👁️',      // View/Navigate to details
  
  // Content types
  CALENDAR: '📅',  // Date/Calendar
  TIME: '🕐',      // Time
  NOTES: '📝',     // Notes/Text content
  IMAGE: '🖼️',     // Images
  
  // Special states
  DEFAULT: '⭐',   // Default item marker
  DUPLICATE: '📋', // Duplicate/Copy functionality
};

// Helper function to get icon with fallback
export const getIcon = (iconName, fallback = '?') => {
  return ICONS[iconName] || fallback;
};