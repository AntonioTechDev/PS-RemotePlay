import asyncio
from pyremoteplay import RPDevice
from pyremoteplay.profile import Profiles
from pyremoteplay.receiver import QueueReceiver
from remote_play.utils import clean_frame_directory
from remote_play.controller import initialize_controller, send_test_commands
from remote_play.frame_handler import save_video_frames
import sys
import time
import traceback

# Abilita logging dettagliato
DEBUG = True

def debug_log(message):
    """Funzione helper per log dettagliati."""
    if DEBUG:
        print(f"🔍 [DEBUG]: {message}")

Profiles.set_default_path(r"C:\Users\ADB\.pyremoteplay\.profile.json")
profiles = Profiles.load()

async def safe_disconnect(device, force_reconnect=False):
    """
    Gestisce la disconnessione sicura della sessione Remote Play.
    
    Args:
        device: Il dispositivo RPDevice da disconnettere
        force_reconnect: Se True, forza una disconnessione completa per permettere una nuova connessione
    """
    try:
        debug_log(f"Disconnessione - device: {device}, has session: {hasattr(device, 'session')}")
        
        if device:
            print("\n🔌 Tentativo di disconnessione in corso...")
            
            # Controlla gli attributi in modo sicuro
            has_session = hasattr(device, "session") and device.session is not None
            has_transport = hasattr(device, "transport") and device.transport is not None
            has_connected = hasattr(device, "connected")
            
            debug_log(f"Stato pre-disconnessione - Session: {has_session}, Transport: {has_transport}, Connected: {has_connected}")
            
            if has_session:
                # Se ci troviamo in modalità riconnessione, dobbiamo fare un reset completo
                if force_reconnect:
                    try:
                        debug_log("Esecuzione soft reset completo della sessione.")
                        # Proviamo a fermare la sessione in modo pulito
                        if hasattr(device.session, "stop"):
                            device.session.stop()
                            debug_log("Session.stop() eseguito.")
                            
                        # Chiudi manualmente ogni componente
                        if hasattr(device, "_controller") and device._controller:
                            device._controller = None
                            debug_log("Controller resettato a None.")
                        
                        # Reset del ricevitore se esiste
                        if hasattr(device.session, "receiver") and device.session.receiver:
                            device.session.receiver = None
                            debug_log("Receiver resettato a None.")
                            
                        # Rimuovi riferimenti alla sessione
                        device._session = None
                        debug_log("Sessione resettata a None.")
                        
                        # Assicurati che il trasporto venga chiuso correttamente
                        if has_transport:
                            try:
                                debug_log("Chiusura forzata del trasporto...")
                                device.transport.close()
                                device.transport = None
                                debug_log("Trasporto chiuso e resettato a None.")
                            except Exception as e:
                                debug_log(f"Errore chiusura trasporto durante force_reconnect: {e}")
                        
                        # Attendi che tutto si stabilizzi
                        await asyncio.sleep(3)
                        
                    except Exception as e:
                        debug_log(f"Errore durante force_reconnect: {e}")
                        debug_log(traceback.format_exc())
                else:
                    # Disconnessione normale
                    if has_connected and device.connected:
                        print("⏳ Arresto della sessione in corso...")
                        try:
                            device.disconnect()
                            debug_log("device.disconnect() eseguito.")
                            await asyncio.sleep(2)  # Attendi la chiusura corretta del trasporto
                        except Exception as e:
                            print(f"⚠️ Errore durante la disconnessione: {e}")
                            debug_log(traceback.format_exc())

                    # Chiusura del trasporto UDP per evitare errori "Fatal write error on datagram transport"
                    if has_transport:
                        try:
                            print("🔌 Chiusura forzata del trasporto...")
                            device.transport.close()
                            debug_log("device.transport.close() eseguito.")
                        except Exception as e:
                            print(f"⚠️ Errore durante la chiusura del trasporto: {e}")
                            debug_log(traceback.format_exc())

                    # Pulisci riferimenti alla sessione
                    device._session = None
                    debug_log("device._session = None eseguito.")
            
            print("✅ Sessione disconnessa correttamente!")
        else:
            print("⚠️ Nessuna sessione attiva da disconnettere.")
    except Exception as e:
        print(f"⚠️ Errore imprevisto durante la disconnessione: {e}")
        debug_log(f"Stack trace disconnessione: {traceback.format_exc()}")


