"""WebSocket real-time communication example."""
import anyio
from anyrfc.websocket import WebSocketClient, CloseCode

async def websocket_example():
    """Demonstrate WebSocket client capabilities."""
    print("WebSocket Real-time Communication Example")
    print("========================================")
    
    # Connect to WebSocket echo server
    client = WebSocketClient("wss://echo.websocket.org/")
    
    try:
        print("\n1. Connecting to WebSocket server...")
        await client.connect()
        print(f"✓ Connected! State: {client.state.name}")
        print(f"  WebSocket State: {client.websocket_state.name}")
        print(f"  Negotiated Protocol: {client.negotiated_protocol}")
        print(f"  Negotiated Extensions: {client.negotiated_extensions}")
        
        print("\n2. Sending text message...")
        test_message = "Hello from AnyIO RFC WebSocket Client!"
        await client.send_text(test_message)
        print(f"✓ Sent: {test_message}")
        
        print("\n3. Receiving messages...")
        message_count = 0
        with anyio.move_on_after(10.0):  # 10 second timeout
            async for message in client.receive():
                print(f"✓ Received: {message!r}")
                message_count += 1
                
                # Send a few more messages to test
                if message_count == 1:
                    await client.send_text("Second message")
                elif message_count == 2:
                    await client.send_binary(b"Binary data: \\x00\\x01\\x02\\x03")
                elif message_count >= 3:
                    break
        
        print(f"\n4. Received {message_count} messages total")
        
        print("\n5. Testing ping/pong...")
        await client.ping(b"ping-test")
        print("✓ Ping sent (pong handled automatically)")
        
        print("\n6. Closing connection gracefully...")
        await client.close(CloseCode.NORMAL_CLOSURE, "Example completed")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n7. Cleaning up...")
        await client.disconnect()
        print("✓ Disconnected")

async def websocket_stress_test():
    """Stress test WebSocket connection."""
    print("\nWebSocket Stress Test")
    print("====================")
    
    client = WebSocketClient("wss://echo.websocket.org/")
    
    try:
        await client.connect()
        print(f"✓ Connected for stress test")
        
        # Send multiple messages rapidly
        print("\nSending 10 messages rapidly...")
        for i in range(10):
            await client.send_text(f"Stress test message {i+1}")
        
        print("✓ All messages sent")
        
        # Receive responses
        received = 0
        with anyio.move_on_after(15.0):
            async for message in client.receive():
                received += 1
                print(f"  Received response {received}: {message[:50]}...")
                if received >= 5:  # Don't wait for all in this example
                    break
        
        print(f"✓ Received {received} responses")
        
    except Exception as e:
        print(f"✗ Stress test error: {e}")
    finally:
        await client.disconnect()

async def main():
    """Run WebSocket examples."""
    await websocket_example()
    await websocket_stress_test()

if __name__ == "__main__":
    anyio.run(main)