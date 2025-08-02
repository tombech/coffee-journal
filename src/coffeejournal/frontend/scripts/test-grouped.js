#!/usr/bin/env node

/**
 * Test runner script for grouped E2E tests.
 * Runs each test group and reports on failures to help identify optimal worker counts.
 */

const { spawn } = require('child_process');

// Use dynamic import for chalk (ESM module)
let chalk;
(async () => {
  chalk = (await import('chalk')).default;
})().catch(() => {
  // Fallback to no colors if chalk fails
  chalk = {
    blue: (str) => str,
    bold: { blue: (str) => str, cyan: (str) => str, yellow: (str) => str },
    gray: (str) => str,
    green: (str) => str,
    red: (str) => str,
    yellow: (str) => str,
    cyan: (str) => str,
    white: (str) => str
  };
});

// Test groups with their expected worker counts
const testGroups = [
  { name: 'lookup-management', workers: 2, description: 'Lookup/Manager pages (prone to race conditions)' },
  { name: 'core-functionality', workers: 6, description: 'Core app functionality (stable)' },
  { name: 'ui-ux', workers: 6, description: 'UI/UX tests (stable)' },
  { name: 'forms-inputs', workers: 4, description: 'Form and input tests (moderate stability)' },
  { name: 'debug-utilities', workers: 1, description: 'Debug and utility tests (sequential)' }
];

const results = {};
let hasFailures = false;

async function runTestGroup(group) {
  console.log(`\n${chalk.blue('━'.repeat(80))}`);
  console.log(chalk.bold.blue(`Running ${group.name} tests`));
  console.log(chalk.gray(`Description: ${group.description}`));
  console.log(chalk.gray(`Workers: ${group.workers}`));
  console.log(chalk.blue('━'.repeat(80)) + '\n');

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
        console.log(chalk.green(`\n✅ ${group.name} passed (${duration}s)`));
        results[group.name] = { success: true, duration, workers: group.workers };
      } else {
        console.log(chalk.red(`\n❌ ${group.name} failed (${duration}s)`));
        results[group.name] = { success: false, duration, workers: group.workers };
        hasFailures = true;
      }
      
      resolve();
    });
  });
}

async function testWorkerConfiguration(group, workerCounts) {
  console.log(`\n${chalk.yellow('🔬 Testing different worker configurations for ' + group.name)}`);
  
  for (const workers of workerCounts) {
    console.log(chalk.gray(`\nTesting with ${workers} workers...`));
    
    // Override worker count
    process.env.PLAYWRIGHT_WORKERS = workers;
    
    const result = await runTestGroup(group);
    
    if (results[group.name].success) {
      console.log(chalk.green(`✅ ${workers} workers: SUCCESS`));
      return workers;
    } else {
      console.log(chalk.red(`❌ ${workers} workers: FAILED`));
    }
  }
  
  return 1; // Default to sequential if all fail
}

async function runAllGroups() {
  console.log(chalk.bold.cyan('\n🚀 Running E2E Tests with Grouped Configuration\n'));
  
  const runSequentially = process.argv.includes('--sequential');
  const testSpecificGroup = process.argv.find(arg => arg.startsWith('--group='));
  const findOptimal = process.argv.includes('--find-optimal');
  
  if (testSpecificGroup) {
    // Run specific group only
    const groupName = testSpecificGroup.split('=')[1];
    const group = testGroups.find(g => g.name === groupName);
    
    if (group) {
      await runTestGroup(group);
    } else {
      console.error(chalk.red(`Unknown group: ${groupName}`));
      process.exit(1);
    }
  } else if (findOptimal) {
    // Find optimal worker count for each group
    console.log(chalk.bold.yellow('Finding optimal worker counts for each test group...\n'));
    
    const optimalConfigs = {};
    
    for (const group of testGroups) {
      const optimal = await testWorkerConfiguration(group, [6, 4, 2, 1]);
      optimalConfigs[group.name] = optimal;
    }
    
    console.log(chalk.bold.cyan('\n📊 Optimal Worker Configuration:'));
    console.log(chalk.cyan('━'.repeat(50)));
    
    for (const [groupName, workers] of Object.entries(optimalConfigs)) {
      console.log(chalk.white(`${groupName.padEnd(20)} : ${workers} workers`));
    }
  } else {
    // Run all groups
    if (runSequentially) {
      // Run groups one at a time
      for (const group of testGroups) {
        await runTestGroup(group);
      }
    } else {
      // Run all groups in parallel (default)
      await Promise.all(testGroups.map(runTestGroup));
    }
  }
  
  // Summary
  console.log(`\n${chalk.bold.cyan('📊 Test Summary')}`);
  console.log(chalk.cyan('━'.repeat(80)));
  
  let totalDuration = 0;
  
  for (const [groupName, result] of Object.entries(results)) {
    const status = result.success ? chalk.green('✅ PASS') : chalk.red('❌ FAIL');
    const duration = parseFloat(result.duration);
    totalDuration += duration;
    
    console.log(
      `${status} ${groupName.padEnd(20)} (${result.duration}s with ${result.workers} workers)`
    );
  }
  
  console.log(chalk.cyan('━'.repeat(80)));
  console.log(chalk.bold(`Total Duration: ${totalDuration.toFixed(1)}s`));
  
  if (hasFailures) {
    console.log(chalk.red('\n❌ Some tests failed!'));
    
    if (!findOptimal) {
      console.log(chalk.yellow('\n💡 Tip: Run with --find-optimal to find the best worker count for each group'));
    }
    
    process.exit(1);
  } else {
    console.log(chalk.green('\n✅ All tests passed!'));
  }
}

// Check if chalk is installed
try {
  require.resolve('chalk');
} catch (e) {
  console.log('Installing chalk for colored output...');
  require('child_process').execSync('npm install --no-save chalk', { stdio: 'inherit' });
}

// Run the tests
runAllGroups().catch(console.error);