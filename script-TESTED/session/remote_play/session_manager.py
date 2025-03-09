import asyncio
import logging
from pyremoteplay import RPDevice
from pyremoteplay.profile import Profiles
from pyremoteplay.receiver import QueueReceiver
from remote_play.utils import clean_frame_directory
from remote_play.controller import initialize_controller, send_test_commands
from remote_play.frame_handler import EnhancedFrameHandler
import sys
import socket
import time

# Configurazione logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SessionManager")

# Configurazione percorso profili
PROFILE_PATH = r"C:\Users\ADB\.pyremoteplay\.profile.json"
Profiles.set_default_path(PROFILE_PATH)
profiles = Profiles.load()

# Costanti per la connessione
CONNECTION_RETRIES = 5       # Aumentato il numero di tentativi
RETRY_DELAY = 3.0            # Aumentato il ritardo tra tentativi
CONNECTION_TIMEOUT = 15.0    # Aumentato il timeout
HEALTH_CHECK_INTERVAL = 3.0  # Intervallo di controllo della connessione
MAX_CONNECTION_ISSUES = 3    # Numero massimo di problemi prima di riconnettere

# This file defines EnhancedSessionManager which:
# - Establishes and manages a Remote Play session.
# - Implements connection retries, health checking, and quality control.
# - Performs adaptive reconnection if connection issues are detected.
# - Manages background tasks such as frame capture and adaptive quality.