async def reset_device_connection(device, user_name):
    """
    Resetta completamente la connessione del dispositivo prima di un nuovo tentativo.
    Questo è necessario quando una sessione precedente è ancora aperta lato console.
    """
    debug_log(f"Inizio reset completo connessione per {user_name}...")
    
    # Primo passo: disconnessione completa
    await safe_disconnect(device, force_reconnect=True)
    
    # Forza il garbage collector per rimuovere riferimenti
    import gc
    gc.collect()
    debug_log("Garbage collection eseguita.")
    
    # Attendi che la connessione si resetti completamente
    await asyncio.sleep(5)
    
    # Crea un nuovo dispositivo se necessario
    if device._session is not None or device.transport is not None:
        debug_log("Creando un nuovo oggetto RPDevice...")
        ip_address = device.host
        device = RPDevice(ip_address)
    
    debug_log("Reset connessione completato.")
    return device


async def create_session(device, user_name, profiles, resolution="360p", fps=30, codec="h264"):
    """Crea una sessione Remote Play e gestisce il fallback a HEVC se necessario."""
    try:
        debug_log(f"Creazione sessione per {user_name} con {codec}...")
        
        # Verifica preliminare
        if hasattr(device, '_session') and device._session is not None:
            debug_log("ERRORE: Device ha già una sessione. Eseguo reset prima di crearne una nuova.")
            device = await reset_device_connection(device, user_name)
        
        # Crea un nuovo ricevitore per questa sessione
        receiver = QueueReceiver()
        receiver.queue_size = 100
        debug_log(f"Nuovo QueueReceiver creato con queue_size={receiver.queue_size}")

        # Creazione sessione
        debug_log(f"Chiamata a device.create_session con codec={codec}...")
        session = device.create_session(
            user=user_name,
            profiles=profiles,
            receiver=receiver,
            resolution=resolution,
            fps=fps,
            quality="default",
            codec=codec,
            hdr=False
        )
        debug_log(f"Sessione creata: {session}")
        
        # Tentativo di connessione
        debug_log("Tentativo di connessione...")
        success = await device.connect()
        debug_log(f"device.connect() risultato: {success}")
        
        if not success:
            debug_log(f"❌ Errore: Connessione con codec {codec} fallita.")
            return False, None
        
        # Verifica che i frame vengano ricevuti
        debug_log("Attesa 3s per verifica ricezione frame...")
        await asyncio.sleep(3)
        
        # Controlla se video_frames è None o vuoto
        has_frames = (receiver.video_frames is not None and len(receiver.video_frames) > 0)
        debug_log(f"Ricevitore ha frame? {has_frames}")
        
        if not has_frames:
            if codec == "h264":
                debug_log("⚠️ Nessun frame ricevuto con h264, provo con HEVC...")
                
                # Assicurati di fermare la sessione prima di crearne una nuova
                if session:
                    debug_log("Arresto sessione h264 prima di provare HEVC...")
                    session.stop()
                    await asyncio.sleep(2)
                
                # Eseguiamo un reset più profondo prima di riprovare con HEVC
                device = await reset_device_connection(device, user_name)
                
                return await create_session(device, user_name, profiles, resolution, fps, "HEVC")
            else:
                debug_log("❌ Errore: Nessun frame ricevuto con codec HEVC.")
                return False, None
        
        print(f"✅ Sessione avviata con successo per {user_name} usando {codec}!")
        debug_log(f"Dettagli sessione: {session}")
        return True, session
    except Exception as e:
        debug_log(f"Eccezione in create_session: {e}")
        debug_log(traceback.format_exc())
        return False, None


