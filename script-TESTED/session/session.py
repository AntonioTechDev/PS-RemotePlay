import asyncio
from remote_play.session_manager import EnhancedSessionManager
import sys
import os
import signal
import logging
from remote_play.network_monitor import check_connection

# Aggiungi il path della cartella superiore
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from account_management.utils import get_user_profile, get_registered_consoles

# Configurazione logging
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
    """ Selezione dell'account e avvio della sessione Remote Play con implementazione ottimizzata. """
    try:
        logger.info("🔍 [DEBUG] Avvio del processo di selezione account e console...")
        user_profile = get_user_profile()
        user_hosts = get_registered_consoles(user_profile)

        logger.info("\n🖥️ Console registrate:")
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
            logger.error("❌ Input non valido. Riprova.")
            return

        selected_mac = console_list[console_choice]
        ip_address = user_hosts[selected_mac]["data"].get("IP")

        logger.info(f"\n📡 IP della console selezionato: {ip_address}")
        
        # Verifica preliminare della connessione
        logger.info("\n🔍 Verifica preliminare della connessione...")
        connection_status = await check_connection(ip_address)
        
        if connection_status["ping_success"] and connection_status["port_open"]:
            logger.info(f"✅ Connessione verificata: Ping {connection_status['ping_time']:.1f}ms")
        else:
            issues = []
            if not connection_status["ping_success"]:
                issues.append("ping fallito")
            if not connection_status["port_open"]:
                issues.append("porta chiusa")
                
            logger.warning(f"⚠️ Problemi di connessione rilevati: {', '.join(issues)}")
            confirm = input("Vuoi tentare comunque la connessione? (s/n): ")
            
            if confirm.lower() != 's':
                logger.info("Operazione annullata dall'utente.")
                return

        # Avvio della sessione Remote Play con il gestore ottimizzato
        logger.info("🚀 [DEBUG] Avvio della sessione Remote Play ottimizzata...")
        
        # Usa il gestore di sessione avanzato
        session_manager = EnhancedSessionManager()
        await session_manager.connect_and_run_session(user_profile, selected_mac, ip_address)
        
        logger.info("✅ [DEBUG] Sessione Remote Play terminata correttamente.")

    except KeyboardInterrupt:
        logger.info("\n🛑 [DEBUG] Interruzione manuale rilevata. Chiudo tutte le sessioni...")

    finally:
        logger.info("🔄 [DEBUG] Avvio della fase di terminazione dello script...")

        # ✅ Cancella tutti i task ancora attivi
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        logger.info(f"🔎 [DEBUG] Task trovati in esecuzione: {len(tasks)}")

        for task in tasks:
            logger.info(f"⚠️ [DEBUG] Cancellazione task: {task}")
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.info(f"✅ [DEBUG] Task {task} cancellato correttamente.")

        # ✅ Ferma e chiude il loop asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            logger.info("🛑 [DEBUG] Fermando il loop asyncio...")
            loop.stop()

        logger.info("✅ Script terminato correttamente.")
        os._exit(0)

# ✅ Registra un handler per catturare SIGINT (CTRL+C) in modo pulito
def shutdown_handler(signal_received, frame):
    logger.info("\n🛑 [DEBUG] Interruzione manuale rilevata, chiusura immediata...")
    os._exit(0)

if __name__ == "__main__":
    # Registra il signal handler per terminare lo script con CTRL+C
    signal.signal(signal.SIGINT, shutdown_handler)

    try:
        logger.info("🟢 [DEBUG] Avvio di asyncio.run(main())...")
        asyncio.run(main())
        logger.info("🔴 [DEBUG] asyncio.run(main()) è terminato.")
    except KeyboardInterrupt:
        logger.info("\n🛑 [DEBUG] Script interrotto con CTRL+C.")
        sys.exit(0)