import asyncio
from pyremoteplay import RPDevice
from pyremoteplay.profile import Profiles

# Imposta il percorso predefinito per il file dei profili
Profiles.set_default_path(r"C:\Users\ADB\.pyremoteplay\.profile.json")

# Carica i profili salvati
profiles = Profiles.load()

# ✅ Funzione per avviare il controller
def initialize_controller(device):
    """Avvia il controller del dispositivo Remote Play."""
    print("🎮 Inizializzazione del controller...")
    device.controller.start()
    print("✅ Controller attivato!")

# ✅ Mostra gli account registrati
print("\n🎮 Account registrati:")
for i, user in enumerate(profiles.users):
    print(f"{i + 1}. {user.name}")

# ✅ Selezione dell'account da utilizzare
while True:
    try:
        account_choice = int(input("\nSeleziona l'account da utilizzare (inserisci il numero): "))
        if 1 <= account_choice <= len(profiles.users):
            selected_user = profiles.users[account_choice - 1]
            break
        else:
            print("⚠️ Numero non valido. Scegli un numero tra quelli disponibili.")
    except ValueError:
        print("⚠️ Inserisci un numero valido!")

# ✅ Recupera le console registrate per quell'account
user_hosts = selected_user.hosts if hasattr(selected_user, 'hosts') else selected_user.get("hosts", {})

# ✅ FIX: Verifica che `user_hosts` sia un dizionario, se è una lista, la converte
if isinstance(user_hosts, list):
    print("⚠️ Errore nel formato dei dati delle console. Correggiamo...")
    user_hosts = {entry["Mac"].upper(): {"data": entry, "type": "PS4"} for entry in user_hosts}

if not user_hosts:
    print(f"❌ Nessuna console registrata per l'account {selected_user.name}.")
    exit()

# ✅ Mostra le console disponibili
print("\n🖥️ Console registrate:")
console_list = list(user_hosts.keys())
for i, mac in enumerate(console_list):
    nickname = user_hosts[mac]["data"]["Nickname"]
    print(f"{i + 1}. {nickname} (MAC: {mac})")

# ✅ Selezione della console
while True:
    try:
        console_choice = int(input("\nSeleziona la console da utilizzare (inserisci il numero): "))
        if 1 <= console_choice <= len(console_list):
            selected_mac = console_list[console_choice - 1]
            break
        else:
            print("⚠️ Numero non valido. Scegli un numero tra quelli disponibili.")
    except ValueError:
        print("⚠️ Inserisci un numero valido!")

# ✅ Recupera l'IP della console
ip_address = user_hosts[selected_mac]["data"].get("IP")
if not ip_address:
    ip_address = input(f"\nInserisci l'IP della console {user_hosts[selected_mac]['data']['Nickname']}: ").strip()
    user_hosts[selected_mac]["data"]["IP"] = ip_address
    profiles.save()

print(f"\n📡 IP della console selezionato: {ip_address}")

# ✅ Creazione del dispositivo Remote Play
device = RPDevice(ip_address)

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

# ✅ Comandi di test automatici
async def send_test_commands(device):
    """Invia una serie di comandi di test per verificare il controller."""
    test_commands = ["CROSS", "CIRCLE", "SQUARE", "TRIANGLE", "UP", "DOWN", "LEFT", "RIGHT", "OPTIONS"]
    print("\n🎮 Esecuzione dei comandi di test...")
    
    for command in test_commands:
        try:
            device.controller.button(command, "tap")
            print(f"✅ Comando {command} inviato!")
            await asyncio.sleep(1)  # Attendere tra un comando e l'altro
        except Exception as e:
            print(f"❌ Errore nell'invio del comando {command}: {e}")

# ✅ Avvio della sessione
async def main(user_profile):
    try:
        # ✅ Verifica stato della console
        print("\n🔌 Verifica stato della console...")
        status = device.get_status()

        if not status:
            print("❌ Errore: impossibile ottenere lo stato della console.")
            return

        # ✅ Recupera il profilo corretto dell'utente
        user_profile = profiles.get_user_profile(user_profile.name)
        if not user_profile:
            print(f"❌ Errore: L'utente {user_profile.name} non è registrato correttamente.")
            return

        # ✅ Creazione della sessione Remote Play
        print("\n🎮 Avvio della sessione Remote Play...")
        session = device.create_session(user=user_profile.name, profiles=profiles)

        if not session:
            print("❌ Errore: impossibile creare la sessione Remote Play.")
            return

        # ✅ Avvio della sessione
        success = await device.connect()
        if not success:
            print("❌ Errore: Connessione alla sessione Remote Play fallita.")
            return

        print(f"✅ Sessione avviata con successo per {user_profile.name} su {user_hosts[selected_mac]['data']['Nickname']}!")

        # ✅ Inizializzazione del controller
        initialize_controller(device)

        # ✅ Aspetta qualche secondo per essere sicuri che la sessione sia pronta
        await asyncio.sleep(3)

        # ✅ Stampa lo stato della sessione prima di inviare i comandi
        print(f"\n🔍 Stato della sessione prima di inviare comandi: {device.session}")

        # ✅ Esegui i comandi di test
        await send_test_commands(device)

        # ✅ Disconnessione e chiusura sessione
        print("\n🔌 Disconnessione della sessione...")
        await safe_disconnect(device)
        print("✅ Sessione terminata con successo!")

    except Exception as e:
        print(f"❌ Errore durante la sessione: {e}")

# Avvia il loop asyncio per gestire la sessione
asyncio.run(main(selected_user))