async def reconnect_controller(device, user_profile, max_retries=3):
    """Riconnette il controller se si verifica un errore."""
    if not device:
        print("❌ Errore: Device non disponibile per la riconnessione.")
        return False
    
    # Prima esegui un reset completo della connessione
    device = await reset_device_connection(device, user_profile.name)
    
    print("\n🔄 Tentativo di riconnessione del controller...")
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"🔄 Tentativo {attempt}/{max_retries}...")
            debug_log(f"Inizio tentativo di riconnessione {attempt}...")
            
            # Ricrea la sessione
            success, _ = await create_session(
                device, 
                user_profile.name, 
                profiles
            )
            
            if not success:
                print(f"❌ Tentativo {attempt} fallito: creazione sessione non riuscita.")
                debug_log(f"Riconnessione tentativo {attempt} fallito: sessione non creata.")
                await asyncio.sleep(2)
                
                # Se c'è stato un fallimento, esegui un reset più profondo prima del prossimo tentativo
                device = await reset_device_connection(device, user_profile.name)
                continue
                
            # Reinizializza il controller
            debug_log("Reinizializzazione controller...")
            initialize_controller(device)
            await asyncio.sleep(1)
            
            # Invia un comando di test per verificare che funzioni
            try:
                debug_log("Invio comando di test OPTIONS...")
                device.controller.button("OPTIONS", "tap")
                print("✅ Test controller riuscito! Controller riconnesso.")
                debug_log("Test controller completato con successo.")
                return True
            except Exception as e:
                print(f"❌ Test controller fallito: {e}")
                debug_log(f"Test controller fallito: {e}")
                debug_log(traceback.format_exc())
                await asyncio.sleep(2)
                
                # Reset più aggressivo
                device = await reset_device_connection(device, user_profile.name)
                
        except Exception as e:
            print(f"❌ Errore durante il tentativo {attempt} di riconnessione: {e}")
            debug_log(f"Eccezione durante tentativo {attempt}: {e}")
            debug_log(traceback.format_exc())
            await asyncio.sleep(2)
            
            # Reset più aggressivo
            device = await reset_device_connection(device, user_profile.name)
    
    print("❌ Tutti i tentativi di riconnessione falliti.")
    debug_log("Riconnessione fallita dopo tutti i tentativi.")
    return False


