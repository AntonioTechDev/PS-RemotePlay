# 📌 PS Remote Play - Guida Completa

Questa guida fornisce istruzioni dettagliate per l'utilizzo degli script per collegare e gestire account PSN con Remote Play utilizzando la libreria `pyremoteplay`.

## 📜 **Indice**
1. [Prerequisiti](#prerequisiti)
2. [Registrazione di un account PSN](#registrazione-di-un-account-psn)
3. [Collegamento di un account a una console](#collegamento-di-un-account-a-una-console)
4. [Avvio e gestione di una sessione Remote Play](#avvio-e-gestione-di-una-sessione-remote-play)
5. [Gestione avanzata della sessione](#gestione-avanzata-della-sessione)
6. [Risoluzione dei problemi](#risoluzione-dei-problemi)

---

## 📌 **Prerequisiti**
- Installare Python 3.10 o superiore.
- Installare le dipendenze richieste eseguendo:
  ```sh
  pip install -r requirements.txt
  ```
- Disporre di un account PSN valido e di una console PlayStation compatibile con Remote Play.
- Assicurarsi che la console sia accesa e connessa alla stessa rete del PC.

---

## 🎮 **Registrazione di un account PSN**
📌 **Script da eseguire:** `link_account.py`

1. Eseguire il comando:
   ```sh
   python link_account.py
   ```
2. Seguire le istruzioni per accedere con il proprio account PSN.
3. Copiare l'URL di redirect generato e incollarlo nella console quando richiesto.
4. Se tutto è corretto, il profilo verrà salvato nel file `.pyremoteplay/.profile.json`.

### ⚠ **Nota**
Se si verificano errori durante il login, cambiare l'indirizzo MAC della scheda di rete con **Technitium MAC Address Changer V6**, ricaricare la pagina di login e riprovare.

---

## 🎮 **Collegamento di un account a una console**
📌 **Script da eseguire:** `connecting_account_to_console.py`

1. Eseguire il comando:
   ```sh
   python connecting_account_to_console.py
   ```
2. Selezionare l'account PSN registrato.
3. Inserire l'indirizzo IP della console (visibile nelle impostazioni di rete della PlayStation).
4. Inserire il codice PIN mostrato nelle impostazioni di **Riproduzione Remota** della console.
5. Se tutto è corretto, la console verrà registrata nel file `.pyremoteplay/.profile.json` associata all'account.

### ⚠ **Nota**
- Quando si collega un account alla console, assicurarsi che sia **l'unico account connesso** e che sia **l'account principale** sulla console.

---

## 🎮 **Avvio e gestione di una sessione Remote Play**
📌 **Script da eseguire:** `session.py`

1. Eseguire il comando:
   ```sh
   python session.py
   ```
2. Selezionare l'account PSN che si desidera utilizzare per la sessione.
3. Selezionare la console a cui connettersi.
4. Se richiesto, inserire l'IP della console.
5. Attendere che la sessione venga avviata correttamente.
6. La sessione invierà automaticamente una serie di comandi per testare la connessione.
7. Per terminare la sessione, digitare `exit` o attendere la chiusura automatica dello script.

---

## 🎮 **Gestione avanzata della sessione**
📌 **Script coinvolti:** `session.py`, `remote_play_controller.py`

### 📌 **`remote_play_controller.py`**
Questo file contiene tutte le funzioni dedicate alla gestione della sessione e del controller. Ecco una panoramica delle funzioni principali:

- **`initialize_controller(device)`**: Avvia il controller per la sessione.
- **`send_test_commands(device)`**: Invia una serie di comandi per verificare il funzionamento dei controlli.
- **`safe_disconnect(device)`**: Garantisce una disconnessione sicura evitando errori.
- **`connect_and_run_session(user_profile, selected_mac, ip_address)`**: Avvia la sessione Remote Play per l'account selezionato e la console corrispondente.

### 📌 **`session.py`**
Questo script permette di avviare una sessione selezionando l'account e la console desiderata. Si basa sulle funzioni definite in `remote_play_controller.py` per gestire la connessione e i comandi del controller.

Eseguendo `session.py`, lo script:
1. Mostrerà gli account PSN registrati.
2. Permetterà di selezionare la console associata.
3. Recupererà automaticamente l'IP della console (o lo chiederà se non è presente).
4. Avvierà la sessione e il controller.
5. Eseguirà una serie di comandi per testare la connessione.
6. Disconnetterà automaticamente la sessione al termine.


---

## 🛠 **Risoluzione dei problemi**

### 🔹 **Errore di autenticazione PSN (Errore 400 o 403)**
- Assicurarsi di copiare l'URL di redirect completo.
- Provare a cambiare l'indirizzo MAC con **Technitium MAC Address Changer V6** e ripetere il login.

### 🔹 **Impossibile connettere l'account alla console**
- Assicurarsi che la console sia accesa e connessa alla stessa rete.
- Controllare che l'account selezionato sia **l'unico connesso** sulla console.
- Verificare l'IP corretto della console nelle impostazioni di rete della PlayStation.

### 🔹 **Errore durante la creazione della sessione Remote Play**
- Controllare che la console sia accesa e in modalità riposo con **Riproduzione remota abilitata**.
- Provare a riavviare sia il PC che la console.

---

## ✅ **Workflow completo**
1. **Registrare l'account PSN** usando `link_account.py`.
2. **Collegare l'account alla console** usando `connecting_account_to_console.py`.
3. **Avviare la sessione Remote Play ed eseguire comandi** con `session.py`.
4. **Terminare la sessione in sicurezza**.

🚀 Ora sei pronto a usare Remote Play con il tuo account PSN! 🎮🔥

