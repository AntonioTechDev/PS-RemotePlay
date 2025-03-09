import asyncio
from remote_play.session_manager import EnhancedSessionManager
import sys
import os
import signal
import logging
from remote_play.network_monitor import check_connection

# Add parent folder path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from account_management.utils import get_user_profile, get_registered_consoles

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("remote_play_session.log")
    ]
)
logger = logging.getLogger("Session")

async def main():
    """Select account and start the Remote Play session with optimized implementation."""
    try:
        logger.info("🔍 [DEBUG] Starting account and console selection process...")
        user_profile = get_user_profile()
        user_hosts = get_registered_consoles(user_profile)

        logger.info("\n🖥️ Registered Consoles:")
        console_list = list(user_hosts.keys())
        for i, mac in enumerate(console_list):
            nickname = user_hosts[mac]["data"]["Nickname"]
            print(f"{i + 1}. {nickname} (MAC: {mac})")

        console_choice = input("\nSelect a console to use (enter the number): ")

        try:
            console_choice = int(console_choice) - 1
            if console_choice < 0 or console_choice >= len(console_list):
                raise ValueError("Invalid selection.")
        except ValueError:
            logger.error("❌ Invalid input. Please try again.")
            return

        selected_mac = console_list[console_choice]
        ip_address = user_hosts[selected_mac]["data"].get("IP")

        logger.info(f"\n📡 Selected console IP: {ip_address}")
        
        # Preliminary connection check
        logger.info("\n🔍 Preliminary connection check...")
        connection_status = await check_connection(ip_address)
        
        if connection_status["ping_success"] and connection_status["port_open"]:
            logger.info(f"✅ Connection verified: Ping {connection_status['ping_time']:.1f}ms")
        else:
            issues = []
            if not connection_status["ping_success"]:
                issues.append("ping failed")
            if not connection_status["port_open"]:
                issues.append("port closed")
                
            logger.warning(f"⚠️ Connection issues detected: {', '.join(issues)}")
            confirm = input("Do you want to try connecting anyway? (y/n): ")
            
            if confirm.lower() != 'y':
                logger.info("Operation cancelled by user.")
                return

        # Starting optimized Remote Play session...
        logger.info("🚀 [DEBUG] Starting optimized Remote Play session...")
        
        # Use the advanced session manager
        session_manager = EnhancedSessionManager()
        await session_manager.connect_and_run_session(user_profile, selected_mac, ip_address)
        
        logger.info("✅ [DEBUG] Remote Play session ended successfully.")

    except KeyboardInterrupt:
        logger.info("\n🛑 [DEBUG] Manual interruption detected. Closing all sessions...")

    finally:
        logger.info("🔄 [DEBUG] Initiating script termination phase...")

        # Cancel all active tasks
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        logger.info(f"🔎 [DEBUG] Found {len(tasks)} running tasks.")

        for task in tasks:
            logger.info(f"⚠️ [DEBUG] Cancelling task: {task}")
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.info(f"✅ [DEBUG] Task {task} cancelled successfully.")

        # Stop and close the asyncio loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            logger.info("🛑 [DEBUG] Stopping asyncio loop...")
            loop.stop()

        logger.info("✅ Script terminated successfully.")
        os._exit(0)

# Register a handler to cleanly catch SIGINT (CTRL+C)
def shutdown_handler(signal_received, frame):
    logger.info("\n🛑 [DEBUG] Manual interruption detected, exiting immediately...")
    os._exit(0)

if __name__ == "__main__":
    # Register signal handler for CTRL+C
    signal.signal(signal.SIGINT, shutdown_handler)

    try:
        logger.info("🟢 [DEBUG] Starting asyncio.run(main())...")
        asyncio.run(main())
        logger.info("🔴 [DEBUG] asyncio.run(main()) has ended.")
    except KeyboardInterrupt:
        logger.info("\n🛑 [DEBUG] Script interrupted with CTRL+C.")
        sys.exit(0)