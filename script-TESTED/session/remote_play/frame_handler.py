import asyncio
import os
import cv2
import numpy as np
from datetime import datetime
import logging
import socket
import threading
from collections import deque

# Configurazione logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("FrameHandler")

# Costanti
FRAME_DIR = "frames"
MAX_BUFFER_SIZE = 30  # Numero massimo di frame nel buffer
FRAME_INTERVAL = 0.033  # ~30fps (1/30 ≈ 0.033)
SOCKET_TIMEOUT = 5.0  # 5 secondi di timeout per operazioni socket

class EnhancedFrameHandler:
    """Gestore avanzato per la cattura e il salvataggio dei frame video."""
    
    def __init__(self, max_buffer_size=MAX_BUFFER_SIZE):
        """Inizializza il gestore dei frame con un buffer ottimizzato."""
        self.frame_buffer = deque(maxlen=max_buffer_size)
        self.is_running = False
        self.lock = threading.Lock()
        self.last_frame_time = 0
        self.stats = {
            "frames_received": 0,
            "frames_saved": 0,
            "frames_dropped": 0,
            "errors": 0
        }
    
    def _optimize_socket(self, sock):
        """Applica ottimizzazioni al socket per migliorare la stabilità e le prestazioni."""
        if sock:
            try:
                # Aumenta il buffer di ricezione
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024 * 1024)
                
                # Disattiva il Nagle algorithm per ridurre la latenza
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                
                # Imposta il timeout per evitare blocchi indefiniti
                sock.settimeout(SOCKET_TIMEOUT)
                
                # Mantieni la connessione attiva con keepalive
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                
                # Su Linux, possiamo configurare ulteriormente il keepalive
                # Questi controlli rendono il codice compatibile con Windows
                if hasattr(socket, 'TCP_KEEPIDLE'):
                    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 60)
                if hasattr(socket, 'TCP_KEEPINTVL'):
                    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 10)
                if hasattr(socket, 'TCP_KEEPCNT'):
                    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 5)
                
                logger.info("🔧 Ottimizzazioni socket applicate con successo")
                return True
            except Exception as e:
                logger.error(f"❌ Errore durante l'ottimizzazione del socket: {e}")
                return False
        return False
    
    def prepare_session(self, device):
        """Prepara la sessione ottimizzando il socket se disponibile."""
        if device and device.session:
            # Accediamo al socket interno della sessione se disponibile
            session = device.session
            if hasattr(session, '_sock') and session._sock:
                logger.info("🔌 Socket nativo trovato, applico ottimizzazioni...")
                self._optimize_socket(session._sock)
            else:
                logger.warning("⚠️ Socket nativo non disponibile")
            
            # Aumentiamo la dimensione della coda del receiver se possibile
            if session.receiver and hasattr(session.receiver, 'queue_size'):
                logger.info(f"📊 Impostazione dimensione coda del receiver a {MAX_BUFFER_SIZE}")
                session.receiver.queue_size = MAX_BUFFER_SIZE
                
            return True
        return False
    
    async def process_frame(self, frame, frame_path):
        """Elabora e salva un singolo frame."""
        try:
            # Conversione del frame in un'immagine
            img = frame.to_ndarray(format='rgb24')
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            
            # Generazione nome file con timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = os.path.join(frame_path, f"frame_{timestamp}.jpg")
            
            # Salvataggio ottimizzato
            cv2.imwrite(filename, img, [cv2.IMWRITE_JPEG_QUALITY, 90])
            
            with self.lock:
                self.stats["frames_saved"] += 1
                
            logger.debug(f"📸 Frame salvato: {filename}")
            return True
        except Exception as e:
            with self.lock:
                self.stats["errors"] += 1
            logger.error(f"❌ Errore nella conversione/salvataggio del frame: {e}")
            return False
    
    def is_valid_frame(self, frame):
        """Verifica che il frame sia valido per l'elaborazione."""
        return (frame is not None and 
                hasattr(frame, 'width') and frame.width > 0 and 
                hasattr(frame, 'height') and frame.height > 0 and 
                hasattr(frame, 'format') and frame.format is not None)
    
    async def save_video_frames(self, device, user_name):
        """Recupera i frame video dal QueueReceiver e li salva come immagini con gestione ottimizzata."""
        # Crea la directory per i frame se non esiste
        frame_path = os.path.join(FRAME_DIR, user_name)
        os.makedirs(frame_path, exist_ok=True)
        
        # Prepara la sessione
        if not self.prepare_session(device):
            logger.error("❌ Impossibile preparare la sessione")
            return
        
        logger.info(f"📡 Inizio cattura frame per {user_name}... Loop attivo fino alla disconnessione.")
        self.is_running = True
        
        # Crea task separati per la gestione asincrona
        processing_tasks = set()
        
        while device.session and device.session.is_ready and self.is_running:
            try:
                receiver = device.session.receiver
                
                # Verifica disponibilità del receiver
                if not receiver or not hasattr(receiver, "video_frames"):
                    logger.warning("⚠️ Receiver non disponibile o non ha `video_frames`. Attendo...")
                    await asyncio.sleep(0.2)
                    continue
                
                # Verifica disponibilità dei frame
                if receiver.video_frames is None:
                    logger.warning("⚠️ receiver.video_frames è None. Disconnettendo...")
                    break
                
                if not receiver.video_frames:
                    await asyncio.sleep(0.1)  # Ridotto il tempo di attesa per essere più reattivi
                    continue
                
                # Preleva l'ultimo frame disponibile
                frame = receiver.video_frames[-1]
                
                # Aggiornamento delle statistiche
                with self.lock:
                    self.stats["frames_received"] += 1
                
                # Verifica validità del frame
                if not self.is_valid_frame(frame):
                    with self.lock:
                        self.stats["frames_dropped"] += 1
                    logger.warning("⚠️ Frame non valido ricevuto, lo ignoriamo.")
                    await asyncio.sleep(0.1)
                    continue
                
                # Processa il frame in modo asincrono
                task = asyncio.create_task(self.process_frame(frame, frame_path))
                processing_tasks.add(task)
                task.add_done_callback(processing_tasks.discard)
                
                # Limita la velocità di cattura per non sovraccaricare il sistema
                await asyncio.sleep(FRAME_INTERVAL)
                
            except AssertionError:
                logger.warning("⚠️ Errore asyncio: tentativo di scrivere su un trasporto chiuso.")
                continue
            except asyncio.CancelledError:
                logger.info("🛑 Task di cattura frame cancellato.")
                break
            except Exception as e:
                with self.lock:
                    self.stats["errors"] += 1
                logger.error(f"❌ Errore imprevisto durante la cattura frame: {e}")
                await asyncio.sleep(0.5)
        
        # Attendi il completamento di tutti i task di elaborazione
        if processing_tasks:
            logger.info(f"⏳ Attesa completamento di {len(processing_tasks)} task di elaborazione...")
            await asyncio.gather(*processing_tasks, return_exceptions=True)
        
        self.is_running = False
        logger.info("🛑 Cattura frame terminata: il receiver non è più disponibile.")
        logger.info(f"📊 Statistiche finali: {self.stats}")
    
    def stop(self):
        """Ferma in modo sicuro la cattura dei frame."""
        logger.info("🛑 Arresto del gestore dei frame...")
        self.is_running = False

# Per mantenere la compatibilità con il codice esistente, aggiungiamo la funzione originale
# che ora utilizza internamente l'EnhancedFrameHandler
async def save_video_frames(device, user_name):
    """Funzione di compatibilità che usa la nuova implementazione."""
    handler = EnhancedFrameHandler()
    await handler.save_video_frames(device, user_name)