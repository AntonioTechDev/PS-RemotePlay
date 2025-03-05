# 🎮 PS Remote Play - Guida Completa

Questa guida fornisce istruzioni dettagliate per l'utilizzo degli script per collegare e gestire account PSN con Remote Play utilizzando la libreria `pyremoteplay`.

---

## 📜 **Indice**
1. [Prerequisiti](#prerequisiti)
2. [Registrazione di un account PSN](#registrazione-di-un-account-psn)
3. [Collegamento di un account a una console](#collegamento-di-un-account-a-una-console)
4. [Avvio e gestione di una sessione Remote Play](#avvio-e-gestione-di-una-sessione-remote-play)
5. [Funzionalità avanzate](#funzionalità-avanzate)
6. [Struttura del codice](#struttura-del-codice)
7. [Risoluzione dei problemi](#risoluzione-dei-problemi)

---

## 📌 **Prerequisiti**
- Installare Python 3.10.11.
- Installare le dipendenze richieste eseguendo:
  ```sh
  pip install -r requirements.txt
  ```
- Disporre di un account PSN valido e di una console PlayStation compatibile con Remote Play.
- Assicurarsi che la console sia accesa e connessa alla stessa rete del PC.

---

## 🎮 **Registrazione di un account PSN**
📌 **Script da eseguire:** `link_account.py`

> **Nota Importante**: Questo script inizializza solamente l'account nel file `.pyremoteplay/.profile.json` creando una struttura base. Il collegamento alla console avverrà tramite lo script successivo.

1. Eseguire il comando:
   ```sh
   python -m account_management.link_account
   ```
2. Seguire le istruzioni per accedere con il proprio account PSN.
3. Copiare l'URL di redirect generato e incollarlo nella console quando richiesto.
4. Se tutto è corretto, il profilo verrà inizializzato nel file `.pyremoteplay/.profile.json` con una struttura simile a:
   ```json
   "nome_utente": {
       "id": "base64_encoded_id",
       "hosts": {}
   }
   ```

---

## 🎮 **Collegamento di un account a una console**## 🎮 **Collegamento di un account a una console**
📌 **Script da eseguire:** `connecting_account_to_console.py`

> **Nota Importante**: Questo script completa il processo di registrazione collegando effettivamente l'account PSN alla console e popolando i dati nella sezione "hosts" del file `.profile.json`.

1. Assicurarsi che la console sia accesa e che il Remote Play sia abilitato nelle impostazioni.
2. Eseguire il comando:
   ```sh
   python -m account_management.connecting_account_to_console
   ```
3. Selezionare l'account PSN registrato nel passaggio precedente.
4. Inserire l'indirizzo IP della console (visibile nelle impostazioni di rete della PlayStation).
5. Inserire il codice PIN mostrato nelle impostazioni di **Riproduzione Remota** della console.
6. Se tutto è corretto, la console verrà registrata nel file `.pyremoteplay/.profile.json` associata all'account, e la sezione "hosts" verrà popolata con tutti i dati necessari:
   ```json
   "nome_utente": {
       "id": "base64_encoded_id",
       "hosts": {
           "MAC_ADDRESS": {
               "data": {
                   "AP-Ssid": "...",
                   "RP-Key": "...",
                   "Mac": "...",
                   "RegistKey": "...",
                   "Nickname": "...",
                   "IP": "..."
               },
               "type": "PS4"
           }
       }
   }
   ```

---

## 🎮 **Avvio e gestione di una sessione Remote Play**
📌 **Script da eseguire:** `session.py`

1. Eseguire il comando:
   ```sh
   python -m session.session
   ```
2. Selezionare l'account PSN che si desidera utilizzare per la sessione.
3. Selezionare la console a cui connettersi.
4. Il sistema eseguirà una verifica preliminare della connessione e avviserà in caso di problemi.
5. Attendere che la sessione venga avviata correttamente.
6. La sessione catturerà i frame video e li salverà automaticamente nella cartella `frames/{user_name}`.
7. Per terminare la sessione, premere **CTRL+C** o chiudere la finestra del terminale.

---

## 🚀 **Funzionalità avanzate**

### 🔄 **Riconnessione automatica**
Il sistema è ora in grado di rilevare quando la connessione cade e tentare automaticamente di riconnettersi. Questo aumenta significativamente la stabilità delle sessioni Remote Play, specialmente in caso di connessioni di rete instabili.

### 📊 **Monitoraggio della connessione**
Un nuovo modulo di monitoraggio verifica costantemente:
- La raggiungibilità della console (ping)
- La disponibilità dei servizi Remote Play
- La qualità della connessione

In caso di problemi, il sistema visualizza avvisi e intraprende azioni correttive.

### 🎛️ **Adattamento dinamico della qualità**
Il sistema monitora le prestazioni e la stabilità della connessione, adattando automaticamente:
- La risoluzione del video
- La frequenza dei fotogrammi (fps)
- La qualità dello stream

Questo garantisce la migliore esperienza possibile anche in condizioni di rete non ottimali.

### 📈 **Ottimizzazioni socket**
Sono state implementate avanzate ottimizzazioni dei socket di rete che migliorano la stabilità della connessione:
- Buffer di ricezione/invio ampliati
- Disattivazione dell'algoritmo Nagle per ridurre la latenza
- Configurazioni keepalive aggressive per mantenere attiva la connessione
- Gestione ottimizzata dei timeout

### 📁 **Gestione migliorata dei frame**
L'acquisizione e il salvataggio dei frame è stata completamente rivista:
- Elaborazione asincrona dei frame per evitare blocchi
- Controllo adattivo della velocità di acquisizione
- Migliore gestione delle risorse di sistema
- Statistiche dettagliate di acquisizione

### 📝 **Logging avanzato**
È stato implementato un sistema di logging completo che registra:
- Stato della connessione
- Prestazioni di acquisizione frame
- Errori e problemi rilevati
- Tentativi di riconnessione

I log vengono salvati nel file `remote_play_session.log` per facilitare il debug.

---

## 📂 **Struttura del Codice**
Il progetto è suddiviso in più moduli per migliorare la manutenibilità.

```
📂 PS-SOFTWARE/script-TESTED
│── requirements.txt       # Dipendenze richieste
│── readme.md              # Documentazione del progetto
│── remote_play_session.log # Log delle sessioni Remote Play
│── 📂 account_management   # Gestione degli account PSN
│   │── __init__.py        # Inizializza il modulo
│   │── connecting_account_to_console.py  # Collega un account PSN a una console
│   │── link_account.py     # Registra un account PSN nel sistema
│   │── utils.py            # Funzioni di utilità per la gestione degli account
│
│── 📂 session              # Gestione delle sessioni di gioco
│   │── session.py          # Avvio della sessione e selezione di account e console
│   │── 📂 frames           # Contiene i frame acquisiti dalle sessioni
│   │── 📂 remote_play      # Moduli per la gestione delle sessioni Remote Play
│       │── __init__.py      # Inizializza il modulo
│       │── controller.py    # Controlla il gamepad della sessione
│       │── session_manager.py  # Gestione avanzata della sessione Remote Play
│       │── frame_handler.py  # Cattura e salvataggio ottimizzati dei frame
│       │── network_monitor.py # Monitoraggio della connessione di rete
│       │── utils.py         # Funzioni di utilità (es. pulizia cartelle)
```

---

## 📌 **Moduli del Progetto**
### 🔹 `session.py`
- **Descrizione:** Script principale per avviare la sessione Remote Play.
- **Cosa fa:**  
  1. Mostra gli account registrati.  
  2. Permette di selezionare la console.  
  3. Verifica preliminarmente la connessione.
  4. Avvia la sessione ottimizzata e inizia la cattura dei frame.  
  5. Gestisce la chiusura sicura della sessione.  

### 🔹 `remote_play/session_manager.py`
- **Descrizione:** Gestisce la connessione alla sessione Remote Play con funzionalità avanzate.
- **Cosa fa:**  
  - Crea e gestisce la connessione con la console.  
  - Implementa la riconnessione automatica.
  - Monitora lo stato della connessione.
  - Adatta dinamicamente la qualità.
  - Gestisce il ciclo di vita completo della sessione.

### 🔹 `remote_play/frame_handler.py`
- **Descrizione:** Gestisce la cattura e il salvataggio ottimizzati dei frame.
- **Cosa fa:**  
  - Riceve i frame video dal QueueReceiver.
  - Elabora i frame in modo asincrono per evitare blocchi.
  - Adatta la velocità di acquisizione in base al carico.
  - Ottimizza la qualità del salvataggio.
  - Mantiene statistiche dettagliate.

### 🔹 `remote_play/network_monitor.py`
- **Descrizione:** Monitora in modo avanzato la connessione di rete.
- **Cosa fa:**  
  - Verifica la raggiungibilità della console.
  - Calcola statistiche di ping e perdita di pacchetti.
  - Fornisce informazioni sulla stabilità della connessione.
  - Offre sia versioni sincrone che asincrone delle funzionalità.

### 🔹 `remote_play/controller.py`
- **Descrizione:** Controlla il gamepad della sessione.
- **Cosa fa:**  
  - Inizializza il controller.  
  - Invia comandi alla console.  

### 🔹 `remote_play/utils.py`
- **Descrizione:** Funzioni di utilità.
- **Cosa fa:**  
  - Cancella i frame vecchi prima di una nuova sessione.  
  - Gestisce la pulizia delle cartelle.  

---

## 🛠 **Risoluzione dei Problemi**
### 🔹 **Errore: Nessun frame video ricevuto**
- **Soluzione:** Il sistema ora tenta automaticamente di passare da h264 a HEVC. Se il problema persiste, verificare che i codec siano installati correttamente.

### 🔹 **Errore di autenticazione PSN**
- **Soluzione:** Cambiare l'indirizzo MAC della scheda di rete e riprovare.

### 🔹 **Errore: "Sessione non attiva"**
- **Soluzione:** Il sistema ora esegue una verifica preliminare della connessione. Se il problema persiste, controllare che la console sia accesa e connessa alla stessa rete.

### 🔹 **Errore: "No Status" durante il collegamento della console**
- **Soluzione:** Verificare che:
  - La console sia accesa e non in modalità standby
  - L'IP inserito sia corretto e raggiungibile (provare a fare un ping)
  - Il Remote Play sia abilitato nelle impostazioni della console
  - Non ci siano firewall che bloccano la comunicazione

### 🔹 **Disconnessioni frequenti**
- **Soluzione:** Il nuovo sistema implementa la riconnessione automatica e l'adattamento della qualità. Se i problemi persistono:
  1. Controllare la stabilità della connessione di rete
  2. Ridurre manualmente la risoluzione a 540p nel file `session_manager.py`
  3. Verificare che non ci siano altri dispositivi che saturano la rete

### 🔹 **Prestazioni scadenti o frame persi**
- **Soluzione:** Il sistema ora monitora le prestazioni e adatta automaticamente la qualità. Se i problemi persistono:
  1. Verificare le risorse disponibili sul PC
  2. Chiudere applicazioni che consumano banda di rete
  3. Collegare la console PlayStation via cavo Ethernet anziché Wi-Fi

---

🚀 **Il software è ora ancora più stabile, resiliente e facile da usare!** 🎮🔥