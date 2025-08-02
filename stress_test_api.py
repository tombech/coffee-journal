#!/usr/bin/env python3
"""
API Stress Test - Mimics E2E test patterns to identify backend bottlenecks.

This script reproduces the same API call patterns that cause E2E test failures:
1. Create items via POST
2. Immediately fetch them via GET (where 404s occur)
3. Test with increasing concurrency to find the breaking point

Usage:
    python stress_test_api.py --workers 6 --iterations 10
"""

import asyncio
import aiohttp
import argparse
import time
import json
import statistics
from typing import Dict, List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor
import threading
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TestResult:
    success: bool
    duration: float
    error: Optional[str] = None
    status_code: Optional[int] = None
    operation: str = ""
    item_id: Optional[int] = None


@dataclass
class StressTestStats:
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    avg_duration: float = 0.0
    max_duration: float = 0.0
    min_duration: float = float('inf')
    errors: Dict[str, int] = field(default_factory=dict)
    durations: List[float] = field(default_factory=list)
    
    def add_result(self, result: TestResult):
        self.total_operations += 1
        self.durations.append(result.duration)
        
        if result.success:
            self.successful_operations += 1
        else:
            self.failed_operations += 1
            error_key = f"{result.status_code}: {result.error}" if result.status_code else result.error
            self.errors[error_key] = self.errors.get(error_key, 0) + 1
        
        self.max_duration = max(self.max_duration, result.duration)
        self.min_duration = min(self.min_duration, result.duration)
        self.avg_duration = statistics.mean(self.durations)
    
    def success_rate(self) -> float:
        return (self.successful_operations / self.total_operations * 100) if self.total_operations > 0 else 0
    
    def print_summary(self, worker_count: int):
        print(f"\n{'='*60}")
        print(f"STRESS TEST RESULTS - {worker_count} Workers")
        print(f"{'='*60}")
        print(f"Total Operations:     {self.total_operations}")
        print(f"Successful:           {self.successful_operations}")
        print(f"Failed:               {self.failed_operations}")
        print(f"Success Rate:         {self.success_rate():.1f}%")
        print(f"Average Duration:     {self.avg_duration:.3f}s")
        print(f"Min Duration:         {self.min_duration:.3f}s")
        print(f"Max Duration:         {self.max_duration:.3f}s")
        
        if self.durations:
            print(f"95th Percentile:      {statistics.quantiles(self.durations, n=20)[18]:.3f}s")
            print(f"99th Percentile:      {statistics.quantiles(self.durations, n=100)[98]:.3f}s")
        
        if self.errors:
            print(f"\nErrors:")
            for error, count in sorted(self.errors.items(), key=lambda x: x[1], reverse=True):
                print(f"  {error}: {count}")


