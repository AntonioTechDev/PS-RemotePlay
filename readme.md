# 🎮 PS Remote Play - Guida Completa

Questa guida fornisce istruzioni dettagliate per l'utilizzo degli script per collegare e gestire account PSN con Remote Play utilizzando la libreria `pyremoteplay`.

---

## 📜 **Indice**
1. [Prerequisiti](#prerequisiti)
2. [Registrazione di un account PSN](#registrazione-di-un-account-psn)
3. [Collegamento di un account a una console](#collegamento-di-un-account-a-una-console)
4. [Avvio e gestione di una sessione Remote Play](#avvio-e-gestione-di-una-sessione-remote-play)
5. [Struttura del codice](#struttura-del-codice)
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
6. La sessione catturerà i frame video e li salverà automaticamente.
7. Per terminare la sessione, premere **CTRL+C** o chiudere la finestra del terminale.

---

## 📂 **Struttura del Codice**
Il progetto è ora suddiviso in più moduli per migliorare la manutenibilità.

```
/session
│── session.py             # Avvio della sessione e selezione di account e console
│── requirements.txt       # Dipendenze richieste
│── readme.md              # Documentazione del progetto
│── /remote_play           # Moduli organizzati per funzionalità
│   │── __init__.py        # Inizializza il modulo
│   │── controller.py       # Funzioni per il controller PS
│   │── session_manager.py  # Connessione e gestione della sessione Remote Play
│   │── frame_handler.py    # Cattura e salvataggio dei frame
│   │── utils.py            # Funzioni di utilità (es. pulizia cartelle)
```

---

## 📌 **Moduli del Progetto**
### 🔹 `session.py`
- **Descrizione:** Script principale per avviare la sessione Remote Play.
- **Cosa fa:**  
  1. Mostra gli account registrati.  
  2. Permette di selezionare la console.  
  3. Avvia la sessione e inizia la cattura dei frame.  
  4. Gestisce la chiusura della sessione.  

### 🔹 `remote_play/session_manager.py`
- **Descrizione:** Gestisce la connessione alla sessione Remote Play.
- **Cosa fa:**  
  - Crea una connessione con la console.  
  - Configura il ricevitore video.  
  - Gestisce la chiusura sicura della sessione.  

### 🔹 `remote_play/controller.py`
- **Descrizione:** Controlla il gamepad della sessione.
- **Cosa fa:**  
  - Inizializza il controller.  
  - Invia comandi test alla console.  

### 🔹 `remote_play/frame_handler.py`
- **Descrizione:** Gestisce la cattura e il salvataggio dei frame.
- **Cosa fa:**  
  - Riceve i frame video.  
  - Li converte in immagini.  
  - Li salva nella cartella `frames/{user_name}`.  

### 🔹 `remote_play/utils.py`
- **Descrizione:** Funzioni di utilità.
- **Cosa fa:**  
  - Cancella i frame vecchi prima di una nuova sessione.  
  - Gestisce la pulizia delle cartelle.  

---

## 🛠 **Risoluzione dei Problemi**
### 🔹 **Errore: Nessun frame video ricevuto**
- **Soluzione:** Assicurarsi che il codec `h264` sia supportato. Se non lo è, il sistema proverà a usare `HEVC`.

### 🔹 **Errore di autenticazione PSN**
- **Soluzione:** Cambiare l'indirizzo MAC della scheda di rete e riprovare.

### 🔹 **Errore: "Sessione non attiva"**
- **Soluzione:** Controllare che la console sia accesa e connessa alla stessa rete.

---

## ✅ **Workflow Completo**
1. **Registrare l'account PSN** con `link_account.py`.
2. **Collegare l'account alla console** con `connecting_account_to_console.py`.
3. **Avviare la sessione Remote Play** con `session.py`.
4. **Il sistema catturerà automaticamente i frame**.
5. **Terminare la sessione in sicurezza**.

🚀 **Ora il codice è ben strutturato, documentato e pronto all'uso!** 🎮🔥
