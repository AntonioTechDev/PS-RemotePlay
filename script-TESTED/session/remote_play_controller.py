import os
import shutil
import asyncio
import cv2
import numpy as np
from datetime import datetime
from pyremoteplay import RPDevice
from pyremoteplay.profile import Profiles
from pyremoteplay.receiver import QueueReceiver
import av

# Imposta il percorso predefinito per il file dei profili
Profiles.set_default_path(r"C:\Users\ADB\.pyremoteplay\.profile.json")

# Carica i profili salvati
profiles = Profiles.load()

# Cartella di salvataggio dei frame
FRAME_DIR = "frames"

async def save_video_frames(device, user_name):
    """ Recupera solo i frame video dal QueueReceiver e li salva come immagini. """
    frame_path = os.path.join(FRAME_DIR, user_name)
    os.makedirs(frame_path, exist_ok=True)

    print(f"📡 Inizio cattura frame per {user_name}... Loop infinito attivo.")

    while device.session and device.session.is_ready:
        receiver = device.session.receiver

        if not receiver or not hasattr(receiver, "video_frames"):
            print("❌ Errore: Receiver non disponibile o non ha `video_frames`.")
            await asyncio.sleep(0.5)
            continue

        if not receiver.video_frames:
            print("⚠️ Nessun frame disponibile, in attesa...")
            await asyncio.sleep(0.5)
            continue

        frame = receiver.video_frames[-1]  # Ultimo frame disponibile

        if frame.width == 0 or frame.height == 0 or frame.format is None:
            print("⚠️ Frame non valido ricevuto (zero dimensioni o formato assente), lo ignoriamo.")
            await asyncio.sleep(0.5)
            continue

        print(f"🔍 Frame ricevuto - Tipo: {type(frame)}, Dimensioni: {frame.width}x{frame.height}, Formato: {frame.format}")
        print(f"🖼️ Frame Data: {np.array(frame.to_ndarray(format='rgb24'))[:5, :5]}\n")  # Stampa una parte del frame

        try:
            img = frame.to_ndarray(format='rgb24')  # Converte in array numpy
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)  # Converti a formato OpenCV

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = os.path.join(frame_path, f"frame_{timestamp}.jpg")

            cv2.imwrite(filename, img)  # Salva il frame
            print(f"📸 Frame salvato: {filename}")
        except Exception as e:
            print(f"❌ Errore nella conversione/salvataggio del frame: {e}")

        await asyncio.sleep(0.5)  # Aspetta 500ms per ridurre il carico CPU

def clean_frame_directory(user_name):
    """ Elimina i frame salvati della sessione precedente. """
    user_frame_path = os.path.join(FRAME_DIR, user_name)
    if os.path.exists(user_frame_path):
        shutil.rmtree(user_frame_path)
    os.makedirs(user_frame_path, exist_ok=True)
    return user_frame_path

def initialize_controller(device):
    """ Attiva il controller della sessione. """
    print("🎮 Inizializzazione del controller...")
    device.controller.start()
    print("✅ Controller attivato!")

async def send_test_commands(device):
    """ Esegue una sequenza di comandi di test. """
    commands = ["CROSS", "CIRCLE", "SQUARE", "TRIANGLE", "UP", "DOWN", "LEFT", "RIGHT", "OPTIONS"]
    
    for command in commands:
        device.controller.button(command, "tap")
        print(f"✅ Comando {command} inviato!")
        await asyncio.sleep(1)

# ✅ Funzione per disconnettere in sicurezza
async def safe_disconnect(device):
    """Gestisce la disconnessione sicura della sessione Remote Play."""
    if device.session:
        print("\n🔌 Tentativo di disconnessione in corso...")

        if device.connected:
            print("⏳ Arresto della sessione in corso...")
            device.session.stop()
            await asyncio.sleep(2)  # Attende per garantire la chiusura

        # Imposta la sessione a None per forzare la disconnessione
        device._session = None
        print("✅ Sessione disconnessa correttamente!")
    else:
        print("⚠️ Nessuna sessione attiva da disconnettere.")

async def connect_and_run_session(user_profile, selected_mac, ip_address):
    """ Connette l'utente alla sessione Remote Play e avvia la cattura dei frame. """
    device = RPDevice(ip_address)
    try:
        print("\n🔌 Verifica stato della console...")
        status = device.get_status()

        if not status:
            print("❌ Errore: impossibile ottenere lo stato della console.")
            return

        user_profile = profiles.get_user_profile(user_profile.name)
        if not user_profile:
            print(f"❌ Errore: L'utente {user_profile.name} non è registrato correttamente.")
            return

        print("\n🎮 Avvio della sessione Remote Play...")
        frame_path = clean_frame_directory(user_profile.name)  # Pulisce la cartella prima di avviare la sessione
        receiver = QueueReceiver()
        receiver.queue_size = 100  # 🔥 Aumentiamo il buffer per evitare pacchetti fuori ordine

        session = device.create_session(
            user=user_profile.name,
            profiles=profiles,
            receiver=receiver,
            resolution="720p",
            fps=30,
            quality="default",
            codec="h264",
            hdr=False
        )

        if not session:
            print("❌ Errore: impossibile creare la sessione Remote Play.")
            return

        success = await device.connect()
        if not success:
            print("❌ Errore: Connessione alla sessione Remote Play fallita.")
            return

        # 🔥 Controlliamo se riceviamo frame con h264, altrimenti passiamo a hevc
        await asyncio.sleep(3)  # Attendere un po' per ricevere i primi frame
        if not receiver.video_frames:
            print("⚠️ Nessun frame ricevuto con h264, provo con HEVC...")
            session.stop()
            session = device.create_session(
                user=user_profile.name,
                profiles=profiles,
                receiver=receiver,
                resolution="720p",
                fps=30,
                quality="default",
                codec="hevc",
                hdr=False
            )
            success = await device.connect()
            if not success:
                print("❌ Errore: Connessione alla sessione con HEVC fallita.")
                return

        print(f"✅ Sessione avviata con successo per {user_profile.name}!")

        # Avvia il salvataggio dei frame in background
        print(f"📡 Avvio del processo di salvataggio frame per {user_profile.name}...")
        task = asyncio.create_task(save_video_frames(device, user_profile.name))
        print(f"🟢 Task di salvataggio avviato? {task is not None}")

        initialize_controller(device)

        await asyncio.sleep(3)
        print(f"\n🔍 Stato della sessione prima di inviare comandi: {device.session}")
        await send_test_commands(device)

    except Exception as e:
        print(f"❌ Errore durante la sessione: {e}")

    finally:
        print("\n🔌 Disconnessione della sessione...")
        await safe_disconnect(device)
