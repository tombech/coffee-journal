/**
 * Simplified Test Data Manager using User-ID Isolation
 * 
 * With multi-user support, each test gets its own completely isolated user space.
 * This eliminates the need for complex cleanup, tracking, and workarounds.
 */

class TestDataManager {
  constructor(testId, apiBaseUrl = 'http://localhost:5000/api', projectName = null) {
    // Create guaranteed unique test ID with process ID and high-resolution timestamp
    const processId = process.pid || Math.floor(Math.random() * 10000);
    const hrTime = process.hrtime ? process.hrtime.bigint() : BigInt(Date.now() * 1000000);
    const randomSuffix = Math.random().toString(36).substr(2, 12);
    
    // If project name is provided, use it to create group-specific user IDs
    const baseTestId = projectName ? `${projectName}_${testId}` : testId;
    this.testId = baseTestId || `test_${processId}_${hrTime}_${randomSuffix}`;
    this.apiBaseUrl = apiBaseUrl;
    this.projectName = projectName;
    
    // Sanitize testId for user_id - remove special characters that might cause validation issues
    const sanitizedTestId = this.testId.replace(/[^a-zA-Z0-9_-]/g, '_');
    this.userId = `test_user_${sanitizedTestId}`;
    
    // Add retry configuration for robustness
    this.maxRetries = 3;
    this.retryDelay = 200; // milliseconds
  }

  /**
   * Add user_id parameter to any URL
   */
  addUserIdToUrl(url) {
    const separator = url.includes('?') ? '&' : '?';
    return `${url}${separator}user_id=${this.userId}`;
  }

  /**
   * Initialize test - creates isolated user space
   */
  async initialize() {
    console.log(`🧪 Test ${this.testId} using isolated user: ${this.userId}`);
    
    // Clean up any existing data from previous test runs (in case of crashes)
    await this.cleanupExistingData();
    
    // With user isolation, initialization is just creating the user space
    // This happens automatically when we first make an API call
    return { userId: this.userId };
  }

  /**
   * Initialize user with full test data - convenient for tests that need rich data
   * This copies all the data from test_data/ directory to the user's isolated space
   */
  async initializeWithTestData() {
    console.log(`🧪 Initializing ${this.testId} with full test data for user: ${this.userId}`);
    
    // We need to call the backend to copy test data to user's directory
    // Since there's no API endpoint for this, we'll do it by making a request that triggers user creation
    // then manually copying via a direct backend call if available, or create representative data
    
    // First, ensure user space exists by making any API call
    try {
      await this.getItems('roasters');
    } catch (e) {
      // Expected if no data exists yet
    }
    
    // Create a representative set of data that matches the full test_data structure
    // This is more reliable than trying to call backend functions directly from frontend
    await this.createFullTestDataSet();
    
    return { userId: this.userId };
  }

