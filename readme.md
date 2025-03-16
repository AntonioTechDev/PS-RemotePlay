# 🎮 PS Remote Play - Complete Guide

This guide provides detailed instructions for using the scripts to connect and manage PSN accounts with Remote Play using the `pyremoteplay` library.

---

## 📜 **Table of Contents**
1. [Prerequisites](#prerequisites)
2. [Registering a PSN Account](#registering-a-psn-account)
3. [Linking an Account to a Console](#linking-an-account-to-a-console)
4. [Starting and Managing a Remote Play Session](#starting-and-managing-a-remote-play-session)
5. [Code Structure](#code-structure)
6. [Troubleshooting](#troubleshooting)

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

## 🎮 **Registering a PSN Account**
📌 **Script to run:** `link_account.py`

> **Important Note**: This script only initializes the account in the file `.pyremoteplay/.profile.json` by creating a basic structure. The actual linking to the console will occur in the next script.

1. Run the command:
   ```sh
   python -m account_management.link_account
   ```
2. Follow the instructions to log in with your PSN account.
3. Copy the generated redirect URL and paste it into the console when prompted.
4. If everything is correct, the profile will be initialized in the file `.pyremoteplay/.profile.json` with a structure similar to:
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

1. Ensure the console is on and that Remote Play is enabled in the settings.
2. Run the command:
   ```sh
   python -m account_management.connecting_account_to_console
   ```
3. Select the registered PSN account from the previous step.
4. Enter the IP address of the console (visible in the console's network settings).
5. Enter the PIN code shown in the console's **Remote Play** settings.
6. If everything goes well, the console will be registered in the `.pyremoteplay/.profile.json` file associated with the account, and the "hosts" section will be populated with all necessary data:
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
2. Select the PSN account you wish to use for the session.
3. Select the console to connect to.
4. If prompted, enter the console’s IP address.
5. Wait for the session to start successfully.
6. The session will automatically capture and save video frames.
7. To end the session, press **CTRL+C** or close the terminal window.

---

## 📂 **Code Structure**
The project is divided into multiple modules to enhance maintainability.

```
📂 PS-SOFTWARE/script-TESTED
│── requirements.txt       # Required dependencies
│── readme.md              # Project documentation
│── 📂 account_management   # PSN account management
│   │── __init__.py        # Module initialization
│   │── connecting_account_to_console.py  # Link a PSN account to a console
│   │── link_account.py     # Register a PSN account in the system
│   │── utils.py            # Utility functions for account management
│
│── 📂 session              # Game session management
│   │── session.py          # Start session and select account and console
│   │── 📂 Frames           # Contains frames captured from sessions
│   │── 📂 remote_play      # Modules for Remote Play session management
│       │── __init__.py      # Module initialization
│       │── controller.py    # Handles the session gamepad
│       │── session_manager.py  # Connection and management of the Remote Play session
│       │── frame_handler.py  # Captures and saves video frames
│       │── utils.py         # Utility functions (e.g., cleaning folders)
```

---

## 📌 **Project Modules**
### 🔹 `session.py`
- **Description:** Main script for starting the Remote Play session.
- **Functions:**  
  1. Displays registered accounts.  
  2. Allows selecting the console.  
  3. Initiates the session and begins capturing frames.  
  4. Manages session termination.  

### 🔹 `remote_play/session_manager.py`
- **Description:** Manages the connection to the Remote Play session.
- **Functions:**  
  - Establishes a connection to the console.  
  - Configures the video receiver.  
  - Handles safe termination of the session.  

### 🔹 `remote_play/controller.py`
- **Description:** Controls the session gamepad.
- **Functions:**  
  - Initializes the controller.  
  - Sends test commands to the console.  

### 🔹 `remote_play/frame_handler.py`
- **Description:** Manages video frame capture and saving.
- **Functions:**  
  - Receives video frames.  
  - Converts frames to images.  
  - Saves them in the directory `Frames/{username}`.  

### 🔹 `remote_play/utils.py`
- **Description:** Utility functions.
- **Functions:**  
  - Cleans up old frames before a new session.  
  - Manages folder cleaning routines.

---

## 🛠 **Troubleshooting**
### 🔹 **Error: No video frames received**
- **Solution:** Ensure that the codec `h264` is supported. If it isn’t, the system will attempt to use `HEVC`.

### 🔹 **Error: PSN Authentication error**
- **Solution:** Change the network card’s MAC address and try again.

### 🔹 **Error: "Session not active"**
- **Solution:** Verify that the console is on and connected to the network.

### 🔹 **Error: "No Status" when linking the console**
- **Solution:** Make sure:
  - The console is turned on and not in standby.
  - The entered IP is correct and reachable (try pinging it).
  - Remote Play is enabled in the console settings.
  - No firewall is blocking communication.

---

## Data Collection and Model Training Flow

1. **Data Collection:**
   - During a Remote Play session, `frame_handler.py` captures video frames from the console.
   - Each frame is processed by `FIFAStateDetector` to extract the current game state (e.g. ball position, player and opponent positions, score, possession, and game phase).
   - Simultaneously, the controller's actions (such as stick movements) are recorded.
   - Both the game state and controller action are saved as records by `FIFADataCollector` into JSON files inside the `training_data/fifa` directory.

2. **Supervised Model Training:**
   - The script `train_ai_model.py` loads the collected JSON data.
   - It pre-processes each record into a numeric feature vector (representing the game state) and an associated target value (the recorded action).
   - A simple feedforward neural network defined in `SimpleFIFAModel` is trained on this data using backpropagation and Mean Squared Error as the loss function.
   - Data is split into training, validation, and test sets to monitor performance during training.

3. **Reinforcement Learning:**
   - The file `reinforcement/training_agent.py` defines an RL agent with a policy network (`RLAgent`).
   - As the game is played, transitions (state, action, reward, next state) are stored in a replay buffer (`ReplayBuffer`).
   - The RL agent uses an epsilon-greedy policy for action selection and is periodically updated by sampling mini-batches from the replay buffer.
   - This training loop continuously refines the agent’s policy to maximize the expected reward based on game feedback.

4. **Overall Flow:**
   - Remote Play sessions continuously record gameplay data (frames, game states, and control inputs).
   - The collected data is used for both supervised learning and reinforcement learning approaches.
   - Combined, these methods allow you to train models that can predict optimal actions from game state features and improve over time based on gameplay rewards.

🚀 **Now the code is well-structured, documented, and ready for use!** 🎮🔥