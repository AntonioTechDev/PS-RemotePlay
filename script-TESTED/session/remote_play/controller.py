from pyremoteplay import RPDevice
import asyncio
import traceback

# Abilita logging dettagliato
DEBUG = True

def debug_log(message):
    """Funzione helper per log dettagliati."""
    if DEBUG:
        print(f"🎮 [DEBUG-CONTROLLER]: {message}")

def initialize_controller(device):
    """ Attiva il controller della sessione. """
    print("🎮 Inizializzazione del controller...")
    try:
        debug_log(f"Controller pre-init - device: {device}, has controller: {hasattr(device, 'controller')}")
        
        if not hasattr(device, 'controller') or device.controller is None:
            debug_log("Controller non disponibile o None!")
            raise Exception("Controller non disponibile sul device")
            
        device.controller.start()
        
        debug_log(f"Controller post-init - controller attivo: {device.controller}")
        print("✅ Controller attivato!")
    except Exception as e:
        print(f"❌ Errore nell'attivazione del controller: {e}")
        debug_log(f"Eccezione in init_controller: {e}")
        debug_log(traceback.format_exc())
        raise

async def send_test_commands(device):
    """ Esegue una sequenza di comandi di test all'infinito. """
    commands = ["CROSS", "CIRCLE", "SQUARE", "TRIANGLE", "UP", "DOWN", "LEFT", "RIGHT", "OPTIONS"]
    
    # Contatore per tracciare gli errori consecutivi
    consecutive_errors = 0
    max_consecutive_errors = 5  # Se ci sono 5 errori consecutivi, usciamo dal loop
    
    debug_log(f"Avvio invio comandi - device: {device}, session: {device.session if hasattr(device, 'session') else None}")
    
    try:
        cycle_count = 0
        while True:
            cycle_count += 1
            error_in_cycle = False
            debug_log(f"Inizio ciclo comandi #{cycle_count}...")
            
            for command in commands:
                # Verifica dettagliata che la sessione sia ancora attiva
                session_ready = (hasattr(device, 'session') and 
                                device.session is not None and 
                                hasattr(device.session, 'is_ready') and 
                                device.session.is_ready)
                
                controller_ready = (hasattr(device, 'controller') and device.controller is not None)
                
                # Log dettagliato dello stato
                if DEBUG and (cycle_count % 5 == 0 or not session_ready or not controller_ready):
                    debug_log(f"Stato pre-comando {command} - Session: {session_ready}, Controller: {controller_ready}")
                
                # Verifica che la sessione sia ancora attiva prima di inviare ogni comando
                if not session_ready or not controller_ready:
                    debug_log(f"Sessione o controller non disponibile - Session ready: {session_ready}, Controller ready: {controller_ready}")
                    print("🛑 Sessione non più attiva, interrompo invio comandi.")
                    return  # Esci dalla funzione, sarà il session_manager a gestire la riconnessione
                
                try:
                    # Attesa breve prima del comando per ridurre carico rete
                    await asyncio.sleep(0.1)
                    
                    debug_log(f"Invio comando {command}...")
                    device.controller.button(command, "tap")
                    print(f"✅ Comando {command} inviato!")
                    consecutive_errors = 0  # Resetta il contatore se un comando ha successo
                except Exception as e:
                    error_in_cycle = True
                    consecutive_errors += 1
                    print(f"⚠️ Errore nell'invio del comando {command}: {e}")
                    debug_log(f"Eccezione invio comando {command}: {e}")
                    
                    # Analisi dettagliata dello stato in caso di errore
                    debug_log(f"Stato durante errore: device.session = {device.session if hasattr(device, 'session') else None}")
                    debug_log(f"Stato controller durante errore: {device.controller if hasattr(device, 'controller') else None}")
                    
                    # Stack trace per debug
                    debug_log(traceback.format_exc())
                    
                    # Se troppi errori consecutivi, segnala un problema serio
                    if consecutive_errors >= max_consecutive_errors:
                        debug_log(f"Troppi errori consecutivi: {consecutive_errors}. Necessaria riconnessione completa.")
                        print(f"❌ Troppi errori consecutivi ({consecutive_errors}). Necessaria riconnessione.")
                        raise Exception("Controller disconnesso dopo errori multipli.")
                    
                # Attesa tra un comando e l'altro
                await asyncio.sleep(1)
            
            # Debug di fine ciclo
            debug_log(f"Fine ciclo comandi #{cycle_count} - errori: {error_in_cycle}")
            
            # Se tutti i comandi in questo ciclo hanno generato errori, attendi un po' di più
            if error_in_cycle:
                print("⚠️ Ciclo di comandi completato con errori. Attesa aggiuntiva...")
                await asyncio.sleep(2)  # Attesa aggiuntiva tra i cicli con errori
                
    except asyncio.CancelledError:
        debug_log("Task di invio comandi cancellata.")
        print("⚠️ Task di invio comandi cancellata.")
        raise
    except Exception as e:
        debug_log(f"Eccezione critica in send_test_commands: {e}")
        debug_log(traceback.format_exc())
        print(f"❌ Errore imprevisto durante l'invio dei comandi: {e}")
        raise  # Propaga l'eccezione al session_manager per gestire la riconnessione