  /**
   * Create a full test data set matching the structure in test_data/
   */
  async createFullTestDataSet() {
    console.log(`🏗️  Creating full test data set for ${this.testId}`);
    
    // Create roasters (matches test_data/roasters.json)
    const roasters = await Promise.all([
      this.createItem('roasters', { name: 'Blue Bottle Coffee' }),
      this.createItem('roasters', { name: 'Intelligentsia Coffee' }),
      this.createItem('roasters', { name: 'Stumptown Coffee Roasters' }),
      this.createItem('roasters', { name: 'Counter Culture Coffee' }),
      this.createItem('roasters', { name: 'La Colombe Coffee' })
    ]);
    
    // Create bean types
    const beanTypes = await Promise.all([
      this.createItem('bean_types', { name: 'Arabica' }),
      this.createItem('bean_types', { name: 'Robusta' }),
      this.createItem('bean_types', { name: 'Liberica' }),
      this.createItem('bean_types', { name: 'Excelsa' })
    ]);
    
    // Create countries and regions
    const ethiopia = await this.createItem('countries', { name: 'Ethiopia' });
    const colombia = await this.createItem('countries', { name: 'Colombia' });
    const guatemala = await this.createItem('countries', { name: 'Guatemala' });
    
    const regions = await Promise.all([
      this.createItem('regions', { name: 'Yirgacheffe', country_id: ethiopia.id }),
      this.createItem('regions', { name: 'Huila', country_id: colombia.id }),
      this.createItem('regions', { name: 'Antigua', country_id: guatemala.id })
    ]);
    
    // Create brew methods and recipes
    const brewMethods = await Promise.all([
      this.createItem('brew_methods', { name: 'V60' }),
      this.createItem('brew_methods', { name: 'Chemex' }),
      this.createItem('brew_methods', { name: 'French Press' }),
      this.createItem('brew_methods', { name: 'AeroPress' })
    ]);
    
    const recipes = await Promise.all([
      this.createItem('recipes', { name: 'Standard V60' }),
      this.createItem('recipes', { name: 'Chemex Classic' }),
      this.createItem('recipes', { name: 'French Press 4min' })
    ]);
    
    // Create equipment
    const grinders = await Promise.all([
      this.createItem('grinders', { name: 'Baratza Encore' }),
      this.createItem('grinders', { name: 'Commandante C40' }),
      this.createItem('grinders', { name: 'Fellow Ode' })
    ]);
    
    console.log(`✅ Created full test data set: ${roasters.length} roasters, ${beanTypes.length} bean types, ${regions.length} regions, ${brewMethods.length} brew methods`);
    
    return {
      roasters,
      beanTypes,
      countries: [ethiopia, colombia, guatemala],
      regions,
      brewMethods,
      recipes,
      grinders
    };
  }

