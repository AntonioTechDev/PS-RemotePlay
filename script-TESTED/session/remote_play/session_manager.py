import asyncio
from pyremoteplay import RPDevice
from pyremoteplay.profile import Profiles
from pyremoteplay.receiver import QueueReceiver
from remote_play.utils import clean_frame_directory
from remote_play.controller import initialize_controller, send_test_commands
from remote_play.frame_handler import save_video_frames
import sys

Profiles.set_default_path(r"C:\Users\ADB\.pyremoteplay\.profile.json")
profiles = Profiles.load()

async def safe_disconnect(device):
    """Gestisce la disconnessione sicura della sessione Remote Play."""
    try:
        if device and hasattr(device, "session"):
            print("\n🔌 Tentativo di disconnessione in corso...")

            if hasattr(device, "connected") and device.connected:
                print("⏳ Arresto della sessione in corso...")
                try:
                    device.disconnect()
                    await asyncio.sleep(2)  # Attendi la chiusura corretta del trasporto
                except Exception as e:
                    print(f"⚠️ Errore durante la disconnessione: {e}")

            # Chiusura del trasporto UDP per evitare errori "Fatal write error on datagram transport"
            if hasattr(device, "transport") and device.transport:
                try:
                    print("🔌 Chiusura forzata del trasporto...")
                    device.transport.close()
                except Exception as e:
                    print(f"⚠️ Errore durante la chiusura del trasporto: {e}")

            # Pulisci riferimenti alla sessione
            device._session = None
            print("✅ Sessione disconnessa correttamente!")
        else:
            print("⚠️ Nessuna sessione attiva da disconnettere.")
    except Exception as e:
        print(f"⚠️ Errore imprevisto durante la disconnessione: {e}")


async def connect_and_run_session(user_profile, selected_mac, ip_address):
    """ Connette l'utente alla sessione Remote Play e avvia la cattura dei frame. """
    device = RPDevice(ip_address)
    frame_task = None
    controller_task = None
    
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
        frame_path = clean_frame_directory(user_profile.name)
        receiver = QueueReceiver()
        receiver.queue_size = 100

        session = device.create_session(
            user=user_profile.name,
            profiles=profiles,
            receiver=receiver,
            resolution="360p",
            fps=30,
            quality="default",
            codec="h264",
            hdr=False
        )

        success = await device.connect()
        if not success:
            print("❌ Errore: Connessione alla sessione Remote Play fallita.")
            return

        await asyncio.sleep(3)
        if not receiver.video_frames:
            print("⚠️ Nessun frame ricevuto con h264, provo con HEVC...")
            session.stop()
            session = device.create_session(
                user=user_profile.name,
                profiles=profiles,
                receiver=receiver,
                resolution="360p",
                fps=30,
                quality="default",
                codec="HEVC",
                hdr=False
            )
            success = await device.connect()
            if not success:
                print("❌ Errore: Connessione alla sessione con HEVC fallita.")
                return

        print(f"✅ Sessione avviata con successo per {user_profile.name}!")

        # Avvia la task per il salvataggio dei frame come task separata
        frame_task = asyncio.create_task(save_video_frames(device, user_profile.name))
        print(f"🟢 Task di salvataggio avviato? {frame_task is not None}")

        # Inizializza il controller
        initialize_controller(device)
        await asyncio.sleep(3)
        
        print(f"\n🔍 Stato della sessione prima di inviare comandi: {device.session}")
        
        # Avvia l'invio dei comandi in un task separato con gestione degli errori
        controller_task = asyncio.create_task(controller_with_error_handling(device))
        
        # Attendi che una delle due task termini
        done, pending = await asyncio.wait(
            [frame_task, controller_task], 
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # Se una task termina, cancella l'altra
        for task in pending:
            print(f"🛑 Cancellazione task in pending: {task}")
            task.cancel()

    except asyncio.CancelledError:
        print("⚠️ Task principale cancellata.")
    except Exception as e:
        print(f"❌ Errore durante la sessione: {e}")

    finally:
        # Assicurati che tutte le task siano cancellate
        if frame_task and not frame_task.done():
            frame_task.cancel()
        if controller_task and not controller_task.done():
            controller_task.cancel()
            
        print("\n🔌 Disconnessione della sessione...")
        await safe_disconnect(device)


async def controller_with_error_handling(device):
    """Wrapper per l'invio dei comandi con gestione degli errori."""
    try:
        # Massimo 3 tentativi in caso di errore di trasporto
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                await send_test_commands(device)
                break  # Se completato con successo, esci dal ciclo
            except Exception as e:
                retry_count += 1
                print(f"⚠️ Errore nel controller (tentativo {retry_count}/{max_retries}): {e}")
                
                # Verifica se la sessione è ancora valida
                if not device or not device.session or not device.session.is_ready:
                    print("🛑 Sessione non più valida, interrompo invio comandi.")
                    break
                    
                # Attendi un po' prima di riprovare
                await asyncio.sleep(2)
                
                if retry_count >= max_retries:
                    print("❌ Numero massimo di tentativi raggiunto. Interrompo invio comandi.")
                    break
                    
    except asyncio.CancelledError:
        print("⚠️ Controller task cancellata.")
    except Exception as e:
        print(f"❌ Errore imprevisto nel controller: {e}")