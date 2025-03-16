import asyncio
import sys
import os
import signal

# Add the parent directory of 'remote_play' to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from remote_play.session_manager import connect_and_run_session

# Add the path of the parent folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from account_management.utils import get_user_profile, get_registered_consoles

async def main():
    """ Account selection and Remote Play session startup. """
    try:
        print("🔍 [DEBUG] Starting the account and console selection process...")
        user_profile = get_user_profile()
        user_hosts = get_registered_consoles(user_profile)

        print("\n🖥️ Registered consoles:")
        console_list = list(user_hosts.keys())
        for i, mac in enumerate(console_list):
            nickname = user_hosts[mac]["data"]["Nickname"]
            print(f"{i + 1}. {nickname} (MAC: {mac})")

        console_choice = input("\nSelect the console to use (enter the number): ")

        try:
            console_choice = int(console_choice) - 1
            if console_choice < 0 or console_choice >= len(console_list):
                raise ValueError("Invalid choice.")
        except ValueError:
            print("❌ Invalid input. Please try again.")
            return

        selected_mac = console_list[console_choice]
        ip_address = user_hosts[selected_mac]["data"].get("IP")

        print(f"\n📡 Selected console IP: {ip_address}")

        # Start the Remote Play session
        print("🚀 [DEBUG] Starting the Remote Play session...")
        await connect_and_run_session(user_profile, selected_mac, ip_address)
        print("✅ [DEBUG] Remote Play session ended successfully.")

    except KeyboardInterrupt:
        print("\n🛑 [DEBUG] Manual interruption detected. Closing all sessions...")

    finally:
        print("🔄 [DEBUG] Starting the script termination phase...")

        # ✅ Cancel all active tasks
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        print(f"🔎 [DEBUG] Tasks found running: {len(tasks)}")

        for task in tasks:
            print(f"⚠️ [DEBUG] Cancelling task: {task}")
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                print(f"✅ [DEBUG] Task {task} cancelled successfully.")

        # ✅ Stop and close the asyncio loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            print("🛑 [DEBUG] Stopping the asyncio loop...")
            loop.stop()

        print("✅ Script terminated successfully.")
        os._exit(0)

# ✅ Register a handler to capture SIGINT (CTRL+C) cleanly
def shutdown_handler(signal_received, frame):
    print("\n🛑 [DEBUG] Manual interruption detected, immediate shutdown...")
    os._exit(0)

if __name__ == "__main__":
    # Register the signal handler to terminate the script with CTRL+C
    signal.signal(signal.SIGINT, shutdown_handler)

    try:
        print("🟢 [DEBUG] Starting asyncio.run(main())...")
        asyncio.run(main())
        print("🔴 [DEBUG] asyncio.run(main()) has ended.")
    except KeyboardInterrupt:
        print("\n🛑 [DEBUG] Script interrupted with CTRL+C.")
        sys.exit(0)
