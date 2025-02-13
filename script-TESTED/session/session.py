import asyncio
from pyremoteplay.profile import Profiles
from remote_play_controller import connect_and_run_session

# Imposta il percorso predefinito per il file dei profili
Profiles.set_default_path(r"C:\Users\ADB\.pyremoteplay\.profile.json")

# Carica i profili salvati
profiles = Profiles.load()

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

# ✅ FIX: Verifica che `user_hosts` sia un dizionario
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

# ✅ Avvia la sessione con l'account selezionato
asyncio.run(connect_and_run_session(selected_user, selected_mac, ip_address))
