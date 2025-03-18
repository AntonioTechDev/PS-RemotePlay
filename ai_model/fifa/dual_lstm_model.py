import torch
import torch.nn as nn
try:
    import torchvision.models as models
except ModuleNotFoundError:
    raise ModuleNotFoundError("torchvision is not installed. Please run 'pip install torchvision' to resolve this error.")

class DualLSTMModel(nn.Module):
    def __init__(self, input_dim, hidden_dim=64, num_layers=1, movement_output_dim=4, action_output_dim=4):
        super(DualLSTMModel, self).__init__()
        # CNN feature extractor using pretrained ResNet18 (removing the final fc layer)
        resnet = models.resnet18(pretrained=True)
        self.feature_extractor = nn.Sequential(*list(resnet.children())[:-1])  # output: (batch*seq_len, 512, 1, 1)
        self.feature_dim = 512

        # LSTM for movement prediction
        self.movement_lstm = nn.LSTM(self.feature_dim, hidden_dim, num_layers, batch_first=True)
        self.movement_fc = nn.Linear(hidden_dim, movement_output_dim)

        # LSTM for action prediction
        self.action_lstm = nn.LSTM(self.feature_dim, hidden_dim, num_layers, batch_first=True)
        self.action_fc = nn.Linear(hidden_dim, action_output_dim)

    def forward(self, x):
        # x shape: (batch, seq_len, channels, H, W)
        batch_size, seq_len, C, H, W = x.size()
        x = x.view(batch_size * seq_len, C, H, W)
        features = self.feature_extractor(x)  # shape: (batch*seq_len, 512, 1, 1)
        features = features.view(batch_size, seq_len, self.feature_dim)  # (batch, seq_len, 512)

        # Process through each LSTM
        movement_out, _ = self.movement_lstm(features)
        action_out, _ = self.action_lstm(features)
        # Use last time-step outputs for predictions
        movement_pred = self.movement_fc(movement_out[:, -1, :])
        action_pred = self.action_fc(action_out[:, -1, :])
        return movement_pred, action_pred
