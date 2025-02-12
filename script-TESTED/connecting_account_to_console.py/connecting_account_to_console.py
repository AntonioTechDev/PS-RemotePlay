from pyremoteplay import RPDevice
from pyremoteplay.profile import Profiles

# Imposta il percorso predefinito per il file dei profili (se necessario)
Profiles.set_default_path(r"C:\Users\ADB\.pyremoteplay\.profile.json")

# Carica i profili salvati dal file
profiles = Profiles.load()

# Mostra gli account registrati
print("\n🎮 Account registrati:")
for i, user in enumerate(profiles.users):
    print(f"{i + 1}. {user.name}")

# Verifica se esiste almeno un profilo registrato
if not profiles.users:
    print("❌ Nessun profilo registrato. Registra prima un account PSN!")
    exit()

# Scelta dell'account da usare
while True:
    try:
        choice = int(input("\nSeleziona l'account da utilizzare (inserisci il numero): "))
        if 1 <= choice <= len(profiles.users):
            user_profile = profiles.users[choice - 1]
            break
        else:
            print("⚠️ Numero non valido. Scegli un numero tra quelli disponibili.")
    except ValueError:
        print("⚠️ Inserisci un numero valido!")

# Inserimento dell'IP della console
ip_address = input(f"\nInserisci l'indirizzo IP della console per {user_profile.name}: ").strip()

# Inserimento del PIN della console
pin = input("Inserisci il PIN di collegamento dalla tua console: ").strip()

# Inizializza il dispositivo Remote Play
device = RPDevice(ip_address)

try:
    print("\n🔌 Verifica stato della console...")
    device.get_status()  # Questo metodo dovrebbe restituire lo stato della console

    print("\n🔗 Registrazione del dispositivo...")
    device.register(user_profile.name, pin, save=True)

    print(f"✅ Collegamento dell'account '{user_profile.name}' con la console completato con successo!")
except Exception as e:
    print(f"❌ Errore durante il collegamento: {e}")
