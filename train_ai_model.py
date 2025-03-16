### Mutti Working




# pip install numpy scikit-learn torch


import os, glob, json, random
import numpy as np
from sklearn.model_selection import train_test_split
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

# Parameters
DATA_DIR = os.path.join("training_data", "fifa")
BATCH_SIZE = 32
EPOCHS = 10
LEARNING_RATE = 0.001

# Data Loading and Preprocessing
def load_data(data_dir):
    data_list = []
    file_paths = glob.glob(os.path.join(data_dir, "*.json"))
    for fp in file_paths:
        with open(fp) as f:
            session = json.load(f)
            data_list.extend(session)
    return data_list

def preprocess_data(record):
    # Convert game_state into a numeric feature vector
    game_state = record["game_state"]
    features = []
    # Flatten ball_position (assumed to be a list of two numbers)
    features.extend(game_state.get("ball_position", [0, 0]))
    # Flatten player_position (assumed to be a list of two numbers)
    features.extend(game_state.get("player_position", [0, 0]))
    # For opponent_positions, use the first opponent as an example
    opponent_positions = game_state.get("opponent_positions", [])
    if opponent_positions and isinstance(opponent_positions[0], (list, tuple)):
        features.extend(opponent_positions[0])
    else:
        features.extend([0, 0])
    # Add score as a feature
    features.append(float(game_state.get("score", 0)))
    # Encode possession as 1 (True) or 0 (False)
    features.append(1.0 if game_state.get("possession", False) else 0.0)
    # Encode game_phase as a numeric value
    phase = game_state.get("game_phase", "unknown")
    phase_mapping = {"first_half": 0.0, "second_half": 1.0, "unknown": -1.0}
    features.append(phase_mapping.get(phase, -1.0))

    # Process action as target value (assuming it's numeric). If not, adjust accordingly.
    action = record.get("action", 0)
    try:
        target = float(action)
    except:
        target = 0.0
    return np.array(features, dtype=np.float32), np.array([target], dtype=np.float32)

class FIFADataDataset(Dataset):
    def __init__(self, records):
        self.samples = [preprocess_data(r) for r in records]

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        features, target = self.samples[idx]
        return features, target

# Model Architecture: Simple feedforward neural network
class SimpleFIFAModel(nn.Module):
    def __init__(self, input_dim):
        super(SimpleFIFAModel, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 64),
            nn.ReLU(),
            nn.Linear(64, 1)  # Regression output for action
        )

    def forward(self, x):
        return self.net(x)

def train():
    # Load and preprocess the data
    data_records = load_data(DATA_DIR)
    random.shuffle(data_records)
    # Determine the input dimension from the first record
    features, _ = preprocess_data(data_records[0])
    input_dim = features.shape[0]

    # Split the data: 60% train, 20% validation, 20% test
    train_records, test_records = train_test_split(data_records, test_size=0.2, random_state=42)
    train_records, val_records = train_test_split(train_records, test_size=0.25, random_state=42)  # 0.25 of 80% = 20%
    train_dataset = FIFADataDataset(train_records)
    val_dataset = FIFADataDataset(val_records)
    test_dataset = FIFADataDataset(test_records)

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE)

    # Initialize model, loss function, and optimizer
    model = SimpleFIFAModel(input_dim)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)

    # Training Loop
    for epoch in range(EPOCHS):
        model.train()
        train_loss = 0.0
        for features_batch, targets_batch in train_loader:
            optimizer.zero_grad()
            outputs = model(features_batch)
            loss = criterion(outputs, targets_batch)
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * features_batch.size(0)
        train_loss /= len(train_loader.dataset)

        # Validation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for features_batch, targets_batch in val_loader:
                outputs = model(features_batch)
                loss = criterion(outputs, targets_batch)
                val_loss += loss.item() * features_batch.size(0)
        val_loss /= len(val_loader.dataset)
        print(f"Epoch {epoch+1}/{EPOCHS} - Train Loss: {train_loss:.4f} - Val Loss: {val_loss:.4f}")

    # Final Evaluation on Test Set
    model.eval()
    test_loss = 0.0
    with torch.no_grad():
        for features_batch, targets_batch in test_loader:
            outputs = model(features_batch)
            loss = criterion(outputs, targets_batch)
            test_loss += loss.item() * features_batch.size(0)
    test_loss /= len(test_loader.dataset)
    print(f"Test Loss: {test_loss:.4f}")

if __name__ == "__main__":
    train()
