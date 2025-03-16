import sys
from pathlib import Path
# Adjust sys.path to include the project root directory (three levels up)
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# This file contains the EnhancedFrameHandler class which:
# - Captures video frames from the Remote Play session.
# - Saves the frames as images, applying compression and quality adjustments.
# - Monitors performance stats and adapts frame capture rate as needed.
# - When enabled for training, integrates with AI modules to record game state and actions.

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
import traceback  # Added import for traceback

# Configurazione logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levellevel)s - %(message)s')
logger = logging.getLogger("FrameHandler")

FRAME_DIR = "frames"

# Enable detailed logging
DEBUG = True

def debug_log(message):
    """Helper function for detailed logs."""
    if DEBUG:
        print(f"📽️ [DEBUG-FRAME]: {message}")

async def save_video_frames(device, user_name):
    """ Capture video frames from QueueReceiver and save them as images. """
    frame_path = os.path.join(FRAME_DIR, user_name)
    os.makedirs(frame_path, exist_ok=True)

    print(f"📡 Starting frame capture for {user_name}... Loop active until disconnection.")
    debug_log(f"Starting frame capture - device: {device}, session: {device.session if hasattr(device, 'session') else None}")
    
    # Initialize game state detector and data collector
    state_detector = FIFAStateDetector()
    data_collector = FIFADataCollector(save_dir="training_data/fifa")

    frame_counter = 0
    last_frame_time = datetime.now()
    frame_timeout = 10  # Maximum seconds without receiving a frame before considering disconnected
    time_without_session = 0
    max_time_without_session = 30  # Maximum seconds without session before exiting
    
    save_interval = 5  # Save a frame every N frames
    save_counter = 0

    while True:
        try:
            # Check session state
            session_active = (hasattr(device, 'session') and 
                             device.session is not None and 
                             hasattr(device.session, 'is_ready') and 
                             device.session.is_ready)
            
            if not session_active:
                time_without_session += 1
                if time_without_session >= max_time_without_session:
                    print(f"🛑 Too much time without an active session ({time_without_session}s). Exiting frame capture loop.")
                    break
                await asyncio.sleep(1)
                continue
            else:
                time_without_session = 0
            
            # Verify receiver validity
            receiver_valid = (hasattr(device, 'session') and 
                             device.session is not None and 
                             hasattr(device.session, 'receiver') and 
                             device.session.receiver is not None)
            
            if not receiver_valid:
                print("❌ Error: Receiver not available. Waiting...")
                await asyncio.sleep(0.5)
                continue
            
            receiver = device.session.receiver
            
            # Check if video_frames is None or empty
            if not receiver.video_frames:
                time_without_frame = (datetime.now() - last_frame_time).total_seconds()
                if time_without_frame > frame_timeout:
                    print(f"⚠️ No frames received for {time_without_frame:.1f} seconds. Possible disconnection.")
                await asyncio.sleep(0.5)
                continue
                
            # Access the latest frame
            try:
                frame = receiver.video_frames[-1]
            except (IndexError, TypeError, AttributeError) as e:
                print(f"⚠️ Error accessing frames: {e}. Waiting...")
                await asyncio.sleep(0.5)
                continue

            if frame is None:
                print("⚠️ Invalid frame received (None), ignoring.")
                await asyncio.sleep(0.5)
                continue
            
            # Convert frame to ndarray
            try:
                img = frame.to_ndarray(format='rgb24')
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            except Exception as e:
                print(f"❌ Error converting frame: {e}")
                continue

            # Detect game state
            try:
                game_state = state_detector.detect_state(img)
                debug_log(f"Game state detected: {game_state}")
            except Exception as e:
                print(f"⚠️ Error detecting game state: {e}")
                debug_log(traceback.format_exc())
                continue

            # Record game state and controller action
            try:
                controller_action = device.controller.stick_state  # Example: Get stick state
                data_collector.record_gameplay(game_state, controller_action)
                debug_log(f"Recorded game state and action: {game_state}, {controller_action}")
            except Exception as e:
                print(f"⚠️ Error recording game state and action: {e}")
                debug_log(traceback.format_exc())
                continue

            # Save frame periodically
            save_counter += 1
            if save_counter >= save_interval:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                filename = os.path.join(frame_path, f"frame_{timestamp}.jpg")
                cv2.imwrite(filename, img)
                print(f"📸 Frame saved: {filename}")
                save_counter = 0

            frame_counter += 1
            last_frame_time = datetime.now()

        except Exception as e:
            print(f"❌ Unexpected error during frame capture: {e}")
            debug_log(traceback.format_exc())
            await asyncio.sleep(0.5)

        await asyncio.sleep(0.5)

    # Save session data at the end
    data_collector.save_session()
    print("🛑 Frame capture ended: receiver no longer available.")