async def connect_and_run_session(user_profile, selected_mac, ip_address):
    """ Connette l'utente alla sessione Remote Play e avvia la cattura dei frame. """
    device = RPDevice(ip_address)
    frame_task = None
    controller_task = None
    
    try:
        debug_log(f"Avvio sessione con {user_profile.name} su {ip_address}")
        print("\n🔌 Verifica stato della console...")
        status = device.get_status()
        debug_log(f"Stato console: {status}")
        
        if not status:
            print("❌ Errore: impossibile ottenere lo stato della console.")
            return

        # Ottieni il profilo utente
        user_profile = profiles.get_user_profile(user_profile.name)
        debug_log(f"Profilo utente ottenuto: {user_profile.name}")
        
        if not user_profile:
            print(f"❌ Errore: L'utente {user_profile.name} non è registrato correttamente.")
            return

        print("\n🎮 Avvio della sessione Remote Play...")
        frame_path = clean_frame_directory(user_profile.name)
        debug_log(f"Directory frame pulita: {frame_path}")
        
        # Crea la sessione iniziale
        success, _ = await create_session(device, user_profile.name, profiles)
        debug_log(f"Creazione sessione iniziale: {success}")
        
        if not success:
            print("❌ Errore: Impossibile creare la sessione Remote Play.")
            return

        # Avvia la task per il salvataggio dei frame (questa continuerà anche se il controller si disconnette)
        frame_task = asyncio.create_task(save_video_frames(device, user_profile.name))
        print(f"🟢 Task di salvataggio avviato? {frame_task is not None}")
        debug_log(f"Frame task avviata: {frame_task}")

        # Inizializza il controller
        debug_log("Inizializzazione controller...")
        initialize_controller(device)
        await asyncio.sleep(3)
        
        print(f"\n🔍 Stato della sessione prima di inviare comandi: {device.session}")
        debug_log(f"Stato sessione dettagliato: {device.session}")
        
        # Contatore di riconnessioni riuscite
        reconnection_count = 0
        max_reconnections = 3  # Numero massimo di riconnessioni prima di abbandonare
        
        # Monitora lo stato del controller con riconnessione automatica
        while reconnection_count <= max_reconnections:
            debug_log(f"Inizio ciclo di monitoraggio controller. Riconnessioni finora: {reconnection_count}/{max_reconnections}")
            
            try:
                # Avvia il controller in modalità test
                debug_log("Avvio task controller...")
                controller_task = asyncio.create_task(send_test_commands(device))
                
                # Attendi per vedere se il controller fallisce
                debug_log("Attesa monitoraggio controller (10s)...")
                await asyncio.sleep(10)
                
                # Controlla se il controller è ancora attivo
                if controller_task.done():
                    debug_log("Controller task terminata prematuramente, verifico stato...")
                    print("⚠️ Controller task terminata prematuramente, verifico se è necessaria una riconnessione...")
                    
                    # Se il controller task è terminato con errore, prova a riconnettersi
                    if controller_task.exception():
                        exception = controller_task.exception()
                        print(f"❌ Errore nel controller: {exception}")
                        debug_log(f"Eccezione controller: {exception}")
                        
                        # Qui implementiamo la logica di riconnessione
                        debug_log("Avvio procedura di riconnessione controller...")
                        reconnected = await reconnect_controller(device, user_profile)
                        
                        if not reconnected:
                            print("❌ Riconnessione fallita dopo multipli tentativi. Termino la sessione.")
                            debug_log("Riconnessione fallita, uscita dal ciclo principale.")
                            break
                        
                        # Incrementa il contatore di riconnessioni riuscite
                        reconnection_count += 1
                        debug_log(f"Riconnessione riuscita! Contatore: {reconnection_count}/{max_reconnections}")
                        
                        # Se riconnesso correttamente, continua con il ciclo while e crea un nuovo controller task
                        print("✅ Controller riconnesso, riprendo l'invio dei comandi...")
                        continue
                    else:
                        # Se il controller è terminato senza errori, probabilmente è stata una terminazione controllata
                        print("ℹ️ Controller terminato senza errori.")
                        debug_log("Controller terminato normalmente.")
                        break
                    
                # Se siamo qui, il controller è ancora in esecuzione
                # Attendi che il controller termini o fallisca
                try:
                    debug_log("Attesa completamento controller_task...")
                    await controller_task
                    print("✅ Controller task completata con successo.")
                    debug_log("Controller task completata normalmente.")
                    break
                except Exception as e:
                    print(f"❌ Controller ha generato un'eccezione: {e}")
                    debug_log(f"Eccezione in await controller_task: {e}")
                    debug_log(traceback.format_exc())
                    
                    # Prova a riconnettersi
                    debug_log("Avvio procedura di riconnessione dopo eccezione...")
                    reconnected = await reconnect_controller(device, user_profile)
                    if not reconnected:
                        print("❌ Riconnessione fallita. Termino la sessione.")
                        debug_log("Riconnessione fallita dopo eccezione, uscita.")
                        break
                    
                    # Incrementa il contatore di riconnessioni
                    reconnection_count += 1
                    debug_log(f"Riconnessione riuscita! Contatore: {reconnection_count}/{max_reconnections}")
                        
            except asyncio.CancelledError:
                print("⚠️ Task di monitoraggio cancellata.")
                debug_log("Task di monitoraggio cancellata.")
                break
            except Exception as e:
                print(f"❌ Errore imprevisto durante il monitoraggio del controller: {e}")
                debug_log(f"Eccezione imprevista in ciclo monitoraggio: {e}")
                debug_log(traceback.format_exc())
                break
        
        if reconnection_count > max_reconnections:
            print(f"❌ Numero massimo di riconnessioni ({max_reconnections}) raggiunto. Terminazione sessione.")
            debug_log(f"Limite riconnessioni {max_reconnections} raggiunto.")

    except asyncio.CancelledError:
        print("⚠️ Task principale cancellata.")
        debug_log("Task principale cancellata.")
    except Exception as e:
        print(f"❌ Errore durante la sessione: {e}")
        debug_log(f"Eccezione in connect_and_run_session: {e}")
        debug_log(traceback.format_exc())

    finally:
        debug_log("Fase di cleanup finale...")
        # Assicurati che tutte le task siano cancellate
        if frame_task and not frame_task.done():
            debug_log("Cancellazione frame_task...")
            frame_task.cancel()
        if controller_task and not controller_task.done():
            debug_log("Cancellazione controller_task...")
            controller_task.cancel()
            
        print("\n🔌 Disconnessione della sessione...")
        await safe_disconnect(device)
        debug_log("Disconnessione completata, terminate tutte le task.")