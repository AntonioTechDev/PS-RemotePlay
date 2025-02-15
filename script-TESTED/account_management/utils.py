import json
from pyremoteplay.profile import Profiles

PROFILE_PATH = r"C:\Users\ADB\.pyremoteplay\.profile.json"

Profiles.set_default_path(PROFILE_PATH)
profiles = Profiles.load()

def get_user_profile():
    """Permette all'utente di selezionare un account registrato."""
    if not profiles.users:
        print("❌ Nessun profilo registrato. Registra prima un account PSN!")
        exit()
    
    print("\n🎮 Account registrati:")
    for i, user in enumerate(profiles.users):
        print(f"{i + 1}. {user.name}")

    while True:
        try:
            choice = int(input("\nSeleziona l'account da utilizzare (inserisci il numero): "))
            if 1 <= choice <= len(profiles.users):
                return profiles.users[choice - 1]
            else:
                print("⚠️ Numero non valido. Scegli un numero tra quelli disponibili.")
        except ValueError:
            print("⚠️ Inserisci un numero valido!")

def get_registered_consoles(user_profile):
    """Recupera le console registrate per un dato utente e corregge eventuali errori di formato."""
    user_hosts = user_profile.hosts if hasattr(user_profile, "hosts") else user_profile.get("hosts", {})

    if isinstance(user_hosts, list):
        print("⚠️ Errore nel formato dei dati delle console. Correggiamo...")
        user_hosts = {entry["Mac"].upper(): {"data": entry, "type": "PS4"} for entry in user_hosts}

    return user_hosts

def update_profile_data(user_name, key, value):
    """Aggiorna un valore specifico nei dati del profilo e lo salva su file."""
    with open(PROFILE_PATH, "r") as file:
        profile_data = json.load(file)

    if user_name in profile_data:
        for mac_address, host_data in profile_data[user_name]["hosts"].items():
            if "data" in host_data:
                host_data["data"][key] = value

    with open(PROFILE_PATH, "w") as file:
        json.dump(profile_data, file, indent=4)
