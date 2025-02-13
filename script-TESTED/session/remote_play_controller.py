import asyncio
from pyremoteplay import RPDevice
from pyremoteplay.profile import Profiles

# Imposta il percorso predefinito per il file dei profili
Profiles.set_default_path(r"C:\Users\ADB\.pyremoteplay\.profile.json")

# Carica i profili salvati
profiles = Profiles.load()

def initialize_controller(device):
    """Attiva il controller della sessione."""
    print("🎮 Inizializzazione del controller...")
    device.controller.start()
    print("✅ Controller attivato!")

async def send_test_commands(device):
    """Esegue una sequenza di comandi di test."""
    commands = ["CROSS", "CIRCLE", "SQUARE", "TRIANGLE", "UP", "DOWN", "LEFT", "RIGHT", "OPTIONS"]
    
    for command in commands:
        device.controller.button(command, "tap")
        print(f"✅ Comando {command} inviato!")
        await asyncio.sleep(1)  # Aspetta 1 secondo tra i comandi

# ✅ Funzione per disconnettere in sicurezza
async def safe_disconnect(device):
    """Gestisce la disconnessione sicura della sessione Remote Play."""
    if device.session:
        print("\n🔌 Tentativo di disconnessione in corso...")

        if device.connected:
            print("⏳ Arresto della sessione in corso...")
            device.session.stop()
            await asyncio.sleep(2)  # Attende per garantire la chiusura

        # Imposta la sessione a None per forzare la disconnessione
        device._session = None
        print("✅ Sessione disconnessa correttamente!")
    else:
        print("⚠️ Nessuna sessione attiva da disconnettere.")

async def connect_and_run_session(user_profile, selected_mac, ip_address):
    """Connette l'utente alla sessione Remote Play e invia comandi di test."""
    device = RPDevice(ip_address)

    try:
        print("\n🔌 Verifica stato della console...")
        status = device.get_status()

        if not status:
            print("❌ Errore: impossibile ottenere lo stato della console.")
            return

        user_profile = profiles.get_user_profile(user_profile.name)
        if not user_profile:
            print(f"❌ Errore: L'utente {user_profile.name} non è registrato correttamente.")
            return

        print("\n🎮 Avvio della sessione Remote Play...")
        session = device.create_session(user=user_profile.name, profiles=profiles)

        if not session:
            print("❌ Errore: impossibile creare la sessione Remote Play.")
            return

        success = await device.connect()
        if not success:
            print("❌ Errore: Connessione alla sessione Remote Play fallita.")
            return

        print(f"✅ Sessione avviata con successo per {user_profile.name}!")

        initialize_controller(device)

        # Aspetta qualche secondo prima di inviare i comandi
        await asyncio.sleep(3)

        print(f"\n🔍 Stato della sessione prima di inviare comandi: {device.session}")

        await send_test_commands(device)

    except Exception as e:
        print(f"❌ Errore durante la sessione: {e}")

    finally:
        print("\n🔌 Disconnessione della sessione...")
        await safe_disconnect(device)
