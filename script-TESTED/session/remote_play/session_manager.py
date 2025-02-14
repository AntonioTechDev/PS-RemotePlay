import asyncio
from pyremoteplay import RPDevice
from pyremoteplay.profile import Profiles
from pyremoteplay.receiver import QueueReceiver
from remote_play.utils import clean_frame_directory
from remote_play.controller import initialize_controller, send_test_commands
from remote_play.frame_handler import save_video_frames

Profiles.set_default_path(r"C:\Users\ADB\.pyremoteplay\.profile.json")
profiles = Profiles.load()

async def safe_disconnect(device):
    """Gestisce la disconnessione sicura della sessione Remote Play."""
    if device.session:
        print("\n🔌 Tentativo di disconnessione in corso...")

        if device.connected:
            print("⏳ Arresto della sessione in corso...")
            device.session.stop()
            await asyncio.sleep(2)

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
        frame_path = clean_frame_directory(user_profile.name)
        receiver = QueueReceiver()
        receiver.queue_size = 100

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
