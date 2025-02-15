import asyncio
from remote_play.session_manager import connect_and_run_session
import sys
import os

# Aggiungi il path della cartella superiore
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from account_management.utils import get_user_profile,  get_registered_consoles

async def main():
    """ Selezione dell'account e avvio della sessione Remote Play. """
    user_profile = get_user_profile()

    # Recupero delle console registrate
    user_hosts = get_registered_consoles(user_profile)

    print("\n🖥️ Console registrate:")
    console_list = list(user_hosts.keys())
    for i, mac in enumerate(console_list):
        nickname = user_hosts[mac]["data"]["Nickname"]
        print(f"{i + 1}. {nickname} (MAC: {mac})")

    # Scelta della console
    console_choice = input("\nSeleziona la console da utilizzare (inserisci il numero): ")

    try:
        console_choice = int(console_choice) - 1
        if console_choice < 0 or console_choice >= len(console_list):
            raise ValueError("Scelta non valida.")
    except ValueError:
        print("❌ Input non valido. Riprova.")
        return

    selected_mac = console_list[console_choice]
    ip_address = user_hosts[selected_mac]["data"].get("IP")

    print(f"\n📡 IP della console selezionato: {ip_address}")

    # Avvio della sessione Remote Play
    await connect_and_run_session(user_profile, selected_mac, ip_address)

if __name__ == "__main__":
    asyncio.run(main())
