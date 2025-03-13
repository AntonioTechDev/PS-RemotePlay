from pyremoteplay import RPDevice
import asyncio

def initialize_controller(device):
    """ Attiva il controller della sessione. """
    print("🎮 Inizializzazione del controller...")
    try:
        device.controller.start()
        print("✅ Controller attivato!")
    except Exception as e:
        print(f"❌ Errore nell'attivazione del controller: {e}")
        raise

async def send_test_commands(device):
    """ Esegue una sequenza di comandi di test all'infinito. """
    commands = ["CROSS", "CIRCLE", "SQUARE", "TRIANGLE", "UP", "DOWN", "LEFT", "RIGHT", "OPTIONS"]
    
    try:
        while True:
            for command in commands:
                # Verifica che la sessione sia ancora attiva prima di inviare ogni comando
                if not device or not device.session or not device.session.is_ready:
                    print("🛑 Sessione non più attiva, interrompo invio comandi.")
                    return
                
                try:
                    device.controller.button(command, "tap")
                    print(f"✅ Comando {command} inviato!")
                except Exception as e:
                    print(f"⚠️ Errore nell'invio del comando {command}: {e}")
                    # Se c'è un errore nell'invio di un comando, verifichiamo lo stato della sessione
                    if not device.session or not device.session.is_ready:
                        print("🛑 Sessione disconnessa durante l'invio comando. Uscita.")
                        return
                    
                await asyncio.sleep(1)
    except asyncio.CancelledError:
        print("⚠️ Task di invio comandi cancellata.")
        raise
    except Exception as e:
        print(f"❌ Errore imprevisto durante l'invio dei comandi: {e}")
        raise