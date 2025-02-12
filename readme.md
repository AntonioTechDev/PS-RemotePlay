# 📌 Guida all'Utilizzo degli Script

Questo file fornisce le istruzioni per l'uso degli script **`link_account.py`** e **`connecting_account_to_console.py`** per registrare e connettere un account PSN a una console tramite **pyremoteplay**.

---

## 📌 Requisiti

- **Python 3.8+** installato
- **Libreria pyremoteplay** (installabile con `pip install pyremoteplay`)
- **Accesso a un account PSN valido**
- **Console PlayStation con Remote Play attivato**

---

## 🔗 1. Registrazione di un Account PSN (`link_account.py`)

Lo script `link_account.py` permette di registrare un account PSN e salvarlo nel file `.profile.json`.

### **📌 Passaggi per la registrazione**
1. **Esegui lo script**
   ```sh
   python link_account.py
   ```
2. **Apri il link generato** nel tuo browser e fai il login con il tuo account PSN.
3. Dopo il login, **copia l'URL di redirect** dalla barra degli indirizzi e incollalo nella finestra del terminale.
4. Lo script registrerà il tuo account e lo salverà in `.profile.json`.

### **⚠️ Risoluzione Problemi**
- **Errore 400 durante il login PSN** → Il server potrebbe aver bloccato il MAC Address del PC. Cambia il **MAC Address** della tua scheda di rete con il software **Technitium MAC Address Changer V6** e ricarica la pagina.
- **Il nuovo account sovrascrive il precedente** → Ora il sistema permette di salvare più account senza perdere i dati.

---

## 🎮 2. Connessione di un Account alla Console (`connecting_account_to_console.py`)

Lo script `connecting_account_to_console.py` consente di connettere un account PSN registrato a una console PlayStation tramite Remote Play.

### **📌 Passaggi per la connessione**
1. **Assicurati che la console sia accesa e che l'account PSN sia l'unico attivo sulla console.**
2. **Esegui lo script**
   ```sh
   python connecting_account_to_console.py
   ```
3. **Seleziona l'account da connettere** (tra quelli registrati in `.profile.json`).
4. **Inserisci l'IP della console** (visibile in Sistema > Informazioni sistema > ip adress).
5. **Inserisci il PIN della console** (presente in "Impostazioni > Connessione Riproduzione Remota").
6. La connessione verrà stabilita e l'account sarà collegato alla console.

### **⚠️ Risoluzione Problemi**
- **Errore durante la connessione** → Verifica che sulla console sia attivo **solo l'account che vuoi connettere** e che sia **l'account principale**.
- **IP errato o console non trovata** → Controlla che l'IP inserito sia corretto e che la console sia accesa.

---

## ✅ Conclusione
Ora sei pronto a registrare e connettere più account PSN alla tua console senza problemi! Se riscontri ulteriori difficoltà, verifica i passaggi e assicurati che il tuo PC e la tua console siano nella stessa rete. 🎮🔥

🚀 **Buon divertimento con Remote Play!**

