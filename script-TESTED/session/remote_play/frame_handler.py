import os
import asyncio
import cv2
import numpy as np
from datetime import datetime

FRAME_DIR = "frames"

async def save_video_frames(device, user_name):
    """ Recupera i frame video dal QueueReceiver e li salva come immagini. """
    frame_path = os.path.join(FRAME_DIR, user_name)
    os.makedirs(frame_path, exist_ok=True)

    print(f"📡 Inizio cattura frame per {user_name}... Loop attivo fino alla disconnessione.")

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

        frame = receiver.video_frames[-1]

        if frame.width == 0 or frame.height == 0 or frame.format is None:
            print("⚠️ Frame non valido ricevuto (zero dimensioni o formato assente), lo ignoriamo.")
            await asyncio.sleep(0.5)
            continue

        print(f"🔍 Frame ricevuto - Tipo: {type(frame)}, Dimensioni: {frame.width}x{frame.height}, Formato: {frame.format}")
        print(f"🖼️ Frame Data: {np.array(frame.to_ndarray(format='rgb24'))[:5, :5]}\n")

        try:
            img = frame.to_ndarray(format='rgb24')
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = os.path.join(frame_path, f"frame_{timestamp}.jpg")

            cv2.imwrite(filename, img)
            print(f"📸 Frame salvato: {filename}")
        except Exception as e:
            print(f"❌ Errore nella conversione/salvataggio del frame: {e}")

        await asyncio.sleep(0.5)
