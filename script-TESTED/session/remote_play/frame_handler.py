import asyncio
import os
import cv2
import numpy as np
from datetime import datetime
from remote_play.utils import clean_frame_directory
import traceback
import time

FRAME_DIR = "frames"

# Abilita logging dettagliato
DEBUG = True

def debug_log(message):
    """Funzione helper per log dettagliati."""
    if DEBUG:
        print(f"📽️ [DEBUG-FRAME]: {message}")

async def save_video_frames(device, user_name):
    """ Recupera i frame video dal QueueReceiver e li salva come immagini. """
    frame_path = os.path.join(FRAME_DIR, user_name)
    os.makedirs(frame_path, exist_ok=True)

    print(f"📡 Inizio cattura frame per {user_name}... Loop attivo fino alla disconnessione.")
    debug_log(f"Avvio cattura frame - device: {device}, session: {device.session if hasattr(device, 'session') else None}")
    
    # Frame counter e timestamp dell'ultimo frame
    frame_counter = 0
    last_frame_time = datetime.now()
    frame_timeout = 10  # secondi massimi senza ricevere frame prima di considerare disconnesso
    time_without_session = 0
    max_time_without_session = 30  # secondi massimi senza sessione prima di uscire
    
    # Tracciamento statistiche
    total_frames = 0
    error_count = 0
    start_time = datetime.now()
    
    # Salvataggio frame ogni N frame per ridurre I/O
    save_interval = 5  # Salva un frame ogni N frame
    save_counter = 0
    
    # Ultimo timestamp di pulizia directory
    last_cleanup_time = time.time()
    cleanup_interval = 30  # Pulisci la directory ogni 30 secondi, non ad ogni frame
    
    while True:
        try:
            # Statistiche periodiche
            if DEBUG and frame_counter % 10 == 0:
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed > 0:
                    fps = total_frames / elapsed
                    debug_log(f"Statistiche: {total_frames} frames, {error_count} errori, {fps:.2f} FPS medi")
            
            # Verifica dettagliata dello stato della sessione
            session_active = (hasattr(device, 'session') and 
                             device.session is not None and 
                             hasattr(device.session, 'is_ready') and 
                             device.session.is_ready)
            
            # Verifica se la sessione è ancora attiva
            if not session_active:
                time_without_session += 1
                if time_without_session % 5 == 0:  # Log ogni 5 secondi per non inondare il console
                    print(f"⚠️ Sessione non attiva ma continuo a cercare di catturare frame... ({time_without_session}s)")
                
                # Dettagli dello stato
                debug_log(f"Stato sessione - device: {device}, session: {device.session if hasattr(device, 'session') else None}")
                
                # Se troppe iterazioni senza sessione attiva, usciamo
                if time_without_session >= max_time_without_session:
                    print(f"🛑 Troppo tempo senza sessione attiva ({time_without_session}s). Uscita dal loop di cattura.")
                    break
                
                await asyncio.sleep(1)
                continue
            else:
                # Resetta il contatore se la sessione è attiva
                time_without_session = 0
            
            # Pulizia della directory solo periodicamente invece che ad ogni frame
            current_time = time.time()
            if current_time - last_cleanup_time > cleanup_interval:
                debug_log(f"Esecuzione pulizia periodica della directory ({cleanup_interval}s trascorsi)")
                print("🧹 Pulizia della directory dei frame...")
                clean_frame_directory(user_name)
                print("🧹 Pulizia riuscita")
                last_cleanup_time = current_time
            
            print("ATTENDO 1S")
            await asyncio.sleep(1)
            
            # Verifica dettagliata del receiver
            receiver_valid = (hasattr(device, 'session') and 
                             device.session is not None and 
                             hasattr(device.session, 'receiver') and 
                             device.session.receiver is not None)
            
            if not receiver_valid:
                debug_log(f"Receiver non valido - sessione: {device.session}, receiver: {device.session.receiver if hasattr(device.session, 'receiver') else None}")
                print("❌ Errore: Receiver non disponibile. Attendo...")
                await asyncio.sleep(0.5)
                continue
            
            receiver = device.session.receiver
            
            # Dettaglio completo del receiver
            if DEBUG and frame_counter % 20 == 0:  # Ogni 20 frame per non inondare i log
                debug_log(f"Dettagli receiver: {receiver}, tipo: {type(receiver)}")
                debug_log(f"Attributi receiver: {dir(receiver) if receiver else 'None'}")
            
            await asyncio.sleep(1)
            print("ATTENDO 1S")
            
            # Verifica che il receiver abbia l'attributo video_frames
            if not hasattr(receiver, "video_frames"):
                debug_log(f"Receiver {receiver} non ha l'attributo video_frames!")
                print("❌ Errore: Receiver non ha l'attributo `video_frames`. Attendo...")
                await asyncio.sleep(0.5)
                continue  

            # Verifica se video_frames è None e gestisci il caso
            if receiver.video_frames is None:
                debug_log("receiver.video_frames è None")
                print("⚠️ Warning: receiver.video_frames è None. Attendo...")
                await asyncio.sleep(0.5)
                continue

            # Verifica se ci sono frame disponibili
            if not receiver.video_frames:  # Lista vuota
                debug_log("receiver.video_frames è una lista vuota")
                print("⚠️ Warning: Nessun frame disponibile. Attendo...")
                
                # Controlla da quanto tempo non riceviamo frame
                time_without_frame = (datetime.now() - last_frame_time).total_seconds()
                if time_without_frame > frame_timeout:
                    debug_log(f"Timeout ricezione frame: {time_without_frame}s > {frame_timeout}s")
                    print(f"⚠️ Nessun frame ricevuto per {time_without_frame:.1f} secondi. Possibile disconnessione.")
                
                await asyncio.sleep(0.5)
                continue
                
            # Accedi all'ultimo frame in modo sicuro
            try:
                debug_log(f"Tentativo accesso all'ultimo frame. Num frames: {len(receiver.video_frames)}")
                frame = receiver.video_frames[-1]
                debug_log(f"Frame ottenuto: {frame}, tipo: {type(frame)}")
            except (IndexError, TypeError, AttributeError) as e:
                error_count += 1
                debug_log(f"Errore accesso frame: {e}, {traceback.format_exc()}")
                print(f"⚠️ Errore nell'accesso ai frame: {e}. Attendo...")
                await asyncio.sleep(0.5)
                continue

            # Verifica che il frame sia valido
            if frame is None:
                debug_log("Frame è None")
                print("⚠️ Frame non valido ricevuto (None), lo ignoriamo.")
                await asyncio.sleep(0.5)
                continue
                
            # Controlli più dettagliati sul frame
            frame_valid = (hasattr(frame, 'width') and frame.width > 0 and
                          hasattr(frame, 'height') and frame.height > 0 and
                          hasattr(frame, 'format') and frame.format is not None)
                          
            if not frame_valid:
                debug_log(f"Frame non valido: width={frame.width if hasattr(frame, 'width') else 'N/A'}, " +
                         f"height={frame.height if hasattr(frame, 'height') else 'N/A'}, " +
                         f"format={frame.format if hasattr(frame, 'format') else 'N/A'}")
                print("⚠️ Frame non valido ricevuto, lo ignoriamo.")
                await asyncio.sleep(0.5)
                continue

            print(f"🔍 Frame ricevuto - Tipo: {type(frame)}, Dimensioni: {frame.width}x{frame.height}, Formato: {frame.format}")
            last_frame_time = datetime.now()  # Aggiorna il timestamp dell'ultimo frame
            frame_counter += 1
            total_frames += 1
            
            # Incrementa il contatore di salvataggio
            save_counter += 1
            
            # Salva solo ogni N frame per ridurre I/O
            if save_counter >= save_interval:
                try:
                    debug_log(f"Conversione e salvataggio frame #{frame_counter}")
                    img = frame.to_ndarray(format='rgb24')
                    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    filename = os.path.join(frame_path, f"frame_{timestamp}.jpg")

                    cv2.imwrite(filename, img)
                    print(f"📸 Frame salvato: {filename}")
                    
                    # Resetta il contatore
                    save_counter = 0

                except Exception as e:
                    error_count += 1
                    debug_log(f"Errore salvataggio: {e}, {traceback.format_exc()}")
                    print(f"❌ Errore nella conversione/salvataggio del frame: {e}")

        except AssertionError as e:
            error_count += 1
            debug_log(f"Errore asyncio: {e}, {traceback.format_exc()}")
            print("⚠️ Errore asyncio: tentativo di scrivere su un trasporto chiuso. Ignoro il frame e continuo...")
            await asyncio.sleep(0.5)
            continue
        except (AttributeError, TypeError) as e:
            error_count += 1
            debug_log(f"Errore attributo/tipo: {e}, {traceback.format_exc()}")
            print(f"⚠️ Errore di attributo/tipo: {e}. La sessione potrebbe essere instabile.")
            await asyncio.sleep(1)  # Attesa più lunga per dare tempo alla sessione di stabilizzarsi
            
            # Non uscire subito, consenti al session_manager di gestire la riconnessione
            time_without_frame = (datetime.now() - last_frame_time).total_seconds()
            if time_without_frame > frame_timeout:
                debug_log(f"Lungo periodo senza frame: {time_without_frame}s > {frame_timeout}s")
                print(f"⚠️ Nessun frame ricevuto per {time_without_frame:.1f} secondi. Possibile disconnessione.")
                
        except Exception as e:
            error_count += 1
            debug_log(f"Errore imprevisto: {e}, {traceback.format_exc()}")
            print(f"❌ Errore imprevisto durante la cattura frame: {e}")
            await asyncio.sleep(0.5)

        await asyncio.sleep(0.5)

    debug_log(f"Uscita dal loop di cattura. Frames totali: {total_frames}, errori: {error_count}")
    print("🛑 Cattura frame terminata: il receiver non è più disponibile.")