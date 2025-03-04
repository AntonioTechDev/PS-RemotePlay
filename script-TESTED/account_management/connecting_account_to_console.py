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
    print("🔍 [DEBUG] Tentativo di connessione all'IP:", ip_address)
    status = device.get_status()
    print("🔍 [DEBUG] Stato ricevuto:", status)
    
    if not status:
        print("❌ Impossibile ottenere lo stato della console. Verifica che sia accesa e connessa alla rete.")
        print("🔍 [DEBUG] Nessun dato ricevuto dalla console. Verifica firewall, connessione di rete e che la console sia accesa.")
        exit()
        
    print("✅ Stato della console verificato correttamente.")
    print("🔍 [DEBUG] Tipo console:", status.get("host-type", "sconosciuto"))
    print("🔍 [DEBUG] Nome console:", status.get("host-name", "sconosciuto"))
    print("🔍 [DEBUG] MAC Address:", status.get("host-id", "sconosciuto"))
    
    print("\n🔗 Registrazione del dispositivo...")
    print("🔍 [DEBUG] Tentativo di registrazione con utente:", user_profile.name)
    print("🔍 [DEBUG] PIN inserito:", pin)
    result = device.register(user_profile.name, pin, save=True)
    print("🔍 [DEBUG] Risultato registrazione:", result)
    
    if not result:
        print("❌ Registrazione fallita. Verifica il PIN e riprova.")
        print("🔍 [DEBUG] Registrazione non riuscita. Possibili cause: PIN errato, timeout, console non in modalità associazione.")
        exit()
    
    print("✅ Dispositivo registrato correttamente.")
    print("🔍 [DEBUG] Dati di registrazione:", result)
    
    # Salva l'IP della console nel profilo
    try:
        print("🔍 [DEBUG] Tentativo di aggiornamento dell'IP nel profilo...")
        update_profile_data(user_profile.name, "IP", ip_address)
        print("✅ IP della console salvato correttamente.")
    except Exception as ip_error:
        print(f"⚠️ Avviso: Impossibile salvare l'IP nel profilo: {ip_error}")
        print(f"🔍 [DEBUG] Errore dettagliato: {str(ip_error)}")
        # Continuiamo comunque perché questo non è critico
    
    print(f"✅ Collegamento dell'account '{user_profile.name}' con la console completato con successo!")
    print("🔍 [DEBUG] Processo completato senza errori.")
    
except Exception as e:
    print(f"❌ Errore durante il collegamento: {e}")
    print(f"🔍 [DEBUG] Eccezione completa: {type(e).__name__}: {str(e)}")
    import traceback
    print("🔍 [DEBUG] Traceback completo:")
    traceback.print_exc()
    print("Il processo è stato interrotto. Riprova con parametri corretti.")