import asyncio
from pyremoteplay import RPDevice
from pyremoteplay.profile import Profiles

# Imposta il percorso predefinito per il file dei profili
Profiles.set_default_path(r"C:\Users\ADB\.pyremoteplay\.profile.json")

# Carica i profili salvati dal file
profiles = Profiles.load()

if not profiles.users:
    print("❌ Nessun profilo registrato! Esegui prima la registrazione dell'account PSN.")
    exit()

# Mostra i nomi reali degli account PSN registrati
print("\n🎮 Account registrati:")
for username in profiles.data.keys():
    print(f"- {username}")

# L'utente sceglie quale profilo usare
account_name = input("\nInserisci il nome dell'account da usare: ").strip()

# Recupera il profilo selezionato
user_profile = profiles.data.get(account_name)
if user_profile is None:
    print("❌ Errore: l'account non esiste!")
    exit()

# Mostra le console registrate per questo account
if not user_profile["hosts"]:
    print("❌ Nessuna console registrata per questo profilo.")
    exit()

print("\n🖥️ Console registrate:")
for mac, details in user_profile["hosts"].items():
    print(f"- MAC: {mac.upper()}, Nome: {details['data'].get('Nickname', 'Sconosciuto')}")

# L'utente sceglie la console da usare
console_mac = input("\nInserisci l'indirizzo MAC della console da usare: ").strip().lower()

# Convertiamo tutte le chiavi in minuscolo per evitare problemi di maiuscole/minuscole
user_profile["hosts"] = {k.lower(): v for k, v in user_profile["hosts"].items()}

if console_mac not in user_profile["hosts"]:
    print("❌ Console non trovata!")
    exit()

# Recupera l'IP della console
console_ip = input(f"Inserisci l'IP della console {console_mac}: ").strip()

# Inizializza il dispositivo Remote Play
device = RPDevice(console_ip)

async def main():
    try:
        print("🔌 Avviando sessione Remote Play...")
        
        # Creiamo una sessione per l'account selezionato
        session = device.create_session(user=account_name, resolution="720p", fps="high")

        if session is None:
            print("❌ Errore: impossibile creare la sessione. Verifica che l'account sia registrato correttamente.")
            exit()
        
        # Connettiamo la sessione alla console
        await device.connect()
        
        # Aspettiamo che la sessione sia pronta
        print("⏳ Attendi che la sessione sia pronta...")
        await device.wait_for_session()
        
        if device.ready:
            print("✅ Sessione pronta! Digita 'exit' per disconnetterti.")
            
            # Rimane in attesa dell'input dell'utente per terminare la sessione
            while True:
                comando = input("\nDigita 'exit' per terminare la sessione: ").strip().lower()
                if comando == "exit":
                    print("❌ Disconnessione in corso...")
                    break

        else:
            print("❌ La sessione non è pronta!")

    except Exception as e:
        print(f"❌ Errore durante la sessione: {e}")

    finally:
        print("🔌 Disconnettendo la sessione...")
        await device.disconnect()
        print("✅ Disconnessione completata.")

# Esegui l'evento asincrono
asyncio.run(main())