  /**
   * Create a simple test item with retry logic for robustness
   */
  async createItem(endpoint, data) {
    const url = this.addUserIdToUrl(`${this.apiBaseUrl}/${endpoint}`);
    
    for (let attempt = 0; attempt <= this.maxRetries; attempt++) {
      try {
        const response = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });
        
        if (!response.ok) {
          const errorText = await response.text();
          
          // If it's a temporary error (like timeout or lock contention), retry
          if (attempt < this.maxRetries && (
            response.status >= 500 || 
            errorText.includes('timeout') || 
            errorText.includes('lock')
          )) {
            console.warn(`⚠️  Attempt ${attempt + 1} failed for ${endpoint}, retrying...`);
            await this._delay(this.retryDelay * (attempt + 1));
            continue;
          }
          
          throw new Error(`Failed to create ${endpoint}: ${response.statusText} - ${errorText}`);
        }
        
        return await response.json();
        
      } catch (error) {
        if (attempt < this.maxRetries && (
          error.name === 'TypeError' || // Network error
          error.message.includes('timeout') ||
          error.message.includes('ECONNRESET')
        )) {
          console.warn(`⚠️  Network error on attempt ${attempt + 1} for ${endpoint}, retrying...`);
          await this._delay(this.retryDelay * (attempt + 1));
          continue;
        }
        throw error;
      }
    }
  }

  /**
   * Utility function for delays
   */
  async _delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Backward compatibility alias
   */
  async createTestItem(endpoint, data) {
    return this.createItem(endpoint, data);
  }

  /**
   * Get items from an endpoint
   */
  async getItems(endpoint) {
    const url = this.addUserIdToUrl(`${this.apiBaseUrl}/${endpoint}`);
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`Failed to get ${endpoint}: ${response.statusText}`);
    }
    
    return await response.json();
  }

  /**
   * Create a complete test scenario with minimal dependencies
   */
  async createTestScenario() {
    console.log(`🏗️  Creating simple test scenario for ${this.testId}`);
    
    // Create minimal test data - much simpler with isolation
    const product = await this.createItem('products', {
      product_name: `Test Product ${this.testId}`,
      roaster: `Test Roaster ${this.testId}`,  // Will be auto-created
      bean_type: ['Arabica'],  // Will be auto-created
      country: 'Colombia',  // Will be auto-created
      region_id: []
    });
    
    const batch = await this.createBatch(product.id, {
      purchase_date: new Date().toISOString().split('T')[0],
      roast_date: new Date().toISOString().split('T')[0], 
      amount_grams: 250,
      price: 15.99
    });
    
    const brewSession = await this.createBrewSession(batch.id, {
      timestamp: new Date().toISOString(),
      brew_method: `Test Method ${this.testId}`,  // Will be auto-created
      recipe: `Test Recipe ${this.testId}`,  // Will be auto-created
      amount_coffee_grams: 20.0,
      amount_water_grams: 320.0,
      brew_temperature_c: 93.0,
      sweetness: 7,
      acidity: 8,
      bitterness: 3,
      body: 6,
      aroma: 8,
      flavor_profile_match: 7,
      notes: `Test notes for ${this.testId}`
    });
    
    // Get the actual country object with ID from the API
    const countries = await this.getItems('countries');
    const country = countries.find(c => c.name === 'Colombia') || { name: 'Colombia', id: null };
    
    // Create a region for the country for tests that need it
    let region = null;
    if (country.id) {
      try {
        region = await this.createItem('regions', {
          name: `Test Region ${this.testId}`,
          country_id: country.id,
          description: `Test region for ${this.testId}`
        });
      } catch (error) {
        console.warn(`Could not create region for test: ${error.message}`);
        region = { name: `Test Region ${this.testId}`, id: null };
      }
    }
    
    // Return enriched data for easy test access
    // The product object from API already contains enriched lookups
    return {
      product: {
        ...product,
        // Ensure backward compatibility with test expectations
        country: product.country || country,
        roaster: product.roaster || { name: `Test Roaster ${this.testId}` }
      },
      batch,
      brewSession,
      // Also return simple lookups for test assertions
      roaster: { name: `Test Roaster ${this.testId}` },
      beanType: { name: 'Arabica' },
      country: country,  // Now includes ID
      region: region,  // Region with ID for country tests
      brewMethod: { name: `Test Method ${this.testId}` },
      recipe: { name: `Test Recipe ${this.testId}` }
    };
  }

  /**
   * Create batch for a product using the nested endpoint
   */
  async createBatch(productId, data) {
    const url = this.addUserIdToUrl(`${this.apiBaseUrl}/products/${productId}/batches`);
    
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...data, product_id: productId })
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Failed to create batch: ${response.statusText} - ${errorText}`);
    }
    
    return await response.json();
  }

  /**
   * Create brew session for a batch using the nested endpoint
   */
  async createBrewSession(batchId, data) {
    const url = this.addUserIdToUrl(`${this.apiBaseUrl}/batches/${batchId}/brew_sessions`);
    
    const response = await fetch(url, {
      method: 'POST',  
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...data, product_batch_id: batchId })
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Failed to create brew session: ${response.statusText} - ${errorText}`);
    }
    
    return await response.json();
  }

  /**
   * Create an espresso test scenario with all necessary equipment
   */
  async createEspressoTestScenario() {
    console.log(`🏗️  Creating espresso test scenario for ${this.testId}`);
    
    // Create basic product and batch
    const product = await this.createItem('products', {
      product_name: `Test Espresso Product ${this.testId}`,
      roaster: `Test Roaster ${this.testId}`,
      bean_type: ['Arabica'],
      country: 'Colombia',
      region_id: []
    });
    
    const batch = await this.createBatch(product.id, {
      purchase_date: new Date().toISOString().split('T')[0],
      roast_date: new Date().toISOString().split('T')[0], 
      amount_grams: 250,
      price: 18.99
    });
    
    // Create espresso equipment
    const brewer = await this.createItem('brewers', {
      name: `Test Espresso Machine ${this.testId}`,
      type: 'Semi-Automatic',
      brand: 'Test Brand'
    });
    
    const portafilter = await this.createItem('portafilters', {
      name: `Test Portafilter ${this.testId}`,
      size: '58mm',
      size_mm: 58,
      material: 'Stainless Steel'
    });
    
    const basket = await this.createItem('baskets', {
      name: `Test Basket ${this.testId}`,
      holes: 25,  // Number of holes (integer)
      capacity_grams: 18,  // Capacity in grams (number)
      basket_type: 'Precision'
    });
    
    const tamper = await this.createItem('tampers', {
      name: `Test Tamper ${this.testId}`,
      size: '58mm',
      base_material: 'Aluminum',
      handle_material: 'Wood'
    });
    
    // Create shot with equipment
    const shot = await this.createShot({
      product_id: product.id,
      product_batch_id: batch.id,
      brewer_id: brewer.id,
      portafilter_id: portafilter.id,
      basket_id: basket.id,
      tamper_id: tamper.id,
      dose_grams: 18.0,
      yield_grams: 36.0,
      dose_yield_ratio: 2.0,
      extraction_time_seconds: 25,
      water_temperature_c: 93,
      grinder_setting: 'fine',
      extraction_status: 'perfect',
      sweetness: 8,
      acidity: 7,
      body: 8,
      aroma: 9,
      bitterness: 2,
      overall_score: 8,
      notes: `Test espresso shot ${this.testId}`
    });
    
    return {
      product,
      batch,
      brewer,
      portafilter,
      basket,
      tamper,
      shot
    };
  }

  /**
   * Create a shot
   */
  async createShot(shotData) {
    const url = this.addUserIdToUrl(`${this.apiBaseUrl}/shots`);
    
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        timestamp: new Date().toISOString(),
        ...shotData
      })
    });
    
    if (!response.ok) {
      const errorBody = await response.text();
      throw new Error(`Failed to create shot: ${response.status} ${response.statusText} - ${errorBody}`);
    }
    
    return await response.json();
  }

  /**
   * Create a shot session
   */
  async createShotSession(sessionData) {
    const url = this.addUserIdToUrl(`${this.apiBaseUrl}/shot_sessions`);
    
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        created_at: new Date().toISOString(),
        ...sessionData
      })
    });
    
    if (!response.ok) {
      const errorBody = await response.text();
      throw new Error(`Failed to create shot session: ${response.status} ${response.statusText} - ${errorBody}`);
    }
    
    return await response.json();
  }

  /**
   * Clean up existing data from previous runs (pre-test cleanup)
   */
  async cleanupExistingData() {
    try {
      // Try to delete any existing data for this user
      const response = await fetch(`${this.apiBaseUrl}/test/cleanup/${this.userId}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        console.log(`🧹 Pre-test cleanup: Removed existing data for ${this.userId}`);
      } else if (response.status === 404) {
        // User doesn't exist yet - that's fine
        console.log(`🆕 Pre-test cleanup: No existing data for ${this.userId}`);
      } else {
        // Log but don't fail - test can still proceed
        console.warn(`⚠️  Pre-test cleanup warning: ${response.status} - ${response.statusText}`);
      }
    } catch (error) {
      // Don't fail the test if cleanup fails - just log it
      console.warn(`⚠️  Pre-test cleanup error (non-fatal):`, error.message);
    }
  }

  /**
   * Clean up - properly delete test user data
   */
  async cleanup() {
    console.log(`🧹 Cleaning up test data for ${this.testId}...`);
    
    try {
      const response = await fetch(`${this.apiBaseUrl}/test/cleanup/${this.userId}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        console.log(`✅ Cleanup complete for ${this.testId} - user ${this.userId} data removed`);
      } else {
        const error = await response.text();
        console.error(`❌ Cleanup failed for ${this.userId}: ${error}`);
      }
    } catch (error) {
      console.error(`❌ Cleanup error for ${this.userId}:`, error);
    }
  }
}

module.exports = TestDataManager;