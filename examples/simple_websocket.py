"""Simple WebSocket example with AnyRFC."""
import anyio
from anyrfc import WebSocketClient

async def main():
    """Simple WebSocket demonstration."""
    client = WebSocketClient("wss://echo.websocket.org/")
    
    try:
        print("Connecting...")
        await client.connect()
        print(f"✓ Connected! State: {client.websocket_state.name}")
        
        # Send message
        await client.send_text("Hello from AnyRFC!")
        print("✓ Message sent")
        
        # Receive response
        async for message in client.receive():
            print(f"✓ Received: {message}")
            break
            
    finally:
        await client.disconnect()
        print("✓ Disconnected")

if __name__ == "__main__":
    anyio.run(main)