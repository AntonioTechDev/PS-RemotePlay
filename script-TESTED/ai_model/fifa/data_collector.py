### Mutti Working


import json
from datetime import datetime
from pathlib import Path

class FIFADataCollector:
    def __init__(self, save_dir: str = "training_data/fifa"):
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.current_session = []
        
    def record_gameplay(self, game_state, human_action):
        """Record game state and human action pairs"""
        self.current_session.append({
            "timestamp": datetime.now().isoformat(),
            "game_state": {
                "ball_position": game_state.ball_position,
                "player_position": game_state.player_position,
                "opponent_positions": game_state.opponent_positions,
                "score": game_state.score,
                "possession": game_state.possession,
                "game_phase": game_state.game_phase
            },
            "action": human_action  # button press or stick movement
        })
    
    def record_rl_transition(self, game_state, human_action, reward, next_state):
        self.current_session.append({
            "timestamp": datetime.now().isoformat(),
            "game_state": {
                "ball_position": game_state.ball_position,
                "player_position": game_state.player_position,
                "opponent_positions": game_state.opponent_positions,
                "score": game_state.score,
                "possession": game_state.possession,
                "game_phase": game_state.game_phase
            },
            "action": human_action,
            "reward": reward,
            "next_state": {
                "ball_position": next_state.ball_position,
                "player_position": next_state.player_position,
                "opponent_positions": next_state.opponent_positions,
                "score": next_state.score,
                "possession": next_state.possession,
                "game_phase": next_state.game_phase
            }
        })
    
    def save_session(self):
        """Save collected data to disk."""
        filename = self.save_dir / f"fifa_session_{datetime.now():%Y%m%d_%H%M%S}.json"
        with open(filename, 'w') as f:
            json.dump(self.current_session, f, indent=2)
        self.current_session = []
        print(f"✅ Session data saved to {filename}")
