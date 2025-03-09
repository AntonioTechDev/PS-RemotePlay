# This file exports a function to:
# - Delete any existing frames saved from previous sessions.
# - Create a fresh directory to store the new session's frames.

import os
import shutil

FRAME_DIR = "frames"

def clean_frame_directory(user_name):
    """ Elimina i frame salvati della sessione precedente. """
    user_frame_path = os.path.join(FRAME_DIR, user_name)
    if os.path.exists(user_frame_path):
        shutil.rmtree(user_frame_path)
    os.makedirs(user_frame_path, exist_ok=True)
    return user_frame_path