class EnhancedSessionManager:
    """Gestore sessione Remote Play ottimizzato per una connessione più stabile."""
    
    def __init__(self):
        """Inizializza il gestore della sessione."""
        self.frame_handler = EnhancedFrameHandler(max_buffer_size=60)  # Buffer più grande per migliore fluidità
        self.device = None
        self.active_tasks = []
        self.user_profile = None
        self.ip_address = None
        self.current_resolution = "720p"
        self.current_fps = 30
        self.current_quality = "default"
        self.reconnection_in_progress = False
    
    async def safe_disconnect(self, device):
        """Gestisce la disconnessione sicura della sessione Remote Play con pulizia aggressiva delle risorse."""
        if device:
            logger.info("\n🔌 Disconnessione in corso...")

            # Ferma il frame handler prima di tutto
            if hasattr(self, 'frame_handler') and self.frame_handler:
                self.frame_handler.stop()
                logger.info("✅ Frame handler arrestato.")

            # Cancella i task attivi
            for task in self.active_tasks:
                if not task.done():
                    task.cancel()
                    try:
                        await asyncio.wait_for(task, timeout=1.0)
                    except (asyncio.CancelledError, asyncio.TimeoutError):
                        pass
            
            self.active_tasks.clear()
            logger.info("✅ Task attivi cancellati.")

            # Disconnetti il controller
            if hasattr(device, 'controller') and device.controller:
                device.controller.disconnect()
                logger.info("✅ Controller disconnesso.")

            if device.session:
                if device.connected:
                    try:
                        device.disconnect()
                        await asyncio.sleep(1)  # Breve attesa
                    except Exception as e:
                        logger.warning(f"⚠️ Errore durante la disconnessione: {e}")

                # Chiusura forzata di tutti i trasporti
                if hasattr(device, "transport") and device.transport:
                    try:
                        device.transport.close()
                    except Exception:
                        pass
                        
                # Chiudi esplicitamente i socket
                if hasattr(device.session, "_sock") and device.session._sock:
                    try:
                        device.session._sock.close()
                    except Exception:
                        pass
                        
                # Forza la chiusura del receiver
                if device.session.receiver:
                    try:
                        device.session.receiver.close()
                    except Exception:
                        pass

                device._session = None
                
            logger.info("✅ Disconnessione completata.")
        else:
            logger.warning("⚠️ Nessun dispositivo da disconnettere.")
    
    async def health_check_task(self, device, interval=HEALTH_CHECK_INTERVAL):
        """Task migliorato che monitora costantemente la salute della connessione."""
        logger.info("🔍 Avvio monitoraggio stato connessione...")
        
        connection_issues = 0
        max_issues = MAX_CONNECTION_ISSUES  # Numero massimo di problemi consecutivi prima di intervenire
        
        while device and device.session and device.session.is_ready and not self.reconnection_in_progress:
            try:
                # Verifica lo stato della connessione
                connection_ok = True
                
                # Verifica che il dispositivo sia ancora connesso
                if not device.connected:
                    logger.error("❌ Connessione persa!")
                    connection_ok = False
                    
                # Verifica che la console sia ancora raggiungibile sulla rete
                if hasattr(device, 'host') and connection_ok:
                    try:
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                            s.settimeout(1.0)
                            result = s.connect_ex((device.host, 9295))  # Porta standard RemotePlay
                            if result != 0:
                                logger.warning(f"⚠️ La console non risponde sulla porta RemotePlay (errore {result})")
                                connection_ok = False
                    except Exception as e:
                        logger.warning(f"⚠️ Errore durante il controllo di rete: {e}")
                        connection_ok = False
                
                # Verifica che il flusso video stia ancora arrivando
                if device.session and device.session.receiver and connection_ok:
                    if not device.session.receiver.video_frames:
                        logger.warning("⚠️ Nessun frame ricevuto")
                        connection_ok = False
                
                # Gestione dei problemi di connessione
                if not connection_ok:
                    connection_issues += 1
                    logger.warning(f"⚠️ Problema di connessione rilevato ({connection_issues}/{max_issues})")
                    
                    if connection_issues >= max_issues:
                        logger.error("❌ Troppi problemi di connessione consecutivi, avvio riconnessione...")
                        # Avvia il processo di riconnessione
                        if self.user_profile and self.ip_address:
                            asyncio.create_task(self.try_reconnect(self.user_profile, self.ip_address))
                        break
                else:
                    # Reset contatore problemi se tutto ok
                    if connection_issues > 0:
                        connection_issues = max(0, connection_issues - 1)  # Riduce gradualmente il contatore
                
            except Exception as e:
                logger.error(f"❌ Errore durante il monitoraggio della connessione: {e}")
            
            await asyncio.sleep(interval)
        
        logger.info("🔍 Monitoraggio connessione terminato")
    
    async def try_reconnect(self, user_profile, ip_address, max_attempts=5):
        """Tenta di ristabilire la connessione quando cade."""
        if self.reconnection_in_progress:
            logger.warning("⚠️ Riconnessione già in corso, ignoro la richiesta")
            return False
            
        self.reconnection_in_progress = True
        logger.info("🔄 Tentativo di riconnessione automatica...")
        
        for attempt in range(max_attempts):
            logger.info(f"🔄 Tentativo di riconnessione {attempt+1}/{max_attempts}")
            
            # Disconnetti prima qualsiasi sessione esistente
            if self.device and self.device.session:
                await self.safe_disconnect(self.device)
                await asyncio.sleep(3)  # Attendi che tutte le risorse siano rilasciate
            
            # Crea un nuovo dispositivo
            self.device = RPDevice(ip_address)
            
            try:
                # Verifica stato console
                status = await asyncio.wait_for(
                    self.device.async_get_status(), 
                    timeout=5.0
                )
                
                if not status:
                    logger.warning("⚠️ Console non raggiungibile, riprovo...")
                    await asyncio.sleep(5)
                    continue
                    
                # Impostazioni di connessione ottimizzate
                receiver = QueueReceiver()
                receiver.queue_size = 60
                
                # Usa una risoluzione adattiva in base ai tentativi
                adaptive_resolution = self.current_resolution
                if attempt > 1:
                    adaptive_resolution = "540p"  # Abbassa la risoluzione dopo il primo tentativo
                
                session = self.device.create_session(
                    user=user_profile.name,
                    profiles=profiles,
                    receiver=receiver,
                    resolution=adaptive_resolution,
                    fps=self.current_fps,
                    quality=self.current_quality,
                    codec="h264",
                    hdr=False
                )
                
                success = await asyncio.wait_for(
                    self.device.connect(),
                    timeout=CONNECTION_TIMEOUT
                )
                
                if success and self.device.connected:
                    logger.info("✅ Riconnessione riuscita!")
                    
                    # Riavvia il monitoraggio e la cattura frame
                    self.active_tasks = []
                    
                    health_task = asyncio.create_task(self.health_check_task(self.device))
                    self.active_tasks.append(health_task)
                    
                    frame_task = asyncio.create_task(
                        self.frame_handler.save_video_frames(self.device, user_profile.name)
                    )
                    self.active_tasks.append(frame_task)
                    
                    # Reinizializza il controller
                    initialize_controller(self.device)
                    
                    self.reconnection_in_progress = False
                    return True
                    
            except Exception as e:
                logger.error(f"❌ Errore durante la riconnessione: {e}")
            
            await asyncio.sleep(RETRY_DELAY)
        
        logger.error("❌ Impossibile ristabilire la connessione dopo più tentativi.")
        self.reconnection_in_progress = False
        return False
    
    async def adaptive_quality_control(self, device, check_interval=10.0):
        """Regola dinamicamente la qualità video in base alla stabilità della connessione."""
        logger.info("📊 Avvio sistema di controllo adattivo della qualità...")
        
        # Parametri di monitoraggio
        dropped_frames_threshold = 5  # Soglia di frame persi per intervallo
        
        while device.session and device.session.is_ready and not self.reconnection_in_progress:
            try:
                await asyncio.sleep(check_interval)
                
                # Ottieni statistiche dal frame handler
                if hasattr(self.frame_handler, 'stats'):
                    frames_dropped = self.frame_handler.stats.get("frames_dropped", 0)
                    frames_received = self.frame_handler.stats.get("frames_received", 0)
                    errors = self.frame_handler.stats.get("errors", 0)
                    
                    # Calcola la percentuale di frame persi
                    drop_percentage = 0
                    if frames_received > 0:
                        drop_percentage = (frames_dropped / frames_received) * 100
                    
                    logger.info(f"📊 Analisi qualità: frame persi {drop_percentage:.1f}% ({frames_dropped}/{frames_received}), errori: {errors}")
                    
                    # Adatta la qualità se necessario
                    if (drop_percentage > 10 or errors > 5) and self.current_resolution != "540p":
                        logger.warning("⚠️ Problemi di prestazioni, la prossima sessione userà una qualità inferiore")
                        self.current_resolution = "540p"
                        self.current_fps = 30
                        self.current_quality = "low"
                        
                    elif drop_percentage < 2 and errors < 2 and self.current_resolution == "540p":
                        logger.info("✅ Connessione stabile, la prossima sessione userà una qualità migliore")
                        self.current_resolution = "720p"
                        self.current_fps = 30
                        self.current_quality = "default"
                    
                    # Resetta i contatori per il prossimo intervallo
                    # Ma non tutti i valori, per mantenere traccia delle statistiche complessive
                    self.frame_handler.stats["frames_dropped"] = 0
                    
            except Exception as e:
                logger.error(f"❌ Errore durante il controllo adattivo della qualità: {e}")
            
        logger.info("📊 Controllo adattivo della qualità terminato")
    
    async def connect_and_run_session(self, user_profile, selected_mac, ip_address):
        """Connette l'utente alla sessione Remote Play e avvia la cattura dei frame con gestione avanzata della connessione."""
        # Salva questi valori per eventuali riconnessioni
        self.user_profile = user_profile
        self.ip_address = ip_address
        
        self.device = RPDevice(ip_address)
        retries = 0
        
        while retries < CONNECTION_RETRIES:
            try:
                logger.info(f"\n🔌 Tentativo di connessione {retries+1}/{CONNECTION_RETRIES}...")
                
                # Verifica stato console con timeout
                logger.info("\n🔌 Verifica stato della console...")
                try:
                    status = await asyncio.wait_for(
                        self.device.async_get_status(),
                        timeout=CONNECTION_TIMEOUT
                    )
                except asyncio.TimeoutError:
                    logger.error("❌ Timeout durante la verifica dello stato della console.")
                    retries += 1
                    await asyncio.sleep(RETRY_DELAY)
                    continue
                
                if not status:
                    logger.error("❌ Errore: impossibile ottenere lo stato della console.")
                    retries += 1
                    await asyncio.sleep(RETRY_DELAY)
                    continue

                user_profile = profiles.get_user_profile(user_profile.name)
                if not user_profile:
                    logger.error(f"❌ Errore: L'utente {user_profile.name} non è registrato correttamente.")
                    return

                logger.info("\n🎮 Avvio della sessione Remote Play...")
                frame_path = clean_frame_directory(user_profile.name)
                
                # Configurazione ottimizzata del receiver
                receiver = QueueReceiver()
                receiver.queue_size = 60  # Buffer più grande
                receiver.video_format = "rgb24"  # Formato video esplicito

                session = self.device.create_session(
                    user=user_profile.name,
                    profiles=profiles,
                    receiver=receiver,
                    resolution=self.current_resolution,
                    fps=self.current_fps,
                    quality=self.current_quality,
                    codec="h264",
                    hdr=False
                )

                # Tentativi di connessione con timeout
                try:
                    success = await asyncio.wait_for(
                        self.device.connect(),
                        timeout=CONNECTION_TIMEOUT
                    )
                except asyncio.TimeoutError:
                    logger.error("❌ Timeout durante la connessione alla console.")
                    retries += 1
                    continue
                
                if not success:
                    logger.error("❌ Errore: Connessione alla sessione Remote Play fallita.")
                    retries += 1
                    continue

                await asyncio.sleep(3)
                if not receiver.video_frames:
                    logger.warning("⚠️ Nessun frame ricevuto con h264, provo con HEVC...")
                    session.stop()
                    session = self.device.create_session = self.device.create_session(
                        user=user_profile.name,
                        profiles=profiles,
                        receiver=receiver,
                        resolution=self.current_resolution,
                        fps=self.current_fps,
                        quality=self.current_quality,
                        codec="hevc",
                        hdr=False
                    )
                    
                    try:
                        success = await asyncio.wait_for(
                            self.device.connect(),
                            timeout=CONNECTION_TIMEOUT
                        )
                    except asyncio.TimeoutError:
                        logger.error("❌ Timeout durante la connessione con HEVC.")
                        retries += 1
                        continue
                    
                    if not success:
                        logger.error("❌ Errore: Connessione alla sessione con HEVC fallita.")
                        retries += 1
                        continue

                logger.info(f"✅ Sessione avviata con successo per {user_profile.name}!")

                # Avvia monitoraggio della connessione
                health_task = asyncio.create_task(self.health_check_task(self.device))
                self.active_tasks.append(health_task)

                # Avvia controllo adattivo della qualità
                quality_task = asyncio.create_task(self.adaptive_quality_control(self.device))
                self.active_tasks.append(quality_task)

                # Avvia la cattura dei frame con il nuovo gestore ottimizzato
                frame_task = asyncio.create_task(
                    self.frame_handler.save_video_frames(self.device, user_profile.name)
                )
                self.active_tasks.append(frame_task)

                initialize_controller(self.device)
                await asyncio.sleep(3)
                logger.info(f"\n🔍 Stato della sessione prima di inviare comandi: {self.device.session}")
                await send_test_commands(self.device)

                # Attendi fino a quando uno dei task termina o viene interrotto
                try:
                    done, pending = await asyncio.wait(
                        [t for t in self.active_tasks if not t.done()],
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    for task in done:
                        if task.exception():
                            logger.error(f"❌ Task terminato con errore: {task.exception()}")
                except asyncio.CancelledError:
                    logger.info("🛑 Operazione di attesa task cancellata.")
                
                break  # Usciamo dal ciclo se la connessione ha avuto successo

            except asyncio.CancelledError:
                logger.info("🛑 Operazione di connessione cancellata.")
                break
            except Exception as e:
                logger.error(f"❌ Errore durante la sessione: {e}")
                retries += 1
                await asyncio.sleep(RETRY_DELAY)

        # Disconnessione sicura alla fine
        await self.safe_disconnect(self.device)
        
        # Cancella tutti i task attivi
        for task in self.active_tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        self.active_tasks = []

# Per mantenere la compatibilità con il codice esistente
async def connect_and_run_session(user_profile, selected_mac, ip_address):
    """Funzione di compatibilità che usa la nuova implementazione."""
    manager = EnhancedSessionManager()
    await manager.connect_and_run_session(user_profile, selected_mac, ip_address)

# Mantieni la funzione safe_disconnect per compatibilità
async def safe_disconnect(device):
    """Funzione di compatibilità che usa la nuova implementazione."""
    manager = EnhancedSessionManager()
    await manager.safe_disconnect(device)