import random
import time
import logging
import sqlite3
from enum import Enum
from datetime import datetime
from typing import Optional, List
from colorama import init, Fore

# Initialize colorama for colorful terminal output
init(autoreset=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cup_game.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class Difficulty(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class GameMode(Enum):
    CLASSIC = "classic"
    TIMED = "timed"
    STREAK = "streak"


class DatabaseManager:
    """Handles all database operations for the Cup Game."""
    
    def __init__(self, db_path: str = "cup_game.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS game_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        difficulty TEXT NOT NULL,
                        game_mode TEXT NOT NULL,
                        wins INTEGER NOT NULL,
                        losses INTEGER NOT NULL,
                        duration_seconds REAL
                    )
                ''')
                conn.commit()
                logger.info("Database initialized successfully")
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    def save_game_session(self, difficulty: str, game_mode: str, wins: int, losses: int, duration: Optional[float] = None):
        """Save a completed game session to the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO game_sessions (difficulty, game_mode, wins, losses, duration_seconds)
                    VALUES (?, ?, ?, ?, ?)
                ''', (difficulty, game_mode, wins, losses, duration))
                conn.commit()
                logger.info(f"Game session saved: {wins}W-{losses}L, {difficulty}, {game_mode}")
        except sqlite3.Error as e:
            logger.error(f"Error saving game session: {e}")
            raise
    
    def get_statistics(self) -> dict:
        """Get game statistics from the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_sessions,
                        SUM(wins) as total_wins,
                        SUM(losses) as total_losses,
                        AVG(duration_seconds) as avg_duration,
                        difficulty,
                        game_mode
                    FROM game_sessions
                    GROUP BY difficulty, game_mode
                ''')
                results = cursor.fetchall()
                
                # Get overall stats
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_sessions,
                        SUM(wins) as total_wins,
                        SUM(losses) as total_losses,
                        AVG(duration_seconds) as avg_duration
                    FROM game_sessions
                ''')
                overall = cursor.fetchone()
                
                return {
                    'overall': {
                        'total_sessions': overall[0] or 0,
                        'total_wins': overall[1] or 0,
                        'total_losses': overall[2] or 0,
                        'avg_duration': overall[3] or 0
                    },
                    'by_category': results
                }
        except sqlite3.Error as e:
            logger.error(f"Error retrieving statistics: {e}")
            return {'overall': {'total_sessions': 0, 'total_wins': 0, 'total_losses': 0, 'avg_duration': 0}, 'by_category': []}


class CupGame:
    """Enhanced Cup Game with multiple difficulty levels and game modes."""
    
    def __init__(self, difficulty: Difficulty = Difficulty.EASY, game_mode: GameMode = GameMode.CLASSIC):
        self.difficulty = difficulty
        self.game_mode = game_mode
        self.wins = 0
        self.losses = 0
        self.start_time = None
        self.db_manager = DatabaseManager()
        
        # Configure game based on difficulty
        self.config = self._get_game_config()
        
        self.prizes = [
            "a Disney Cruise ticket",
            "a Ferrari",
            "a mansion in Beverly Hills",
            "a giraffe",
            "Jordan Air 1s",
            "a golden watch",
            "a private jet",
            "a treasure chest",
            "a magical sword",
            "a diamond ring"
        ]
        
        logger.info(f"Game initialized: {difficulty.value} difficulty, {game_mode.value} mode")
    
    def _get_game_config(self) -> dict:
        """Get game configuration based on difficulty level."""
        configs = {
            Difficulty.EASY: {
                'cups': ['left', 'right'],
                'shuffle_time': 2.0,
                'max_rounds': None
            },
            Difficulty.MEDIUM: {
                'cups': ['left', 'middle', 'right'],
                'shuffle_time': 1.5,
                'max_rounds': None
            },
            Difficulty.HARD: {
                'cups': ['left', 'middle-left', 'middle-right', 'right'],
                'shuffle_time': 1.0,
                'max_rounds': None
            }
        }
        
        if self.game_mode == GameMode.TIMED:
            configs[self.difficulty]['time_limit'] = 30  # 30 seconds
        elif self.game_mode == GameMode.STREAK:
            configs[self.difficulty]['max_rounds'] = 10
        
        return configs[self.difficulty]
    
    def show_intro(self):
        """Display game introduction and current settings."""
        try:
            print(Fore.CYAN + "|| Welcome to the Enhanced Cup Game ||")
            time.sleep(1)
            print(f"Difficulty: {self.difficulty.value.title()}")
            print(f"Game Mode: {self.game_mode.value.title()}")
            print(f"Cups: {len(self.config['cups'])}")
            
            if self.game_mode == GameMode.TIMED:
                print(f"Time Limit: {self.config.get('time_limit', 30)} seconds")
            elif self.game_mode == GameMode.STREAK:
                print(f"Target: {self.config.get('max_rounds', 10)} rounds")
            
            print("Try to guess which cup hides the prize!\n")
            logger.info("Game introduction displayed")
        except Exception as e:
            logger.error(f"Error displaying intro: {e}")
    
    def show_rules(self):
        """Display game rules based on current mode and difficulty."""
        try:
            print(Fore.YELLOW + "Game Rules:")
            print(f"- Choose a cup from: {', '.join(self.config['cups'])}")
            print("- Guess correctly to win a random prize.")
            print("- Incorrect guesses don't win anything.")
            
            if self.game_mode == GameMode.TIMED:
                print(f"- You have {self.config.get('time_limit', 30)} seconds total!")
            elif self.game_mode == GameMode.STREAK:
                print(f"- Try to win {self.config.get('max_rounds', 10)} rounds in a row!")
            
            print("- Your score will be tracked.\n")
            logger.info("Game rules displayed")
        except Exception as e:
            logger.error(f"Error displaying rules: {e}")
    
    def validate_choice(self, choice: str) -> bool:
        """Validate user's cup choice."""
        return choice.lower() in self.config['cups']
    
    def play_round(self) -> bool:
        """Play a single round. Returns True if game should continue, False to stop."""
        try:
            # Check time limit for timed mode
            if self.game_mode == GameMode.TIMED:
                elapsed = time.time() - self.start_time
                if elapsed >= self.config.get('time_limit', 30):
                    print(Fore.RED + "Time's up!")
                    return False
                remaining = self.config.get('time_limit', 30) - elapsed
                print(f"Time remaining: {remaining:.1f} seconds")
            
            prize_cup = random.choice(self.config['cups'])
            prize = random.choice(self.prizes)
            
            print(f"Available cups: {', '.join(self.config['cups'])}")
            user_choice = input("Choose a cup: ").lower().strip()
            
            while not self.validate_choice(user_choice):
                print(f"Invalid input. Choose from: {', '.join(self.config['cups'])}")
                user_choice = input("Choose a cup: ").lower().strip()
            
            time.sleep(0.5)
            print(Fore.MAGENTA + "Shuffling cups...")
            time.sleep(self.config['shuffle_time'])
            
            if user_choice == prize_cup:
                self.wins += 1
                print(Fore.GREEN + f"You guessed right! 🎉 You won {prize} in the {prize_cup} cup.")
                logger.info(f"Player won round: {user_choice} == {prize_cup}")
            else:
                self.losses += 1
                print(Fore.RED + f"Nope! The prize was in the {prize_cup} cup. Try again!")
                logger.info(f"Player lost round: {user_choice} != {prize_cup}")
                
                # In streak mode, end game on first loss
                if self.game_mode == GameMode.STREAK:
                    print(Fore.RED + "Streak broken! Game over.")
                    return False
            
            print(f"Current score: {self.wins} wins, {self.losses} losses\n")
            
            # Check if max rounds reached
            if self.config.get('max_rounds'):
                total_rounds = self.wins + self.losses
                if total_rounds >= self.config['max_rounds']:
                    return False
            
            return True
            
        except KeyboardInterrupt:
            print("\nGame interrupted by user.")
            logger.info("Game interrupted by user")
            return False
        except Exception as e:
            logger.error(f"Error in play_round: {e}")
            print(Fore.RED + "An error occurred during the round.")
            return False
    
    def show_summary(self):
        """Display game summary and save results."""
        try:
            duration = None
            if self.start_time:
                duration = time.time() - self.start_time
            
            print(Fore.CYAN + f"\nGame Over!")
            print(f"Final Score: {self.wins} wins, {self.losses} losses")
            
            if duration:
                print(f"Game Duration: {duration:.1f} seconds")
            
            if self.wins + self.losses > 0:
                win_rate = (self.wins / (self.wins + self.losses)) * 100
                print(f"Win Rate: {win_rate:.1f}%")
            
            # Save to database
            self.db_manager.save_game_session(
                self.difficulty.value,
                self.game_mode.value,
                self.wins,
                self.losses,
                duration
            )
            
            if duration is not None:
                logger.info(f"Game completed: {self.wins}W-{self.losses}L in {duration:.1f}s")
            else:
                logger.info(f"Game completed: {self.wins}W-{self.losses}L")
            
        except Exception as e:
            logger.error(f"Error showing summary: {e}")
    
    def show_statistics(self):
        """Display historical game statistics."""
        try:
            stats = self.db_manager.get_statistics()
            print(Fore.CYAN + "\n=== Game Statistics ===")
            
            overall = stats['overall']
            if overall['total_sessions'] > 0:
                print(f"Total Sessions: {overall['total_sessions']}")
                print(f"Total Wins: {overall['total_wins']}")
                print(f"Total Losses: {overall['total_losses']}")
                print(f"Overall Win Rate: {(overall['total_wins'] / (overall['total_wins'] + overall['total_losses']) * 100):.1f}%")
                if overall['avg_duration']:
                    print(f"Average Game Duration: {overall['avg_duration']:.1f} seconds")
            else:
                print("No game history found.")
            
        except Exception as e:
            logger.error(f"Error showing statistics: {e}")
            print("Error retrieving statistics.")
    
    def run(self):
        """Run the complete game session."""
        try:
            self.start_time = time.time()
            self.show_intro()
            
            if input("Would you like to see the rules? (y/n): ").lower().strip() == "y":
                self.show_rules()
            
            if input("Would you like to see your statistics? (y/n): ").lower().strip() == "y":
                self.show_statistics()
            
            print("\nStarting game...\n")
            
            while True:
                if not self.play_round():
                    break
                
                if self.game_mode == GameMode.CLASSIC:
                    again = input("Play another round? (y/n): ").lower().strip()
                    if again != "y":
                        break
            
            self.show_summary()
            
        except Exception as e:
            logger.error(f"Error running game: {e}")
            print(Fore.RED + "An unexpected error occurred.")


def select_difficulty() -> Difficulty:
    """Allow user to select game difficulty."""
    print("Select difficulty:")
    print("1. Easy (2 cups)")
    print("2. Medium (3 cups)")
    print("3. Hard (4 cups)")
    
    while True:
        try:
            choice = input("Enter choice (1-3): ").strip()
            if choice == "1":
                return Difficulty.EASY
            elif choice == "2":
                return Difficulty.MEDIUM
            elif choice == "3":
                return Difficulty.HARD
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")
        except Exception as e:
            logger.error(f"Error selecting difficulty: {e}")
            print("Invalid input. Please try again.")


def select_game_mode() -> GameMode:
    """Allow user to select game mode."""
    print("\nSelect game mode:")
    print("1. Classic (Play until you quit)")
    print("2. Timed (30 second time limit)")
    print("3. Streak (Win 10 rounds in a row)")
    
    while True:
        try:
            choice = input("Enter choice (1-3): ").strip()
            if choice == "1":
                return GameMode.CLASSIC
            elif choice == "2":
                return GameMode.TIMED
            elif choice == "3":
                return GameMode.STREAK
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")
        except Exception as e:
            logger.error(f"Error selecting game mode: {e}")
            print("Invalid input. Please try again.")


# Run the game
if __name__ == "__main__":
    try:
        print(Fore.CYAN + "=== Enhanced Cup Game ===\n")
        difficulty = select_difficulty()
        game_mode = select_game_mode()
        
        game = CupGame(difficulty, game_mode)
        game.run()
        
    except KeyboardInterrupt:
        print("\nThanks for playing!")
        logger.info("Game exited by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(Fore.RED + "An unexpected error occurred. Check the log file for details.")