#!/usr/bin/env python3
"""
Real-time email monitoring example using AnyRFC IMAP client.

This example demonstrates how to:
1. Monitor an INBOX for new incoming emails
2. Display real-time alerts when new messages arrive
3. Extract basic email information (sender, subject, timestamp)
4. Handle IMAP connection management for long-running monitoring

Setup:
1. Create a .env file with:
   IMAP_HOSTNAME=imap.gmail.com (or your IMAP server)
   IMAP_PORT=993
   IMAP_USERNAME=your.email@example.com
   IMAP_PASSWORD=your_app_specific_password
2. Run: uv sync --group examples
3. Run: uv run python examples/email_monitoring.py [duration_minutes]
"""
import anyio
import os
import sys
from datetime import datetime, timedelta

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Using os.environ directly.")

from anyrfc.email.imap import IMAPClient


async def monitor_emails(duration_minutes: int = 5):
    """Monitor for new emails for the specified duration."""
    
    # Get credentials from environment
    hostname = os.getenv("IMAP_HOSTNAME", "imap.gmail.com")
    port = int(os.getenv("IMAP_PORT", "993"))
    username = os.getenv("IMAP_USERNAME")
    password = os.getenv("IMAP_PASSWORD")
    
    if not username or not password:
        print("Error: IMAP_USERNAME and IMAP_PASSWORD must be set in .env file")
        print("Optional: IMAP_HOSTNAME (default: imap.gmail.com), IMAP_PORT (default: 993)")
        return False
    
    print(f"🔍 Starting email monitoring...")
    print(f"📧 Server: {hostname}:{port}")
    print(f"👤 User: {username}")
    print(f"⏰ Duration: {duration_minutes} minutes")
    print()
    
    try:
        # Get baseline count
        print("📊 Getting baseline message count...")
        baseline_client = IMAPClient(hostname, port, use_tls=True)
        await baseline_client.connect()
        await baseline_client.authenticate({"username": username, "password": password})
        baseline_info = await baseline_client.select_mailbox("INBOX")
        baseline_count = baseline_info.get("exists", 0)
        await baseline_client.disconnect()
        
        print(f"📬 Baseline: {baseline_count} messages in INBOX")
        print(f"🎧 Starting real-time monitoring...")
        print(f"⏹️  Press Ctrl+C to stop early")
        print()
        
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        last_count = baseline_count
        
        check_interval = 10  # Check every 10 seconds
        
        while datetime.now() < end_time:
            try:
                # Create fresh connection for each check (IMAP-server friendly)
                client = IMAPClient(hostname, port, use_tls=True)
                await client.connect()
                await client.authenticate({"username": username, "password": password})
                
                current_info = await client.select_mailbox("INBOX")
                current_count = current_info.get("exists", 0)
                
                if current_count > last_count:
                    new_emails = current_count - last_count
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    
                    print(f"\n🚨 ALERT [{timestamp}]: {new_emails} new email(s) detected!")
                    print(f"📊 Count: {last_count} → {current_count}")
                    
                    # Try to get basic info about the new emails
                    try:
                        for msg_num in range(current_count - new_emails + 1, current_count + 1):
                            messages = await client.fetch_messages(
                                str(msg_num), 
                                "ENVELOPE"
                            )
                            
                            if messages:
                                # Simple envelope parsing (this could be enhanced)
                                raw_data = str(messages[0].get('fetch_data', ''))
                                print(f"📧 Message #{msg_num}: {raw_data[:100]}...")
                    
                    except Exception as e:
                        print(f"⚠️ Could not get new message details: {e}")
                    
                    last_count = current_count
                    print()
                    
                elif current_count < last_count:
                    # Messages were deleted
                    deleted_count = last_count - current_count
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"🗑️ [{timestamp}]: {deleted_count} message(s) deleted")
                    last_count = current_count
                
                else:
                    # Show we're still monitoring
                    elapsed = datetime.now() - start_time
                    remaining = end_time - datetime.now()
                    print(f"⏱️ [{elapsed.seconds//60:02d}:{elapsed.seconds%60:02d}] Monitoring... ({remaining.seconds//60:02d}:{remaining.seconds%60:02d} remaining)", end='\r')
                
                await client.disconnect()
                await anyio.sleep(check_interval)
                
            except Exception as e:
                print(f"\n❌ Error during monitoring: {e}")
                await anyio.sleep(30)  # Wait longer on error
        
        print(f"\n\n⏰ {duration_minutes}-minute monitoring completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main function."""
    
    # Get duration from command line or use default
    duration = 5  # Default 5 minutes
    if len(sys.argv) > 1:
        try:
            duration = int(sys.argv[1])
        except ValueError:
            print("Invalid duration. Using default of 5 minutes.")
    
    print("=" * 80)
    print("🎧 AnyRFC Real-Time Email Monitoring")
    print("=" * 80)
    print()
    print("This example monitors your INBOX for new incoming emails")
    print("and provides real-time alerts when messages arrive.")
    print()
    print("Features:")
    print("• Real-time monitoring using IMAP polling")
    print("• Configurable duration and check intervals")
    print("• Basic email information extraction")
    print("• Graceful connection management")
    print()
    
    success = await monitor_emails(duration)
    
    print()
    print("=" * 80)
    if success:
        print("✅ Email monitoring completed successfully!")
        print("💡 You can extend this example to:")
        print("   - Parse email content in detail")
        print("   - Filter by sender/subject patterns")
        print("   - Trigger automated actions")
        print("   - Send notifications to external systems")
    else:
        print("❌ Email monitoring failed")
        print("💡 Check your .env file and IMAP credentials")
    print("=" * 80)


if __name__ == "__main__":
    try:
        anyio.run(main)
    except KeyboardInterrupt:
        print("\n\n🛑 Email monitoring stopped by user")
        print("✅ Monitoring session completed!")