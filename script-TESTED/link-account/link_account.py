from pyremoteplay.profile import Profiles, format_user_account
from pyremoteplay import oauth

# Genera l'URL per il login PSN
login_url = oauth.get_login_url()
print("\n🔗 APRI QUESTO URL IN UN BROWSER E FA IL LOGIN CON IL TUO ACCOUNT PSN:")
print(login_url)

# L'utente deve incollare l'URL di redirect dopo il login
redirect_url = input("\nINSERISCI L'URL DI REDIRECT: ").strip()

# Recupera i dati dell'account
account = oauth.get_user_account(redirect_url)

# ✅ Stampiamo i dati ricevuti per debugging
print("\n🔍 Dati ricevuti dall'account:")
print(account)

# Controllo se il recupero dell'account ha avuto successo
if account is None:
    print("❌ Errore: impossibile ottenere le credenziali PSN. Verifica il link di redirect e riprova.")
    exit()

# ✅ Formattiamo l'account usando `format_user_account()` da `profile.py`
user_profile = format_user_account(account)

# Controllo se la formattazione ha avuto successo
if user_profile is None:
    print("❌ Errore: L'account non contiene un ID valido. Controlla i dati ricevuti.")
    exit()

# ✅ Carichiamo i profili esistenti PRIMA di aggiornare il file
profiles = Profiles.load()  # <-- IMPORTANTE: carica il file senza sovrascrivere

# ✅ Controlliamo se l'utente è già registrato
if user_profile.name in profiles.usernames:
    print(f"⚠️ L'account '{user_profile.name}' è già registrato. Non verrà sovrascritto.")
else:
    # ✅ Aggiungiamo il nuovo utente SENZA rimuovere quelli esistenti
    profiles.update_user(user_profile)
    profiles.save()  # Salviamo il file senza perdere altri account

    print(f"✅ Account '{user_profile.name}' registrato con successo!")
