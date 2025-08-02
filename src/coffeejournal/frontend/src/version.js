// Version info for the Coffee Journal frontend
// This file can be updated during build to include git info

export const version = {
  // This will be replaced during Docker build
  commit: process.env.REACT_APP_GIT_SHA || 'development',
  buildDate: process.env.REACT_APP_BUILD_DATE || new Date().toISOString(),
  version: process.env.REACT_APP_VERSION || '0.1.0'
};