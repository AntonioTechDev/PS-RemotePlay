# This file provides:
# - initialize_controller(): To activate and start the session controller.
# - send_test_commands(): To send a preset sequence of commands to the console.

from pyremoteplay import RPDevice
import asyncio

def initialize_controller(device):
    """ Attiva il controller della sessione. """
    print("🎮 Inizializzazione del controller...")
    device.controller.start()
    print("✅ Controller attivato!")

async def send_test_commands(device):
    """ Esegue una sequenza di comandi di test. """
    commands = ["CROSS", "CIRCLE", "SQUARE", "TRIANGLE", "UP", "DOWN", "LEFT", "RIGHT", "OPTIONS"]
    
    for command in commands:
        device.controller.button(command, "tap")
        print(f"✅ Comando {command} inviato!")
        await asyncio.sleep(1)
