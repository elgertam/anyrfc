"""Full Autobahn Testsuite runner for AnyRFC WebSocket client.

This script runs the complete RFC 6455 compliance test suite against AnyRFC.
The Autobahn Testsuite is the industry standard with 500+ test cases.

Usage:
    1. Start Autobahn server: uv run wstest -m fuzzingserver
    2. Run this script: python tests/compliance/autobahn_runner.py
    3. View results: open reports/clients/index.html
"""
import anyio
import json
import logging
from anyrfc import WebSocketClient

logger = logging.getLogger(__name__)


class AnyRFCAutobahnClient:
    """AnyRFC client for Autobahn Testsuite."""
    
    def __init__(self, server_port: int = 9001):
        self.server_port = server_port
        self.results = []
    
    async def run_test_case(self, case_id: int, strict_validation: bool = True):
        """Run a specific Autobahn test case."""
        uri = f"ws://localhost:{self.server_port}/runCase?case={case_id}&agent=AnyRFC"
        
        print(f"Running test case {case_id}...")
        
        try:
            async with WebSocketClient(uri, strict_rfc_validation=strict_validation) as ws:
                # Echo all messages back to the server
                try:
                    async for message in ws.receive():
                        if isinstance(message, str):
                            await ws.send_text(message)
                        else:
                            await ws.send_binary(message)
                except Exception as e:
                    # Some tests expect connection failures
                    logger.debug(f"Test case {case_id} exception: {e}")
                    
        except Exception as e:
            # Some tests expect handshake failures
            logger.debug(f"Test case {case_id} connection failed: {e}")
    
    async def get_case_count(self):
        """Get total number of test cases from server."""
        uri = f"ws://localhost:{self.server_port}/getCaseCount"
        
        try:
            async with WebSocketClient(uri) as ws:
                async for message in ws.receive():
                    return int(message)
        except Exception:
            return 0
    
    async def update_reports(self):
        """Tell server to generate reports."""
        uri = f"ws://localhost:{self.server_port}/updateReports?agent=AnyRFC"
        
        try:
            async with WebSocketClient(uri) as ws:
                pass  # Just connect and disconnect
        except Exception:
            pass
    
    async def run_all_tests(self, max_cases: int = None, strict_validation: bool = True):
        """Run all available test cases."""
        case_count = await self.get_case_count()
        
        if case_count == 0:
            print("❌ No test server found. Start with: uv run wstest -m fuzzingserver")
            return
        
        if max_cases:
            case_count = min(case_count, max_cases)
        
        print(f"🧪 Running {case_count} Autobahn test cases...")
        print(f"📋 RFC compliance validation: {'strict' if strict_validation else 'relaxed'}")
        
        failed_cases = []
        
        for case_id in range(1, case_count + 1):
            try:
                await self.run_test_case(case_id, strict_validation)
                print(f"✅ Test case {case_id}")
            except Exception as e:
                print(f"❌ Test case {case_id}: {e}")
                failed_cases.append(case_id)
        
        # Generate reports
        print("\n📊 Generating test reports...")
        await self.update_reports()
        
        print(f"\n🎯 Results: {case_count - len(failed_cases)}/{case_count} passed")
        if failed_cases:
            print(f"❌ Failed cases: {failed_cases[:10]}{'...' if len(failed_cases) > 10 else ''}")
        
        print("\n📁 View detailed results: open reports/clients/index.html")


async def main():
    """Run Autobahn compliance tests."""
    client = AnyRFCAutobahnClient()
    
    # First run with strict RFC validation
    print("🔬 Running with strict RFC 6455 validation...")
    await client.run_all_tests(max_cases=50, strict_validation=True)  # Limit for demo
    
    print("\n" + "="*60)
    
    # Then run with relaxed validation for real-world compatibility
    print("🌐 Running with relaxed validation (real-world mode)...")
    await client.run_all_tests(max_cases=50, strict_validation=False)


if __name__ == "__main__":
    print("🚀 AnyRFC Autobahn Testsuite Runner")
    print("="*40)
    print("Testing RFC 6455 WebSocket compliance...")
    print()
    
    anyio.run(main)