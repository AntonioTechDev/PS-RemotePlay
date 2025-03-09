# 🎮 PS Remote Play - Complete Guide

This guide provides detailed instructions for using scripts to connect and manage PSN accounts with Remote Play using the `pyremoteplay` library.

---

## 📜 **Table of Contents**
1. [Prerequisites](#prerequisites)
2. [PSN Account Registration](#psn-account-registration)
3. [Linking an Account to a Console](#linking-an-account-to-a-console)
4. [Starting and Managing a Remote Play Session](#starting-and-managing-a-remote-play-session)
5. [Advanced Features](#advanced-features)
6. [Code Structure](#code-structure)
7. [Troubleshooting](#troubleshooting)

---

## 📌 **Prerequisites**
- Install Python 3.10.11.
- Install the required dependencies by running:
  ```sh
  pip install -r requirements.txt
  ```
- Have a valid PSN account and a PlayStation console compatible with Remote Play.
- Ensure the console is turned on and connected to the same network as the PC.

---

## 🎮 **PSN Account Registration**
📌 **Script to run:** `link_account.py`

> **Important Note**: This script only initializes the account in the `.pyremoteplay/.profile.json` file by creating a basic structure. The console linking will be done through the next script.

1. Run the command:
   ```sh
   python -m account_management.link_account
   ```
2. Follow the instructions to log in with your PSN account.
3. Copy the generated redirect URL and paste it into the console when prompted.
4. If everything is correct, the profile will be initialized in the `.pyremoteplay/.profile.json` file with a structure similar to:
   ```json
   "username": {
       "id": "base64_encoded_id",
       "hosts": {}
   }
   ```

---

## 🎮 **Linking an Account to a Console**
📌 **Script to run:** `connecting_account_to_console.py`

> **Important Note**: This script completes the registration process by actually linking the PSN account to the console and populating the data in the "hosts" section of the `.profile.json` file.

1. Ensure the console is turned on and Remote Play is enabled in the settings.
2. Run the command:
   ```sh
   python -m account_management.connecting_account_to_console
   ```
3. Select the PSN account registered in the previous step.
4. Enter the console's IP address (visible in the PlayStation's network settings).
5. Enter the PIN code shown in the console's **Remote Play** settings.
6. If everything is correct, the console will be registered in the `.pyremoteplay/.profile.json` file associated with the account, and the "hosts" section will be populated with all the necessary data:
   ```json
   "username": {
       "id": "base64_encoded_id",
       "hosts": {
           "MAC_ADDRESS": {
               "data": {
                   "AP-Ssid": "...",
                   "RP-Key": "...",
                   "Mac": "...",
                   "RegistKey": "...",
                   "Nickname": "...",
                   "IP": "..."
               },
               "type": "PS4"
           }
       }
   }
   ```

---

## 🎮 **Starting and Managing a Remote Play Session**
📌 **Script to run:** `session.py`

1. Run the command:
   ```sh
   python -m session.session
   ```
2. Select the PSN account you want to use for the session.
3. Select the console to connect to.
4. The system will perform a preliminary connection check and notify you of any issues.
5. Wait for the session to start correctly.
6. The session will capture video frames and automatically save them in the `frames/{user_name}` folder.
7. To end the session, press **CTRL+C** or close the terminal window.

---

## 🚀 **Advanced Features**

### 🔄 **Automatic Reconnection**
The system can now detect when the connection drops and automatically attempt to reconnect. This significantly increases Remote Play session stability, especially with unstable network connections.

### 📊 **Connection Monitoring**
A new monitoring module constantly checks:
- Console reachability (ping)
- Remote Play services availability
- Connection quality

In case of problems, the system displays warnings and takes corrective actions.

### 🎛️ **Dynamic Quality Adaptation**
The system monitors connection performance and stability, automatically adjusting:
- Video resolution
- Frame rate (fps)
- Stream quality

This ensures the best possible experience even under non-optimal network conditions.

### 📈 **Socket Optimizations**
Advanced network socket optimizations have been implemented to improve connection stability:
- Enlarged receive/send buffers
- Nagle algorithm disabled to reduce latency
- Aggressive keepalive configurations
- Optimized timeout handling

### 📁 **Improved Frame Management**
Frame capture and saving has been completely revamped:
- Asynchronous frame processing to avoid blocking
- Adaptive capture speed control
- Better system resource management
- Detailed capture statistics

### 📝 **Advanced Logging**
A comprehensive logging system has been implemented that records:
- Connection status
- Frame capture performance
- Detected errors and issues
- Reconnection attempts

Logs are saved in the `remote_play_session.log` file for easier debugging.

---

## 📂 **Code Structure**
The project is divided into multiple modules to improve maintainability.

```
📂 PS-SOFTWARE/script-TESTED
├── requirements.txt       # Required dependencies
├── readme.md            # Project documentation
├── remote_play_session.log # Remote Play session logs
├── 📂 account_management  # PSN account management
│   ├── __init__.py      # Initializes the module
│   ├── connecting_account_to_console.py  # Links PSN account to console
│   ├── link_account.py   # Registers PSN account in system
│   └── utils.py         # Account management utility functions
│
└── 📂 session           # Game session management
    ├── session.py       # Session startup and account/console selection
    ├── 📂 frames        # Contains captured session frames
    └── 📂 remote_play   # Remote Play session management modules
        ├── __init__.py   # Initializes the module
        ├── controller.py # Controls session gamepad
        ├── session_manager.py # Advanced Remote Play session management
        ├── frame_handler.py # Optimized frame capture and saving
        ├── network_monitor.py # Network connection monitoring
        └── utils.py      # Utility functions (e.g., folder cleanup)
```

---

## 📌 **Project Modules**
### 🔹 `session.py`
- **Description:** Main script to start the Remote Play session.
- **What it does:**  
  1. Displays registered accounts.  
  2. Allows console selection.  
  3. Performs a preliminary connection check.
  4. Starts the optimized session and begins frame capture.  
  5. Manages safe session closure.  

### 🔹 `remote_play/session_manager.py`
- **Description:** Manages the connection to the Remote Play session with advanced features.
- **What it does:**  
  - Creates and manages the connection with the console.  
  - Implements automatic reconnection.
  - Monitors connection status.
  - Dynamically adapts quality.
  - Manages the complete session lifecycle.

### 🔹 `remote_play/frame_handler.py`
- **Description:** Manages optimized frame capture and saving.
- **What it does:**  
  - Receives video frames from the QueueReceiver.
  - Processes frames asynchronously to avoid blocking.
  - Adapts capture speed based on load.
  - Optimizes saving quality.
  - Maintains detailed statistics.

### 🔹 `remote_play/network_monitor.py`
- **Description:** Advanced network connection monitoring.
- **What it does:**  
  - Checks console reachability.
  - Calculates ping and packet loss statistics.
  - Provides information on connection stability.
  - Offers both synchronous and asynchronous versions of functionalities.

### 🔹 `remote_play/controller.py`
- **Description:** Controls the session gamepad.
- **What it does:**  
  - Initializes the controller.  
  - Sends commands to the console.  

### 🔹 `remote_play/utils.py`
- **Description:** Utility functions.
- **What it does:**  
  - Deletes old frames before a new session.  
  - Manages folder cleanup.  

---

## 🛠 **Troubleshooting**
### 🔹 **Error: No video frames received**
- **Solution:** The system now automatically attempts to switch from h264 to HEVC. If the problem persists, ensure the codecs are correctly installed.

### 🔹 **PSN authentication error**
- **Solution:** Change the network card's MAC address and try again.

### 🔹 **Error: "Session not active"**
- **Solution:** The system now performs a preliminary connection check. If the problem persists, ensure the console is turned on and connected to the same network.

### 🔹 **Error: "No Status" during console linking**
- **Solution:** Ensure that:
  - The console is turned on and not in standby mode
  - The entered IP is correct and reachable (try pinging it)
  - Remote Play is enabled in the console settings
  - No firewalls are blocking the communication

### 🔹 **Frequent disconnections**
- **Solution:** The new system implements automatic reconnection and quality adaptation. If problems persist:
  1. Check network connection stability
  2. Manually reduce resolution to 540p in the `session_manager.py` file
  3. Ensure no other devices are saturating the network

### 🔹 **Poor performance or lost frames**
- **Solution:** The system now monitors performance and automatically adapts quality. If problems persist:
  1. Check available resources on the PC
  2. Close applications consuming network bandwidth
  3. Connect the PlayStation console via Ethernet cable instead of Wi-Fi

---

🚀 **The software is now even more stable, resilient and easy to use!** 🎮🔥







<!-- =============================================== -->