import cv2
import numpy as np
import torch
from torchvision import transforms
from dataclasses import dataclass
from pathlib import Path
import torch.serialization  # added import

@dataclass
class FIFAGameState:
    ball_position: tuple
    player_position: tuple
    opponent_positions: list
    score: tuple
    possession: str
    game_phase: str  # e.g., 'attack', 'defense', 'transition'

class FIFAStateDetector:
    def __init__(self):
        # Initialize an optional backup detector (e.g., background subtraction)
        self.ball_detector = cv2.createBackgroundSubtractorMOG2()
        # Load the pretrained model for ball detection using safe_globals
        model_path = Path(__file__).parent / "fifa_trained_model.pt"
        # Allowlist the required global from ultralytics if you trust the source.
        torch.serialization.add_safe_globals(["ultralytics.nn.tasks.DetectionModel"])
        self.ball_detection_model = torch.load(
            str(model_path),
            map_location=torch.device("cpu"),
            weights_only=False  # Set to False to load full model
        )
        self.ball_detection_model.eval()
        print("Initialized FIFAStateDetector")  # Debug print

    def detect_state(self, frame: np.ndarray) -> FIFAGameState:
        print("Starting state detection...")  # Debug print
        ball_pos = self._detect_ball(frame)
        print("Ball position detected:", ball_pos)
        
        player_pos = self._detect_player(frame)
        print("Player position detected:", player_pos)
        
        opponent_pos = self._detect_opponents(frame)
        print("Opponent positions detected:", opponent_pos)
        
        score = self._detect_score(frame)
        print("Score detected:", score)
        
        possession = self._detect_possession(frame)
        print("Possession detected:", possession)
        
        game_phase = self._determine_phase(ball_pos, player_pos, opponent_pos)
        print("Game phase determined:", game_phase)
        
        state = FIFAGameState(
            ball_position=ball_pos,
            player_position=player_pos,
            opponent_positions=opponent_pos,
            score=score,
            possession=possession,
            game_phase=game_phase
        )
        print("Final detected game state:", state)
        return state
    
    def _detect_ball(self, frame: np.ndarray) -> tuple:
        print("Detecting ball...")  # Debug print
        # Convert frame from BGR to RGB as required by the model
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Preprocess the frame; adjust resize dimensions as needed by your model
        preprocess = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
        ])
        input_tensor = preprocess(rgb_frame)
        input_tensor = input_tensor.unsqueeze(0)  # Add batch dimension
        # Forward pass through the pretrained model to get normalized (x, y) coordinates
        with torch.no_grad():
            output = self.ball_detection_model(input_tensor)
        ball_x = output[0, 0].item() * frame.shape[1]
        ball_y = output[0, 1].item() * frame.shape[0]
        return (int(ball_x), int(ball_y))
    
    def _detect_player(self, frame: np.ndarray) -> tuple:
        print("Detecting player... [placeholder]")  # Debug print
        return (100, 200)  # Dummy placeholder value
    
    def _detect_opponents(self, frame: np.ndarray) -> list:
        print("Detecting opponents... [placeholder]")  # Debug print
        return [(300, 400)]  # Dummy placeholder value
    
    def _detect_score(self, frame: np.ndarray) -> tuple:
        print("Extracting score... [placeholder]")  # Debug print
        return (0, 0)  # Dummy placeholder score
    
    def _detect_possession(self, frame: np.ndarray) -> str:
        print("Determining possession... [placeholder]")  # Debug print
        return "unknown"  # Dummy placeholder
    
    def _determine_phase(self, ball_pos: tuple, player_pos: tuple, opponent_pos: list) -> str:
        print("Determining game phase... [placeholder]")  # Debug print
        return "unknown"  # Dummy placeholder

if __name__ == "__main__":
    print("Running FIFAStateDetector test...")
    # Create a dummy black image for testing
    dummy_img = np.zeros((480, 640, 3), dtype=np.uint8)
    detector = FIFAStateDetector()
    state = detector.detect_state(dummy_img)
    print("Test complete. Detected state:")
    print(state)