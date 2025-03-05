import asyncio
from remote_play.session_manager import connect_and_run_session
import sys
import os
import signal

# Aggiungi il path della cartella superiore
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from account_management.utils import get_user_profile,  get_registered_consoles

async def main():
    """ Selezione dell'account e avvio della sessione Remote Play con la nuova implementazione ottimizzata. """
    try:
        print("🔍 [DEBUG] Avvio del processo di selezione account e console...")
        user_profile = get_user_profile()
        user_hosts = get_registered_consoles(user_profile)

        print("\n🖥️ Console registrate:")
        console_list = list(user_hosts.keys())
        for i, mac in enumerate(console_list):
            nickname = user_hosts[mac]["data"]["Nickname"]
            print(f"{i + 1}. {nickname} (MAC: {mac})")

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

        # Avvio della sessione Remote Play con il nuovo gestore ottimizzato
        print("🚀 [DEBUG] Avvio della sessione Remote Play ottimizzata...")
        
        # Importa il nuovo gestore di sessione
        from remote_play.session_manager import connect_and_run_session
        
        await connect_and_run_session(user_profile, selected_mac, ip_address)
        print("✅ [DEBUG] Sessione Remote Play terminata correttamente.")

    except KeyboardInterrupt:
        print("\n🛑 [DEBUG] Interruzione manuale rilevata. Chiudo tutte le sessioni...")

    finally:
        print("🔄 [DEBUG] Avvio della fase di terminazione dello script...")

        # ✅ Cancella tutti i task ancora attivi
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        print(f"🔎 [DEBUG] Task trovati in esecuzione: {len(tasks)}")

        for task in tasks:
            print(f"⚠️ [DEBUG] Cancellazione task: {task}")
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                print(f"✅ [DEBUG] Task {task} cancellato correttamente.")

        # ✅ Ferma e chiude il loop asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            print("🛑 [DEBUG] Fermando il loop asyncio...")
            loop.stop()

        print("✅ Script terminato correttamente.")
        os._exit(0)

# ✅ Registra un handler per catturare SIGINT (CTRL+C) in modo pulito
def shutdown_handler(signal_received, frame):
    print("\n🛑 [DEBUG] Interruzione manuale rilevata, chiusura immediata...")
    os._exit(0)

if __name__ == "__main__":
    # Registra il signal handler per terminare lo script con CTRL+C
    signal.signal(signal.SIGINT, shutdown_handler)

    try:
        print("🟢 [DEBUG] Avvio di asyncio.run(main())...")
        asyncio.run(main())
        print("🔴 [DEBUG] asyncio.run(main()) è terminato.")
    except KeyboardInterrupt:
        print("\n🛑 [DEBUG] Script interrotto con CTRL+C.")
        sys.exit(0)
