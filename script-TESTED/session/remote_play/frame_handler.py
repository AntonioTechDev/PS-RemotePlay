import asyncio
import os
import cv2
import numpy as np
from datetime import datetime
import logging
import socket
import threading
import platform
from collections import deque
import time
from ai_model.fifa.game_state import FIFAStateDetector
from ai_model.fifa.data_collector import FIFADataCollector

# Configurazione logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("FrameHandler")

# Costanti
FRAME_DIR = "frames"
MAX_BUFFER_SIZE = 30      # Numero massimo di frame nel buffer
FRAME_INTERVAL = 0.05     # ~20fps (ridotto per migliorare la stabilità)
SOCKET_TIMEOUT = 10.0     # Timeout aumentato per maggiore stabilità
QUALITY_CHECK_INTERVAL = 5.0  # Intervallo per il controllo della qualità
MAX_PROCESSING_TASKS = 4  # Limita il numero di task di elaborazione paralleli

class EnhancedFrameHandler:
    """Gestore avanzato per la cattura e il salvataggio dei frame video."""
    
    def __init__(self, max_buffer_size=MAX_BUFFER_SIZE, collect_training=False):
        """Inizializza il gestore dei frame con un buffer ottimizzato."""
        self.frame_buffer = deque(maxlen=max_buffer_size)
        self.is_running = False
        self.lock = threading.Lock()
        self.last_frame_time = 0
        self.corrupt_frame_count = 0
        self.stats = {
            "frames_received": 0,
            "frames_saved": 0,
            "frames_dropped": 0,
            "errors": 0,
            "corrupt_frames": 0,
            "last_reset": time.time()
        }
        self.quality_adjusted = False
        self.processing_semaphore = asyncio.Semaphore(MAX_PROCESSING_TASKS)
        
        # Nuova strategia di buffer adattiva
        self.buffer_strategy = "normal"  # può essere "normal", "aggressive", "conservative"
        
        # Add FIFA-specific components for training
        self.collect_training = collect_training
        if collect_training:
            self.state_detector = FIFAStateDetector()
            self.data_collector = FIFADataCollector()
    
    def _enhanced_socket_optimization(self, sock):
        """Applica ottimizzazioni avanzate al socket per massimizzare la stabilità."""
        if sock:
            try:
                # Aumenta significativamente il buffer di ricezione
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 8 * 1024 * 1024)  # 8MB buffer
                
                # Aumenta il buffer di invio
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024 * 1024)
                
                # Disattiva Nagle algorithm per ridurre la latenza
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                
                # Timeout più lungo per tollerare interruzioni temporanee
                sock.settimeout(SOCKET_TIMEOUT)
                
                # Configurazione keepalive aggressiva
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                
                # Impostazioni keepalive più aggressive su sistemi Linux
                if hasattr(socket, 'TCP_KEEPIDLE'):
                    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 30)  # Tempo prima del primo probe
                if hasattr(socket, 'TCP_KEEPINTVL'):
                    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 5)  # Intervallo tra probe
                if hasattr(socket, 'TCP_KEEPCNT'):
                    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 10)  # Numero di probe prima della disconnessione
                
                # Imposta priorità alta per i pacchetti (su sistemi che lo supportano)
                if hasattr(socket, 'SO_PRIORITY') and platform.system() == 'Linux':
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_PRIORITY, 6)  # Alta priorità
                
                # Su Windows, impostazioni specifiche per keepalive
                if platform.system() == 'win32':
                    if hasattr(socket, 'SIO_KEEPALIVE_VALS'):
                        # (onoff, keepalivetime, keepaliveinterval)
                        sock.ioctl(socket.SIO_KEEPALIVE_VALS, (1, 30000, 5000))
                
                logger.info("🔧 Ottimizzazioni socket avanzate applicate con successo")
                return True
            except Exception as e:
                logger.error(f"❌ Errore durante l'ottimizzazione del socket: {e}")
            
        return False
    
    async def handle_corrupted_frames(self, device):
        """Gestisce più efficacemente i frame corrotti."""
        corrupt_frames_count = 0
        corrupt_frames_threshold = 10
        
        # Aggiungi un listener per gli eventi di frame corrotti
        if device.session and device.session.events:
            def on_corrupt_frame():
                nonlocal corrupt_frames_count
                corrupt_frames_count += 1
                with self.lock:
                    self.stats["corrupt_frames"] += 1
                    
                logger.warning(f"⚠️ Frame corrotto rilevato ({corrupt_frames_count}/{corrupt_frames_threshold})")
                
                # Se ci sono troppi frame corrotti consecutivi, riduci la qualità
                if corrupt_frames_count >= corrupt_frames_threshold:
                    logger.warning("⚠️ Troppi frame corrotti, riduco la qualità dello stream")
                    self.quality_adjusted = True
                    corrupt_frames_count = 0
            
            device.session.events.on("corrupt_frame", on_corrupt_frame)
    
    def prepare_session(self, device):
        """Prepara la sessione ottimizzando il socket se disponibile."""
        if device and device.session:
            # Accediamo al socket interno della sessione se disponibile
            session = device.session
            if hasattr(session, '_sock') and session._sock:
                logger.info("🔌 Socket nativo trovato, applico ottimizzazioni avanzate...")
                self._enhanced_socket_optimization(session._sock)
            else:
                logger.warning("⚠️ Socket nativo non disponibile")
            
            # Patch per la gestione degli errori di datagram
            self._apply_datagram_error_patch()
            
            # Aumentiamo la dimensione della coda del receiver se possibile
            if session.receiver and hasattr(session.receiver, 'queue_size'):
                logger.info(f"📊 Impostazione dimensione coda del receiver a {MAX_BUFFER_SIZE}")
                session.receiver.queue_size = MAX_BUFFER_SIZE
                
            # Avvia gestore frame corrotti
            asyncio.create_task(self.handle_corrupted_frames(device))
                
            return True
        return False
    
    def _apply_datagram_error_patch(self):
        """Applica patch per errori datagram fatali."""
        try:
            import asyncio.proactor_events
            
            # Questo è un monkey patch per gestire l'errore AssertionError in proactor_events.py
            original_loop_writing = asyncio.proactor_events._ProactorBaseWritePipeTransport._loop_writing
            
            def patched_loop_writing(self, f):
                try:
                    return original_loop_writing(self, f)
                except AssertionError:
                    logger.warning("⚠️ Intercettato errore di scrittura sul socket, tentativo di recupero...")
                    if hasattr(self, '_force_close'):
                        self._force_close(None)
            
            # Applica il patch solo se non è già stato applicato
            if asyncio.proactor_events._ProactorBaseWritePipeTransport._loop_writing.__name__ != "patched_loop_writing":
                asyncio.proactor_events._ProactorBaseWritePipeTransport._loop_writing = patched_loop_writing
                logger.info("✅ Patch per errori datagram applicato")
                
        except (ImportError, AttributeError) as e:
            logger.warning(f"⚠️ Impossibile applicare patch datagram: {e}")
    
    async def process_frame(self, frame, frame_path, device=None):
        """Elabora e salva un singolo frame con controllo delle risorse."""
        async with self.processing_semaphore:  # Limita il numero di task di elaborazione paralleli
            try:
                # Conversione del frame in un'immagine
                img = frame.to_ndarray(format='rgb24')
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                
                # Generazione nome file con timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                filename = os.path.join(frame_path, f"frame_{timestamp}.jpg")
                
                # Salvataggio ottimizzato con compressione adattiva
                quality = 90  # Qualità JPEG di base
                
                # Riduci la qualità se ci sono problemi di prestazioni
                if self.stats.get("frames_dropped", 0) > 5 or self.stats.get("errors", 0) > 3:
                    quality = 80
                
                cv2.imwrite(filename, img, [cv2.IMWRITE_JPEG_QUALITY, quality])
                
                with self.lock:
                    self.stats["frames_saved"] += 1
                    
                logger.debug(f"📸 Frame salvato: {filename}")
                
                if self.collect_training and device and device.controller:
                    # Previously: record gameplay as (game_state, human_action)
                    # New: compute reward from game_state and sample next state,
                    # then store the transition for RL training
                    game_state = self.state_detector.detect_state(img)
                    human_action = {
                        "buttons": device.controller.last_button_state,
                        "sticks": device.controller.stick_state
                    }
                    reward = compute_reward(game_state)  # Define your reward function elsewhere
                    next_state = game_state  # (or the updated state from subsequent frame)
                    self.data_collector.record_rl_transition(game_state, human_action, reward, next_state)
                    
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
    
    def reset_stats(self):
        """Resetta le statistiche di acquisizione frame."""
        with self.lock:
            self.stats = {
                "frames_received": 0,
                "frames_saved": 0,
                "frames_dropped": 0,
                "errors": 0,
                "corrupt_frames": 0,
                "last_reset": time.time()
            }
    
    async def adaptive_frame_rate(self, processing_tasks):
        """Adatta l'intervallo di acquisizione frame in base al carico."""
        # Se ci sono troppi task di elaborazione, rallenta l'acquisizione
        current_interval = FRAME_INTERVAL
        
        if len(processing_tasks) > MAX_PROCESSING_TASKS * 0.8:
            return FRAME_INTERVAL * 1.5  # Rallenta se c'è sovraccarico
        elif self.stats.get("errors", 0) > 5:
            return FRAME_INTERVAL * 1.2  # Rallenta in caso di errori
        elif self.stats.get("frames_dropped", 0) > 10:
            return FRAME_INTERVAL * 1.1  # Rallenta in caso di frame persi
        else:
            return FRAME_INTERVAL  # Mantieni la velocità normale
    
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
        self.reset_stats()
        
        # Crea task separati per la gestione asincrona
        processing_tasks = set()
        last_stats_report = time.time()
        
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
                
                # Report periodico delle statistiche
                current_time = time.time()
                if current_time - last_stats_report > 10:
                    elapsed = current_time - self.stats.get("last_reset", current_time)
                    fps = self.stats.get("frames_saved", 0) / elapsed if elapsed > 0 else 0
                    logger.info(f"📊 Statistiche: Ricevuti={self.stats.get('frames_received', 0)}, "
                               f"Salvati={self.stats.get('frames_saved', 0)}, "
                               f"Persi={self.stats.get('frames_dropped', 0)}, "
                               f"Errori={self.stats.get('errors', 0)}, "
                               f"Corrotti={self.stats.get('corrupt_frames', 0)}, "
                               f"FPS={fps:.1f}")
                    last_stats_report = current_time
                
                # Verifica validità del frame
                if not self.is_valid_frame(frame):
                    with self.lock:
                        self.stats["frames_dropped"] += 1
                    logger.warning("⚠️ Frame non valido ricevuto, lo ignoriamo.")
                    await asyncio.sleep(0.1)
                    continue
                
                # Processa il frame in modo asincrono
                task = asyncio.create_task(self.process_frame(frame, frame_path, device))
                processing_tasks.add(task)
                task.add_done_callback(processing_tasks.discard)
                
                # Adatta la velocità di acquisizione in base al carico
                interval = await self.adaptive_frame_rate(processing_tasks)
                await asyncio.sleep(interval)
                
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
        logger.info("🛑 Cattura frame terminata.")
        logger.info(f"📊 Statistiche finali: {self.stats}")
    
    def stop(self):
        """Ferma in modo sicuro la cattura dei frame."""
        logger.info("🛑 Arresto del gestore dei frame...")
        self.is_running = False
        if self.collect_training:
            self.data_collector.save_session()

# Per mantenere la compatibilità con il codice esistente, aggiungiamo la funzione originale
# che ora utilizza internamente l'EnhancedFrameHandler
async def save_video_frames(device, user_name):
    """Funzione di compatibilità che usa la nuova implementazione."""
    handler = EnhancedFrameHandler()
    await handler.save_video_frames(device, user_name)