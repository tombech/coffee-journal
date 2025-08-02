const { exec } = require('child_process');
const { promisify } = require('util');
const execAsync = promisify(exec);

async function globalSetup() {
  console.log('🔧 Running global test setup...');
  
  // Step 1: Clean up any leftover test user data
  try {
    console.log('🧹 Cleaning up leftover test user data...');
    const response = await fetch('http://localhost:5000/api/test/cleanup-all', {
      method: 'DELETE'
    });
    
    if (response.ok) {
      const result = await response.json();
      console.log(`✅ Cleaned up ${result.count} test user directories`);
    } else {
      console.warn('⚠️  Test user cleanup failed:', response.statusText);
    }
  } catch (error) {
    console.warn('⚠️  Could not perform test user cleanup:', error.message);
    console.log('   (This is OK if the backend is not running yet)');
  }
  
  // Step 2: Reset shared test data to clean state
  console.log('🧹 Resetting shared test data to clean state...');
  
  try {
    // Change to project root and run the test data creation script
    const { stdout, stderr } = await execAsync('cd /home/tomb/Projects/coffeejournal && uv run python3 create_test_data.py');
    
    if (stderr) {
      console.warn('Test data reset warnings:', stderr);
    }
    
    console.log('✅ Test data reset complete');
    console.log('✅ Global test setup complete - ready for E2E tests');
    return Promise.resolve();
  } catch (error) {
    console.error('❌ Failed to reset test data:', error);
    throw error;
  }
}

module.exports = globalSetup;