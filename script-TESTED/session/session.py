import asyncio
from pyremoteplay import RPDevice
from pyremoteplay.profile import Profiles
from remote_play.session_manager import connect_and_run_session
from remote_play.utils import clean_frame_directory

# ✅ Imposta il percorso del profilo
Profiles.set_default_path(r"C:\Users\ADB\.pyremoteplay\.profile.json")

# ✅ Carica i profili salvati
profiles = Profiles.load()

async def main():
    """ Selezione dell'account e avvio della sessione Remote Play. """
    print("\n🎮 Account registrati:")
    for i, user in enumerate(profiles.users):
        print(f"{i + 1}. {user.name}")

    while True:
        try:
            account_choice = int(input("\nSeleziona l'account da utilizzare (inserisci il numero): "))
            if 1 <= account_choice <= len(profiles.users):
                selected_user = profiles.users[account_choice - 1]
                break
            else:
                print("⚠️ Numero non valido.")
        except ValueError:
            print("⚠️ Inserisci un numero valido!")

    # ✅ Pulizia della cartella dei frame all'avvio
    clean_frame_directory(selected_user.name)

    # ✅ Selezione della console
    user_hosts = selected_user.hosts if hasattr(selected_user, 'hosts') else selected_user.get("hosts", {})

    if isinstance(user_hosts, list):
        print("⚠️ Errore nel formato dei dati delle console. Correggiamo...")
        user_hosts = {entry["Mac"].upper(): {"data": entry, "type": "PS4"} for entry in user_hosts}

    print("\n🖥️ Console registrate:")
    console_list = list(user_hosts.keys())
    for i, mac in enumerate(console_list):
        nickname = user_hosts[mac]["data"]["Nickname"]
        print(f"{i + 1}. {nickname} (MAC: {mac})")

    while True:
        try:
            console_choice = int(input("\nSeleziona la console da utilizzare (inserisci il numero): "))
            if 1 <= console_choice <= len(console_list):
                selected_mac = console_list[console_choice - 1]
                break
            else:
                print("⚠️ Numero non valido.")
        except ValueError:
            print("⚠️ Inserisci un numero valido!")

    ip_address = user_hosts[selected_mac]["data"].get("IP")
    if not ip_address:
        ip_address = input(f"\nInserisci l'IP della console {user_hosts[selected_mac]['data']['Nickname']}: ").strip()
        user_hosts[selected_mac]["data"]["IP"] = ip_address
        profiles.save()

    print(f"\n📡 IP della console selezionato: {ip_address}")

    # ✅ Avvio della sessione con gestione video e comandi
    await connect_and_run_session(selected_user, selected_mac, ip_address)

if __name__ == "__main__":
    asyncio.run(main())
