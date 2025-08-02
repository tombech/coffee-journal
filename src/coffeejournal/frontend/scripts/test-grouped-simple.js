#!/usr/bin/env node

/**
 * Simple test runner for grouped E2E tests.
 * Runs each test group and reports on failures.
 */

const { spawn } = require('child_process');

// Test groups with their expected worker counts
const testGroups = [
  { name: 'basic-managers', workers: 2, description: 'Basic manager CRUD operations' },
  { name: 'roaster-views', workers: 1, description: 'Roaster view functionality' },
  { name: 'brew-method-views', workers: 1, description: 'Brew method view functionality' },
  { name: 'recipe-views', workers: 1, description: 'Recipe view functionality' },
  { name: 'bean-type-views', workers: 1, description: 'Bean type view functionality' },
  { name: 'equipment-views', workers: 2, description: 'Equipment view functionality' },
  { name: 'country-views', workers: 1, description: 'Country view functionality' },
  { name: 'country-management', workers: 1, description: 'Country/region management (most sensitive)' },
  { name: 'roaster-management', workers: 1, description: 'Roaster management operations' },
  { name: 'product-management', workers: 4, description: 'Product management tests' },
  { name: 'batch-management', workers: 4, description: 'Batch management tests' },
  { name: 'brew-session-management', workers: 4, description: 'Brew session management tests' },
  { name: 'session-duplication', workers: 2, description: 'Session duplication tests' },
  { name: 'ui-ux', workers: 6, description: 'UI/UX tests (stable)' },
  { name: 'forms-inputs', workers: 4, description: 'Form and input tests (moderate stability)' },
  { name: 'debug-utilities', workers: 1, description: 'Debug and utility tests (sequential)' }
];

const results = {};
let hasFailures = false;

async function runTestGroup(group) {
  console.log(`\n${'='.repeat(80)}`);
  console.log(`Running ${group.name} tests`);
  console.log(`Description: ${group.description}`);
  console.log(`Workers: ${group.workers}`);
  console.log(`${'='.repeat(80)}\n`);

  return new Promise((resolve) => {
    const startTime = Date.now();
    
    const args = [
      'playwright', 'test',
      '--config=playwright.config.grouped.js',
      '--project=' + group.name
    ];

    if (process.env.VERBOSE) {
      args.push('--reporter=list');
    }

    const proc = spawn('npx', args, {
      stdio: 'inherit',
      shell: true
    });

    proc.on('close', (code) => {
      const duration = ((Date.now() - startTime) / 1000).toFixed(1);
      
      if (code === 0) {
        console.log(`\n✅ ${group.name} passed (${duration}s)`);
        results[group.name] = { success: true, duration, workers: group.workers };
      } else {
        console.log(`\n❌ ${group.name} failed (${duration}s)`);
        results[group.name] = { success: false, duration, workers: group.workers };
        hasFailures = true;
      }
      
      resolve();
    });
  });
}

async function runAllGroups() {
  console.log('\n🚀 Running E2E Tests with Grouped Configuration\n');
  
  const testSpecificGroup = process.argv.find(arg => arg.startsWith('--group='));
  
  if (testSpecificGroup) {
    // Run specific group only
    const groupName = testSpecificGroup.split('=')[1];
    const group = testGroups.find(g => g.name === groupName);
    
    if (group) {
      await runTestGroup(group);
    } else {
      console.error(`Unknown group: ${groupName}`);
      process.exit(1);
    }
  } else {
    // Run all groups sequentially
    for (const group of testGroups) {
      await runTestGroup(group);
    }
  }
  
  // Summary
  console.log(`\n${'='.repeat(80)}`);
  console.log('📊 Test Summary');
  console.log('='.repeat(80));
  
  let totalDuration = 0;
  
  for (const [groupName, result] of Object.entries(results)) {
    const status = result.success ? '✅ PASS' : '❌ FAIL';
    const duration = parseFloat(result.duration);
    totalDuration += duration;
    
    console.log(
      `${status} ${groupName.padEnd(20)} (${result.duration}s with ${result.workers} workers)`
    );
  }
  
  console.log('='.repeat(80));
  console.log(`Total Duration: ${totalDuration.toFixed(1)}s`);
  
  if (hasFailures) {
    console.log('\n❌ Some tests failed!');
    process.exit(1);
  } else {
    console.log('\n✅ All tests passed!');
  }
}

// Run the tests
runAllGroups().catch(console.error);