class APIStressTester:
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.stats = StressTestStats()
        self.stats_lock = threading.Lock()
        
        # Lookup types that match the failing E2E tests
        self.lookup_types = [
            "roasters", "brew_methods", "recipes", "bean_types", "countries",
            "grinders", "filters", "kettles", "scales", "decaf_methods"
        ]
    
    async def create_test_user_session(self, session: aiohttp.ClientSession, user_id: str):
        """Clean up any existing test data for this user."""
        try:
            url = f"{self.base_url}/api/test/cleanup/{user_id}"
            async with session.delete(url) as response:
                # Ignore 404s - user might not exist yet
                pass
        except Exception:
            pass  # Cleanup failures are non-critical
    
    async def create_item(self, session: aiohttp.ClientSession, lookup_type: str, 
                         user_id: str, unique_suffix: str) -> TestResult:
        """Create an item via POST and return the result."""
        start_time = time.time()
        
        try:
            url = f"{self.base_url}/api/{lookup_type}"
            data = {
                "name": f"Stress Test {lookup_type.title()} {unique_suffix}",
                "description": f"Test item for stress testing {lookup_type}"
            }
            
            params = {"user_id": user_id}
            
            async with session.post(url, json=data, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                duration = time.time() - start_time
                
                if response.status == 201:
                    result_data = await response.json()
                    return TestResult(
                        success=True,
                        duration=duration,
                        operation=f"CREATE {lookup_type}",
                        item_id=result_data.get('id')
                    )
                else:
                    error_text = await response.text()
                    return TestResult(
                        success=False,
                        duration=duration,
                        error=f"Create failed: {error_text}",
                        status_code=response.status,
                        operation=f"CREATE {lookup_type}"
                    )
                    
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                success=False,
                duration=duration,
                error=f"Create exception: {str(e)}",
                operation=f"CREATE {lookup_type}"
            )
    
    async def get_item(self, session: aiohttp.ClientSession, lookup_type: str, 
                      item_id: int, user_id: str, retry_count: int = 0) -> TestResult:
        """Fetch an item via GET immediately after creation (mimics E2E test pattern)."""
        start_time = time.time()
        
        try:
            url = f"{self.base_url}/api/{lookup_type}/{item_id}"
            params = {"user_id": user_id}
            
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                duration = time.time() - start_time
                
                if response.status == 200:
                    return TestResult(
                        success=True,
                        duration=duration,
                        operation=f"GET {lookup_type}/{item_id}",
                        item_id=item_id
                    )
                elif response.status == 404:
                    error_text = await response.text()
                    return TestResult(
                        success=False,
                        duration=duration,
                        error=f"404 Not Found: {error_text}",
                        status_code=404,
                        operation=f"GET {lookup_type}/{item_id}"
                    )
                else:
                    error_text = await response.text()
                    return TestResult(
                        success=False,
                        duration=duration,
                        error=f"Get failed: {error_text}",
                        status_code=response.status,
                        operation=f"GET {lookup_type}/{item_id}"
                    )
                    
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                success=False,
                duration=duration,
                error=f"Get exception: {str(e)}",
                operation=f"GET {lookup_type}/{item_id}"
            )
    
    async def test_create_then_get_cycle(self, session: aiohttp.ClientSession, 
                                       lookup_type: str, worker_id: int, iteration: int) -> List[TestResult]:
        """
        Mimics the exact E2E test pattern:
        1. Create an item
        2. Immediately try to GET it by ID
        This is where the 404 race condition occurs.
        """
        user_id = f"stress_test_worker_{worker_id}"
        unique_suffix = f"w{worker_id}_i{iteration}_{int(time.time() * 1000)}"
        
        results = []
        
        # Clean up user data first
        await self.create_test_user_session(session, user_id)
        
        # Step 1: Create the item
        create_result = await self.create_item(session, lookup_type, user_id, unique_suffix)
        results.append(create_result)
        
        # Step 2: Immediately try to GET it (this is where 404s happen)
        if create_result.success and create_result.item_id:
            # Add delays to mimic E2E test patterns: page navigation, DOM rendering, etc.
            await asyncio.sleep(0.5)  # 500ms - realistic browser navigation + DOM rendering time
            
            get_result = await self.get_item(session, lookup_type, create_result.item_id, user_id)
            results.append(get_result)
        
        return results
    
    async def worker_task(self, worker_id: int, iterations: int, session: aiohttp.ClientSession):
        """Single worker that performs multiple test iterations."""
        print(f"Worker {worker_id} starting {iterations} iterations...")
        
        for iteration in range(iterations):
            # Test different lookup types to spread the load
            lookup_type = self.lookup_types[iteration % len(self.lookup_types)]
            
            try:
                results = await self.test_create_then_get_cycle(session, lookup_type, worker_id, iteration)
                
                # Add results to stats thread-safely
                with self.stats_lock:
                    for result in results:
                        self.stats.add_result(result)
                        
            except Exception as e:
                print(f"Worker {worker_id}, iteration {iteration} failed: {e}")
                with self.stats_lock:
                    self.stats.add_result(TestResult(
                        success=False,
                        duration=0.0,
                        error=f"Worker exception: {str(e)}",
                        operation=f"WORKER {worker_id}"
                    ))
    
    async def run_stress_test(self, worker_count: int, iterations_per_worker: int):
        """Run the stress test with specified concurrency."""
        print(f"Starting stress test: {worker_count} workers × {iterations_per_worker} iterations each")
        print(f"Total operations: {worker_count * iterations_per_worker * 2} (create + get)")
        print(f"Target endpoint: {self.base_url}")
        
        # Reset stats
        self.stats = StressTestStats()
        
        # Create session with appropriate connection limits
        connector = aiohttp.TCPConnector(limit=worker_count * 2, limit_per_host=worker_count * 2)
        timeout = aiohttp.ClientTimeout(total=30)
        
        start_time = time.time()
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # Create all worker tasks
            tasks = [
                self.worker_task(worker_id, iterations_per_worker, session)
                for worker_id in range(worker_count)
            ]
            
            # Run all workers concurrently
            await asyncio.gather(*tasks)
        
        total_duration = time.time() - start_time
        
        print(f"\nTest completed in {total_duration:.2f} seconds")
        self.stats.print_summary(worker_count)
        
        return self.stats.success_rate()


def test_scaling_limits():
    """Test different worker counts to find the breaking point."""
    tester = APIStressTester()
    
    print("SCALING TEST - Finding the breaking point\n")
    
    # Test with increasing worker counts
    worker_counts = [1, 2, 4, 6, 8, 10, 12]
    iterations_per_worker = 5  # Keep iterations low for faster testing
    
    results = {}
    
    for workers in worker_counts:
        print(f"\n🧪 Testing {workers} workers...")
        success_rate = asyncio.run(tester.run_stress_test(workers, iterations_per_worker))
        results[workers] = success_rate
        
        # Stop if success rate drops below 95%
        if success_rate < 95.0:
            print(f"\n❌ Breaking point found at {workers} workers ({success_rate:.1f}% success rate)")
            break
        elif success_rate == 100.0:
            print(f"✅ {workers} workers: PERFECT ({success_rate:.1f}% success rate)")
        else:
            print(f"⚠️  {workers} workers: MARGINAL ({success_rate:.1f}% success rate)")
    
    print(f"\n{'='*60}")
    print("SCALING SUMMARY")
    print(f"{'='*60}")
    for workers, success_rate in results.items():
        status = "✅ PASS" if success_rate >= 95.0 else "❌ FAIL"
        print(f"{workers:2d} workers: {success_rate:5.1f}% {status}")


def main():
    parser = argparse.ArgumentParser(description='API Stress Test')
    parser.add_argument('--workers', type=int, default=6, help='Number of concurrent workers')
    parser.add_argument('--iterations', type=int, default=10, help='Iterations per worker')
    parser.add_argument('--scaling', action='store_true', help='Run scaling test to find limits')
    parser.add_argument('--url', default='http://localhost:5000', help='Base URL for API')
    
    args = parser.parse_args()
    
    if args.scaling:
        test_scaling_limits()
    else:
        tester = APIStressTester(args.url)
        asyncio.run(tester.run_stress_test(args.workers, args.iterations))


if __name__ == "__main__":
    main()