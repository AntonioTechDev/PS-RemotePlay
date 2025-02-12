import asyncio
from pyremoteplay import RPDevice
from pyremoteplay.profile import Profiles

# Imposta il percorso predefinito per il file dei profili
Profiles.set_default_path(r"C:\Users\ADB\.pyremoteplay\.profile.json")

# Carica i profili salvati
profiles = Profiles.load()

# Verifica se ci sono account registrati
if not profiles.users:
    print("❌ Nessun account registrato. Esegui prima la registrazione con link_account.py!")
    exit()

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

# ✅ Debug per verificare i dati dell'account selezionato
print("\n🔍 Debug: Dati dell'account selezionato:", selected_user)

# ✅ Recupera le console registrate per quell'account
user_hosts = selected_user.hosts if hasattr(selected_user, 'hosts') else selected_user.get("hosts", {})

# **✅ Controllo se `user_hosts` è una LISTA invece di un DIZIONARIO**
if isinstance(user_hosts, list):
    print("⚠️ Dati delle console in formato errato, correggiamo automaticamente...")
    new_hosts = {}
    for item in user_hosts:
        mac_address = item.get("Mac")  # Recuperiamo il MAC come chiave
        if mac_address:
            new_hosts[mac_address.upper()] = {
                "data": item,
                "type": "PS4"
            }
    user_hosts = new_hosts  # Aggiorniamo il valore corretto

# ✅ Controllo se ci sono console registrate
if not user_hosts:
    print(f"❌ Nessuna console registrata per l'account {selected_user.name}. Associa una console prima di procedere.")
    exit()

print("\n🖥️ Console registrate:")
console_list = list(user_hosts.keys())  # Ora user_hosts è un dict, quindi possiamo usare .keys()
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

# ✅ Recupera l'IP se presente nei dati salvati
ip_address = user_hosts[selected_mac]["data"].get("IP")

# ✅ Se l'IP non è registrato, chiedilo all'utente
if not ip_address:
    ip_address = input(f"\nInserisci l'IP della console {user_hosts[selected_mac]['data']['Nickname']}: ").strip()
    user_hosts[selected_mac]["data"]["IP"] = ip_address  # Salva l'IP per usi futuri
    profiles.save()

print(f"\n📡 IP della console selezionato: {ip_address}")

# ✅ Creazione del dispositivo Remote Play
device = RPDevice(ip_address)

async def main(user_profile):
    try:
        # ✅ Verifica lo stato della console
        print("\n🔌 Verifica stato della console...")
        status = device.get_status()

        if not status:
            print("❌ Errore: impossibile ottenere lo stato della console. Assicurati che sia accesa e connessa alla rete.")
            return

        # ✅ Recuperiamo il profilo corretto dell'utente per questa console
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

        # ✅ Connessione alla sessione
        success = await device.connect()
        if not success:
            print("❌ Errore: Connessione alla sessione Remote Play fallita.")
            return

        print(f"✅ Sessione avviata con successo per {user_profile.name} su {user_hosts[selected_mac]['data']['Nickname']}!")

        # ✅ Attendi il comando per chiudere la sessione
        while True:
            exit_cmd = input("\n✏️ Digita 'exit' per terminare la sessione: ").strip().lower()
            if exit_cmd == "exit":
                break

        # ✅ Disconnessione e chiusura della sessione
        print("\n🔌 Disconnessione della sessione...")
        await device.disconnect()
        print("✅ Sessione terminata con successo!")

    except Exception as e:
        print(f"❌ Errore durante la sessione: {e}")

# Avvia il loop asyncio per gestire la sessione, passando `selected_user`
asyncio.run(main(selected_user))
