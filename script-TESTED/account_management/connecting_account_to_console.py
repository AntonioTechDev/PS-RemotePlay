from pyremoteplay import RPDevice
import sys
import os
# Aggiungi il path della cartella superiore
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from account_management.utils import get_user_profile, update_profile_data

# Selezione dell'account
user_profile = get_user_profile()

# Inserimento dell'IP e del PIN della console
ip_address = input(f"\nInserisci l'indirizzo IP della console per {user_profile.name}: ").strip()
pin = input("Inserisci il PIN di collegamento dalla tua console: ").strip()

# Inizializza il dispositivo Remote Play
device = RPDevice(ip_address)

try:
    print("\n🔌 Verifica stato della console...")
    device.get_status()  

    print("\n🔗 Registrazione del dispositivo...")
    device.register(user_profile.name, pin, save=True)

    # Salva l'IP della console nel profilo
    update_profile_data(user_profile.name, "IP", ip_address)

    print(f"✅ Collegamento dell'account '{user_profile.name}' con la console completato con successo!")
except Exception as e:
    print(f"❌ Errore durante il collegamento: {e}")
