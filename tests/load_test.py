#!/usr/bin/env python3
"""
SKAILA - Load Testing Script
Tests maximum concurrent users and database query capacity
"""

import requests
import time
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import json

class SKAILALoadTester:
    """Comprehensive load testing for SKAILA platform"""
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.results = {
            'database_queries': [],
            'concurrent_users': [],
            'api_endpoints': [],
            'errors': []
        }
    
    def test_database_query_capacity(self, duration_seconds=10):
        """Test maximum database queries per second"""
        print("\n" + "="*60)
        print("🔥 DATABASE QUERY STRESS TEST")
        print("="*60)
        
        query_count = 0
        errors = 0
        start_time = time.time()
        latencies = []
        
        def execute_query():
            nonlocal query_count, errors
            try:
                query_start = time.time()
                response = requests.get(
                    f"{self.base_url}/api/health/db-check",
                    timeout=5
                )
                query_time = (time.time() - query_start) * 1000  # ms
                latencies.append(query_time)
                
                if response.status_code == 200:
                    query_count += 1
                else:
                    errors += 1
            except Exception as e:
                errors += 1
        
        print(f"⏱️  Running queries for {duration_seconds} seconds...")
        
        # Spawn threads to execute queries continuously
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = []
            end_time = start_time + duration_seconds
            
            while time.time() < end_time:
                futures.append(executor.submit(execute_query))
                time.sleep(0.01)  # Small delay between spawning
            
            # Wait for all to complete
            for future in as_completed(futures):
                future.result()
        
        total_time = time.time() - start_time
        qps = query_count / total_time
        
        result = {
            'total_queries': query_count,
            'duration_seconds': total_time,
            'queries_per_second': qps,
            'errors': errors,
            'avg_latency_ms': statistics.mean(latencies) if latencies else 0,
            'p95_latency_ms': statistics.quantiles(latencies, n=20)[18] if len(latencies) > 20 else 0,
            'p99_latency_ms': statistics.quantiles(latencies, n=100)[98] if len(latencies) > 100 else 0
        }
        
        self.results['database_queries'] = result
        
        print(f"\n✅ Results:")
        print(f"   Total Queries: {query_count:,}")
        print(f"   Duration: {total_time:.2f}s")
        print(f"   Queries/Second: {qps:.2f} QPS")
        print(f"   Errors: {errors}")
        print(f"   Avg Latency: {result['avg_latency_ms']:.2f}ms")
        print(f"   P95 Latency: {result['p95_latency_ms']:.2f}ms")
        print(f"   P99 Latency: {result['p99_latency_ms']:.2f}ms")
        
        return result
    
    def test_concurrent_users(self, max_users=200, ramp_up_step=20):
        """Test maximum concurrent user connections"""
        print("\n" + "="*60)
        print("👥 CONCURRENT USERS TEST")
        print("="*60)
        
        results = []
        
        for num_users in range(ramp_up_step, max_users + 1, ramp_up_step):
            print(f"\n🧪 Testing {num_users} concurrent users...")
            
            successful = 0
            failed = 0
            response_times = []
            
            def simulate_user():
                nonlocal successful, failed
                try:
                    start = time.time()
                    response = requests.get(
                        f"{self.base_url}/",
                        timeout=10
                    )
                    elapsed = (time.time() - start) * 1000
                    response_times.append(elapsed)
                    
                    if response.status_code == 200:
                        successful += 1
                    else:
                        failed += 1
                except Exception as e:
                    failed += 1
            
            # Execute concurrent requests
            start_time = time.time()
            with ThreadPoolExecutor(max_workers=num_users) as executor:
                futures = [executor.submit(simulate_user) for _ in range(num_users)]
                for future in as_completed(futures):
                    future.result()
            
            total_time = time.time() - start_time
            
            result = {
                'concurrent_users': num_users,
                'successful': successful,
                'failed': failed,
                'total_time_seconds': total_time,
                'avg_response_ms': statistics.mean(response_times) if response_times else 0,
                'throughput_rps': num_users / total_time
            }
            
            results.append(result)
            
            print(f"   ✅ Successful: {successful}/{num_users}")
            print(f"   ❌ Failed: {failed}/{num_users}")
            print(f"   ⏱️  Avg Response: {result['avg_response_ms']:.2f}ms")
            print(f"   🚀 Throughput: {result['throughput_rps']:.2f} req/s")
            
            # Stop if failure rate exceeds 10%
            if failed > num_users * 0.1:
                print(f"\n⚠️  High failure rate detected at {num_users} users!")
                break
            
            time.sleep(1)  # Cool down between tests
        
        self.results['concurrent_users'] = results
        return results
    
    def test_api_endpoints(self, requests_per_endpoint=100):
        """Test API endpoint performance under load"""
        print("\n" + "="*60)
        print("🌐 API ENDPOINTS STRESS TEST")
        print("="*60)
        
        endpoints = [
            ('GET', '/api/health/status', 'Health Check'),
            ('GET', '/api/health/db-check', 'Database Check'),
        ]
        
        results = []
        
        for method, path, name in endpoints:
            print(f"\n🔍 Testing: {name} ({method} {path})")
            
            successful = 0
            failed = 0
            latencies = []
            
            def test_endpoint():
                nonlocal successful, failed
                try:
                    start = time.time()
                    if method == 'GET':
                        response = requests.get(f"{self.base_url}{path}", timeout=10)
                    else:
                        response = requests.post(f"{self.base_url}{path}", timeout=10)
                    
                    elapsed = (time.time() - start) * 1000
                    latencies.append(elapsed)
                    
                    if response.status_code in [200, 201]:
                        successful += 1
                    else:
                        failed += 1
                except Exception as e:
                    failed += 1
            
            start_time = time.time()
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = [executor.submit(test_endpoint) for _ in range(requests_per_endpoint)]
                for future in as_completed(futures):
                    future.result()
            
            total_time = time.time() - start_time
            
            result = {
                'endpoint': f"{method} {path}",
                'name': name,
                'requests': requests_per_endpoint,
                'successful': successful,
                'failed': failed,
                'total_time_seconds': total_time,
                'requests_per_second': requests_per_endpoint / total_time,
                'avg_latency_ms': statistics.mean(latencies) if latencies else 0,
                'p95_latency_ms': statistics.quantiles(latencies, n=20)[18] if len(latencies) > 20 else 0
            }
            
            results.append(result)
            
            print(f"   ✅ Successful: {successful}/{requests_per_endpoint}")
            print(f"   ❌ Failed: {failed}/{requests_per_endpoint}")
            print(f"   ⏱️  Avg Latency: {result['avg_latency_ms']:.2f}ms")
            print(f"   🚀 Throughput: {result['requests_per_second']:.2f} req/s")
        
        self.results['api_endpoints'] = results
        return results
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*60)
        print("📊 LOAD TEST SUMMARY REPORT")
        print("="*60)
        print(f"🕐 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Database Performance
        if self.results['database_queries']:
            db = self.results['database_queries']
            print(f"\n📈 DATABASE PERFORMANCE:")
            print(f"   Max QPS: {db['queries_per_second']:.2f} queries/second")
            print(f"   Total Queries: {db['total_queries']:,}")
            print(f"   Avg Latency: {db['avg_latency_ms']:.2f}ms")
            print(f"   P95 Latency: {db['p95_latency_ms']:.2f}ms")
            print(f"   Error Rate: {(db['errors'] / db['total_queries'] * 100):.2f}%")
        
        # Concurrent Users
        if self.results['concurrent_users']:
            print(f"\n👥 CONCURRENT USERS:")
            for result in self.results['concurrent_users']:
                success_rate = (result['successful'] / result['concurrent_users'] * 100)
                print(f"   {result['concurrent_users']} users: {success_rate:.1f}% success, {result['avg_response_ms']:.0f}ms avg")
            
            max_users = max([r['concurrent_users'] for r in self.results['concurrent_users'] if r['failed'] == 0], default=0)
            print(f"\n   ✅ Max Concurrent Users (0% failure): {max_users}")
        
        # API Endpoints
        if self.results['api_endpoints']:
            print(f"\n🌐 API PERFORMANCE:")
            for result in self.results['api_endpoints']:
                print(f"   {result['name']}: {result['requests_per_second']:.2f} req/s, {result['avg_latency_ms']:.2f}ms avg")
        
        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        
        if self.results['database_queries']:
            qps = self.results['database_queries']['queries_per_second']
            if qps < 50:
                print("   ⚠️  Database QPS is low - consider connection pooling optimization")
            elif qps > 200:
                print("   ✅ Excellent database performance!")
            else:
                print("   ✅ Good database performance")
        
        if self.results['concurrent_users']:
            max_users = max([r['concurrent_users'] for r in self.results['concurrent_users'] if r['failed'] == 0], default=0)
            if max_users < 50:
                print("   ⚠️  Low concurrent user capacity - consider scaling resources")
            elif max_users >= 100:
                print("   ✅ Excellent concurrent user capacity!")
            else:
                print("   ✅ Good concurrent user capacity")
        
        print("\n" + "="*60)
        
        # Save results to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"tests/load_test_report_{timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"📄 Full report saved to: {report_file}")
        print("="*60)


def main():
    """Run comprehensive load tests"""
    print("""
    ╔═══════════════════════════════════════════════╗
    ║   SKAILA LOAD TESTING SUITE                   ║
    ║   Testing Maximum Capacity & Performance      ║
    ╚═══════════════════════════════════════════════╝
    """)
    
    tester = SKAILALoadTester()
    
    # Run all tests
    try:
        # Test 1: Database query capacity
        tester.test_database_query_capacity(duration_seconds=10)
        
        # Test 2: Concurrent users (ramp up to 200 users)
        tester.test_concurrent_users(max_users=200, ramp_up_step=20)
        
        # Test 3: API endpoints
        tester.test_api_endpoints(requests_per_endpoint=100)
        
        # Generate final report
        tester.generate_report()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        tester.generate_report()
    except Exception as e:
        print(f"\n\n❌ Error during testing: {e}")
        tester.generate_report()


if __name__ == "__main__":
    main()
