#!/usr/bin/env python3
"""
SKAJLA - Quick Load Test
Fast performance and capacity testing
"""

import requests
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

class QuickLoadTest:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
    
    def test_db_queries(self, duration=5):
        """Test database query throughput"""
        print("\n" + "="*50)
        print("🔥 DATABASE QUERY TEST")
        print("="*50)
        
        queries = 0
        errors = 0
        latencies = []
        start = time.time()
        
        def query():
            nonlocal queries, errors
            try:
                t = time.time()
                r = requests.get(f"{self.base_url}/api/health/db-check", timeout=5)
                latencies.append((time.time() - t) * 1000)
                queries += 1 if r.status_code == 200 else 0
                errors += 0 if r.status_code == 200 else 1
            except:
                errors += 1
        
        with ThreadPoolExecutor(max_workers=20) as ex:
            end = start + duration
            while time.time() < end:
                ex.submit(query)
                time.sleep(0.02)
        
        elapsed = time.time() - start
        qps = queries / elapsed
        
        print(f"✅ Queries: {queries:,}")
        print(f"⚡ QPS: {qps:.1f} queries/second")
        print(f"⏱️  Avg: {statistics.mean(latencies) if latencies else 0:.1f}ms")
        print(f"📊 P95: {statistics.quantiles(latencies, n=20)[18] if len(latencies)>20 else 0:.1f}ms")
        print(f"❌ Errors: {errors}")
        
        return {'qps': qps, 'queries': queries, 'avg_ms': statistics.mean(latencies) if latencies else 0}
    
    def test_concurrent_users(self, steps=[10, 20, 40, 60, 80, 100]):
        """Test concurrent user capacity"""
        print("\n" + "="*50)
        print("👥 CONCURRENT USERS TEST")
        print("="*50)
        
        max_successful = 0
        
        for users in steps:
            success = 0
            fail = 0
            times = []
            
            def user():
                nonlocal success, fail
                try:
                    t = time.time()
                    r = requests.get(f"{self.base_url}/", timeout=10)
                    times.append((time.time() - t) * 1000)
                    success += 1 if r.status_code == 200 else 0
                    fail += 0 if r.status_code == 200 else 1
                except:
                    fail += 1
            
            start = time.time()
            with ThreadPoolExecutor(max_workers=users) as ex:
                list(ex.map(lambda _: user(), range(users)))
            elapsed = time.time() - start
            
            success_rate = (success / users * 100)
            avg_ms = statistics.mean(times) if times else 0
            
            print(f"\n{users} users: {success}/{users} OK ({success_rate:.0f}%), {avg_ms:.0f}ms avg")
            
            if fail == 0:
                max_successful = users
            
            if fail > users * 0.2:
                print(f"⚠️  High failure at {users} users")
                break
        
        print(f"\n✅ Max Concurrent (0% fail): {max_successful}")
        return max_successful
    
    def test_api_performance(self):
        """Test API endpoint throughput"""
        print("\n" + "="*50)
        print("🌐 API PERFORMANCE TEST")
        print("="*50)
        
        endpoints = [
            ('/api/health/status', 'Health'),
            ('/api/health/db-check', 'DB Check')
        ]
        
        for path, name in endpoints:
            success = 0
            times = []
            
            def req():
                nonlocal success
                try:
                    t = time.time()
                    r = requests.get(f"{self.base_url}{path}", timeout=5)
                    times.append((time.time() - t) * 1000)
                    success += 1 if r.status_code == 200 else 0
                except:
                    pass
            
            start = time.time()
            with ThreadPoolExecutor(max_workers=10) as ex:
                list(ex.map(lambda _: req(), range(50)))
            elapsed = time.time() - start
            
            rps = 50 / elapsed
            avg = statistics.mean(times) if times else 0
            
            print(f"{name}: {rps:.1f} req/s, {avg:.1f}ms avg ({success}/50 OK)")
    
    def run_all(self):
        """Run all tests"""
        print("""
╔═══════════════════════════════════════╗
║   SKAJLA QUICK LOAD TEST              ║
╚═══════════════════════════════════════╝
        """)
        
        db_result = self.test_db_queries(duration=5)
        max_users = self.test_concurrent_users()
        self.test_api_performance()
        
        print("\n" + "="*50)
        print("📊 SUMMARY")
        print("="*50)
        print(f"Database: {db_result['qps']:.1f} QPS, {db_result['avg_ms']:.1f}ms avg")
        print(f"Max Concurrent Users: {max_users} (0% failure)")
        
        if db_result['qps'] > 100:
            print("\n✅ Excellent database performance!")
        elif db_result['qps'] > 50:
            print("\n✅ Good database performance")
        else:
            print("\n⚠️  Consider database optimization")
        
        if max_users >= 80:
            print("✅ Excellent concurrent capacity!")
        elif max_users >= 40:
            print("✅ Good concurrent capacity")
        else:
            print("⚠️  Consider scaling resources")
        
        print("\n" + "="*50)
        print(f"⏰ Test completed: {datetime.now().strftime('%H:%M:%S')}")
        print("="*50)

if __name__ == "__main__":
    tester = QuickLoadTest()
    tester.run_all()
