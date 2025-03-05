import asyncio
import logging
from pyremoteplay import RPDevice
from pyremoteplay.profile import Profiles
from pyremoteplay.receiver import QueueReceiver
from remote_play.utils import clean_frame_directory
from remote_play.controller import initialize_controller, send_test_commands
from remote_play.frame_handler import EnhancedFrameHandler
import socket

# Configurazione logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SessionManager")

# Configurazione percorso profili
PROFILE_PATH = r"C:\Users\ADB\.pyremoteplay\.profile.json"
Profiles.set_default_path(PROFILE_PATH)
profiles = Profiles.load()

# Costanti per la connessione
CONNECTION_RETRIES = 3
RETRY_DELAY = 2.0
CONNECTION_TIMEOUT = 10.0

class EnhancedSessionManager:
    """Gestore sessione Remote Play ottimizzato per una connessione più stabile."""
    
    def __init__(self):
        """Inizializza il gestore della sessione."""
        self.frame_handler = EnhancedFrameHandler(max_buffer_size=60)  # Buffer più grande per migliore fluidità
        self.device = None
        self.active_tasks = []
    
    async def safe_disconnect(self, device):
        """Gestisce la disconnessione sicura della sessione Remote Play."""
        if device.session:
            logger.info("\n🔌 Tentativo di disconnessione in corso...")

            if device.connected:
                logger.info("⏳ Arresto della sessione in corso...")
                try:
                    device.disconnect()
                    await asyncio.sleep(2)  # Attendi la chiusura corretta del trasporto
                except Exception as e:
                    logger.warning(f"⚠️ Errore durante la disconnessione: {e}")

            # Chiusura del trasporto UDP per evitare errori "Fatal write error on datagram transport"
            if hasattr(device, "transport") and device.transport:
                try:
                    logger.info("🔌 Chiusura forzata del trasporto...")
                    device.transport.close()
                except Exception as e:
                    logger.warning(f"⚠️ Errore durante la chiusura del trasporto: {e}")

            # Arresto del frame handler
            if hasattr(self, 'frame_handler') and self.frame_handler:
                self.frame_handler.stop()

            device._session = None
            logger.info("✅ Sessione disconnessa correttamente!")
        else:
            logger.warning("⚠️ Nessuna sessione attiva da disconnettere.")
    
    async def health_check_task(self, device, interval=5.0):
        """Task che monitora costantemente la salute della connessione."""
        logger.info("🔍 Avvio monitoraggio stato connessione...")
        
        while device.session and device.session.is_ready:
            try:
                if not device.connected:
                    logger.error("❌ Connessione persa! Tentativo di riconnessione...")
                    # Qui potremmo implementare la logica di riconnessione automatica
                    break
                
                # Verifica la connessione di rete verso la console
                if hasattr(device, 'host'):
                    try:
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                            s.settimeout(1.0)
                            result = s.connect_ex((device.host, 9295))  # Porta standard RemotePlay
                            if result != 0:
                                logger.warning(f"⚠️ La console non risponde sulla porta RemotePlay (errore {result})")
                    except Exception as e:
                        logger.warning(f"⚠️ Errore durante il controllo della connessione: {e}")
                
                # Controlla se receiver e flusso video sono attivi
                if device.session.receiver and not device.session.receiver.video_frames:
                    logger.warning("⚠️ Nessun frame ricevuto nell'intervallo di controllo")
            
            except Exception as e:
                logger.error(f"❌ Errore durante il monitoraggio della connessione: {e}")
            
            await asyncio.sleep(interval)
        
        logger.info("🔍 Monitoraggio connessione terminato")
    
    async def connect_and_run_session(self, user_profile, selected_mac, ip_address):
        """Connette l'utente alla sessione Remote Play e avvia la cattura dei frame con gestione avanzata della connessione."""
        self.device = RPDevice(ip_address)
        retries = 0
        
        while retries < CONNECTION_RETRIES:
            try:
                logger.info(f"\n🔌 Tentativo di connessione {retries+1}/{CONNECTION_RETRIES}...")
                
                # Verifica stato console con timeout
                logger.info("\n🔌 Verifica stato della console...")
                status = await asyncio.wait_for(
                    self.device.async_get_status(),
                    timeout=CONNECTION_TIMEOUT
                )
                
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
                    resolution="720p",
                    fps=30,
                    quality="default",
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
                    session = self.device.create_session(
                        user=user_profile.name,
                        profiles=profiles,
                        receiver=receiver,
                        resolution="720p",
                        fps=30,
                        quality="default",
                        codec="hevc",
                        hdr=False
                    )
                    
                    success = await asyncio.wait_for(
                        self.device.connect(),
                        timeout=CONNECTION_TIMEOUT
                    )
                    
                    if not success:
                        logger.error("❌ Errore: Connessione alla sessione con HEVC fallita.")
                        retries += 1
                        continue

                logger.info(f"✅ Sessione avviata con successo per {user_profile.name}!")

                # Avvia monitoraggio della connessione
                health_task = asyncio.create_task(self.health_check_task(self.device))
                self.active_tasks.append(health_task)

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
                done, _ = await asyncio.wait(
                    [t for t in self.active_tasks if not t.done()],
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                for task in done:
                    if task.exception():
                        logger.error(f"❌ Task terminato con errore: {task.exception()}")
                
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