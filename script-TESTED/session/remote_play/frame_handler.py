import asyncio
import os
import cv2
import numpy as np
from datetime import datetime
from remote_play.utils import clean_frame_directory

FRAME_DIR = "frames"

async def save_video_frames(device, user_name):
    """ Recupera i frame video dal QueueReceiver e li salva come immagini. """
    frame_path = os.path.join(FRAME_DIR, user_name)
    os.makedirs(frame_path, exist_ok=True)

    print(f"📡 Inizio cattura frame per {user_name}... Loop attivo fino alla disconnessione.")
    
    while True:
        try:
            # Verifica se la sessione è ancora attiva
            if not device.session or not device.session.is_ready:
                print("🛑 Sessione non più attiva o pronta. Uscita dal loop di cattura.")
                break
                
            print("🧹 Pulizia della directory dei frame...")
            clean_frame_directory(user_name)
            print("🧹 Pulizia riuscita")
            
            print("ATTENDO 1S")
            await asyncio.sleep(1)
            
            # Controllo che il device e la sessione siano ancora validi
            if not device or not device.session:
                print("❌ Errore: Device o sessione non disponibile. Uscita dal loop.")
                break
                
            receiver = device.session.receiver

            await asyncio.sleep(1)
            print("ATTENDO 1S")
            
            # Verifica che il receiver sia valido
            if not receiver:
                print("❌ Errore: Receiver non disponibile. Attendo...")
                await asyncio.sleep(0.5)
                continue
                
            if not hasattr(receiver, "video_frames"):
                print("❌ Errore: Receiver non ha l'attributo `video_frames`. Attendo...")
                await asyncio.sleep(0.5)
                continue  

            # Verifica se video_frames è None e gestisci il caso
            if receiver.video_frames is None:
                print("⚠️ Warning: receiver.video_frames è None. Attendo...")
                await asyncio.sleep(0.5)
                continue

            # Verifica se ci sono frame disponibili
            if not receiver.video_frames:  # Lista vuota
                print("⚠️ Warning: Nessun frame disponibile. Attendo...")
                await asyncio.sleep(0.5)
                continue
                
            # Accedi all'ultimo frame in modo sicuro
            try:
                frame = receiver.video_frames[-1]
            except (IndexError, TypeError, AttributeError) as e:
                print(f"⚠️ Errore nell'accesso ai frame: {e}. Attendo...")
                await asyncio.sleep(0.5)
                continue

            # Verifica che il frame sia valido
            if frame is None or frame.width == 0 or frame.height == 0 or frame.format is None:
                print("⚠️ Frame non valido ricevuto, lo ignoriamo.")
                await asyncio.sleep(0.5)
                continue

            print(f"🔍 Frame ricevuto - Tipo: {type(frame)}, Dimensioni: {frame.width}x{frame.height}, Formato: {frame.format}")
            
            try:
                img = frame.to_ndarray(format='rgb24')
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                filename = os.path.join(frame_path, f"frame_{timestamp}.jpg")

                cv2.imwrite(filename, img)
                print(f"📸 Frame salvato: {filename}")

            except Exception as e:
                print(f"❌ Errore nella conversione/salvataggio del frame: {e}")

        except AssertionError:
            print("⚠️ Errore asyncio: tentativo di scrivere su un trasporto chiuso. Ignoro il frame e continuo...")
            await asyncio.sleep(0.5)
            continue
        except (AttributeError, TypeError) as e:
            print(f"⚠️ Errore di attributo/tipo: {e}. La sessione potrebbe essere instabile.")
            await asyncio.sleep(1)  # Attesa più lunga per dare tempo alla sessione di stabilizzarsi
            
            # Verifica se la sessione è ancora attiva
            if not device.session or not device.session.is_ready:
                print("🛑 Sessione non più disponibile dopo errore. Uscita dal loop.")
                break
                
        except Exception as e:
            print(f"❌ Errore imprevisto durante la cattura frame: {e}")
            await asyncio.sleep(0.5)

        await asyncio.sleep(0.5)

    print("🛑 Cattura frame terminata: il receiver non è più disponibile.")