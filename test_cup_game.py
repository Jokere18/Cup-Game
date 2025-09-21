import pytest
import sqlite3
import tempfile
import os
from unittest.mock import patch, MagicMock
from cup_game_enhanced import CupGame, DatabaseManager, Difficulty, GameMode


class TestDatabaseManager:
    """Test cases for the DatabaseManager class."""
    
    def setup_method(self):
        """Setup method to create a temporary database for each test."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_manager = DatabaseManager(self.temp_db.name)
    
    def teardown_method(self):
        """Cleanup method to remove temporary database after each test."""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_database_initialization(self):
        """Test that database is properly initialized with required tables."""
        with sqlite3.connect(self.temp_db.name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='game_sessions'")
            assert cursor.fetchone() is not None
    
    def test_save_game_session(self):
        """Test saving a game session to the database."""
        self.db_manager.save_game_session("easy", "classic", 5, 3, 120.5)
        
        with sqlite3.connect(self.temp_db.name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM game_sessions")
            session = cursor.fetchone()
            
            assert session is not None
            assert session[2] == "easy"  # difficulty
            assert session[3] == "classic"  # game_mode
            assert session[4] == 5  # wins
            assert session[5] == 3  # losses
            assert session[6] == 120.5  # duration
    
    def test_get_statistics_empty_database(self):
        """Test getting statistics from an empty database."""
        stats = self.db_manager.get_statistics()
        
        assert stats['overall']['total_sessions'] == 0
        assert stats['overall']['total_wins'] == 0
        assert stats['overall']['total_losses'] == 0
        assert stats['overall']['avg_duration'] == 0
        assert stats['by_category'] == []
    
    def test_get_statistics_with_data(self):
        """Test getting statistics from a database with game sessions."""
        # Add test data
        self.db_manager.save_game_session("easy", "classic", 3, 2, 100.0)
        self.db_manager.save_game_session("medium", "timed", 5, 1, 30.0)
        self.db_manager.save_game_session("easy", "classic", 2, 3, 150.0)
        
        stats = self.db_manager.get_statistics()
        
        assert stats['overall']['total_sessions'] == 3
        assert stats['overall']['total_wins'] == 10
        assert stats['overall']['total_losses'] == 6
        assert len(stats['by_category']) == 2  # Two different difficulty/mode combinations
    
    def test_database_error_handling(self):
        """Test that database errors are properly handled."""
        # Try to use a non-existent directory for database
        with pytest.raises(sqlite3.Error):
            DatabaseManager("/non_existent_path/test.db")


class TestCupGame:
    """Test cases for the CupGame class."""
    
    def setup_method(self):
        """Setup method to create a game instance for each test."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Mock the DatabaseManager to use our temp database
        with patch('cup_game_enhanced.DatabaseManager') as mock_db:
            mock_db.return_value = DatabaseManager(self.temp_db.name)
            self.game = CupGame(Difficulty.EASY, GameMode.CLASSIC)
    
    def teardown_method(self):
        """Cleanup method to remove temporary database after each test."""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_game_initialization(self):
        """Test that the game is properly initialized."""
        assert self.game.difficulty == Difficulty.EASY
        assert self.game.game_mode == GameMode.CLASSIC
        assert self.game.wins == 0
        assert self.game.losses == 0
        assert len(self.game.config['cups']) == 2  # Easy mode has 2 cups
    
    def test_game_config_easy(self):
        """Test game configuration for easy difficulty."""
        game = CupGame(Difficulty.EASY, GameMode.CLASSIC)
        assert len(game.config['cups']) == 2
        assert game.config['shuffle_time'] == 2.0
    
    def test_game_config_medium(self):
        """Test game configuration for medium difficulty."""
        game = CupGame(Difficulty.MEDIUM, GameMode.CLASSIC)
        assert len(game.config['cups']) == 3
        assert game.config['shuffle_time'] == 1.5
    
    def test_game_config_hard(self):
        """Test game configuration for hard difficulty."""
        game = CupGame(Difficulty.HARD, GameMode.CLASSIC)
        assert len(game.config['cups']) == 4
        assert game.config['shuffle_time'] == 1.0
    
    def test_game_config_timed_mode(self):
        """Test game configuration for timed mode."""
        game = CupGame(Difficulty.MEDIUM, GameMode.TIMED)
        assert 'time_limit' in game.config
        assert game.config['time_limit'] == 30
    
    def test_game_config_streak_mode(self):
        """Test game configuration for streak mode."""
        game = CupGame(Difficulty.MEDIUM, GameMode.STREAK)
        assert 'max_rounds' in game.config
        assert game.config['max_rounds'] == 10
    
    def test_validate_choice_valid(self):
        """Test choice validation with valid inputs."""
        assert self.game.validate_choice("left") is True
        assert self.game.validate_choice("right") is True
    
    def test_validate_choice_invalid(self):
        """Test choice validation with invalid inputs."""
        assert self.game.validate_choice("middle") is False  # Easy mode only has left/right
        assert self.game.validate_choice("invalid") is False
        assert self.game.validate_choice("") is False
    
    def test_validate_choice_case_insensitive(self):
        """Test that choice validation is case insensitive."""
        assert self.game.validate_choice("LEFT") is True
        assert self.game.validate_choice("Right") is True
        assert self.game.validate_choice("LeFt") is True
    
    @patch('random.choice')
    @patch('builtins.input')
    @patch('time.sleep')
    @patch('builtins.print')
    def test_play_round_win(self, mock_print, mock_sleep, mock_input, mock_choice):
        """Test a winning round."""
        mock_choice.side_effect = ["left", "a Ferrari"]  # prize_cup, prize
        mock_input.return_value = "left"
        
        result = self.game.play_round()
        
        assert result is True
        assert self.game.wins == 1
        assert self.game.losses == 0
    
    @patch('random.choice')
    @patch('builtins.input')
    @patch('time.sleep')
    @patch('builtins.print')
    def test_play_round_loss(self, mock_print, mock_sleep, mock_input, mock_choice):
        """Test a losing round."""
        mock_choice.side_effect = ["right", "a Ferrari"]  # prize_cup, prize
        mock_input.return_value = "left"
        
        result = self.game.play_round()
        
        assert result is True
        assert self.game.wins == 0
        assert self.game.losses == 1
    
    @patch('random.choice')
    @patch('builtins.input')
    @patch('time.sleep')
    @patch('builtins.print')
    def test_play_round_invalid_then_valid_input(self, mock_print, mock_sleep, mock_input, mock_choice):
        """Test handling of invalid input followed by valid input."""
        mock_choice.side_effect = ["left", "a Ferrari"]
        mock_input.side_effect = ["invalid", "middle", "left"]  # invalid, then invalid for easy mode, then valid
        
        result = self.game.play_round()
        
        assert result is True
        assert mock_input.call_count == 3
    
    @patch('time.time')
    @patch('random.choice')
    @patch('builtins.input')
    @patch('time.sleep')
    @patch('builtins.print')
    def test_timed_mode_time_limit(self, mock_print, mock_sleep, mock_input, mock_choice, mock_time):
        """Test that timed mode respects time limits."""
        game = CupGame(Difficulty.EASY, GameMode.TIMED)
        game.start_time = 0  # Set start time
        
        mock_time.return_value = 35  # 35 seconds elapsed, over the 30 second limit
        
        result = game.play_round()
        
        assert result is False  # Game should end due to time limit
    
    @patch('random.choice')
    @patch('builtins.input')
    @patch('time.sleep')
    @patch('builtins.print')
    def test_streak_mode_loss_ends_game(self, mock_print, mock_sleep, mock_input, mock_choice):
        """Test that streak mode ends on first loss."""
        game = CupGame(Difficulty.EASY, GameMode.STREAK)
        
        mock_choice.side_effect = ["right", "a Ferrari"]  # User chooses left, prize is in right
        mock_input.return_value = "left"
        
        result = game.play_round()
        
        assert result is False  # Game should end due to loss in streak mode
        assert game.losses == 1
    
    def test_show_intro_no_exception(self):
        """Test that show_intro method doesn't raise exceptions."""
        with patch('builtins.print'):
            with patch('time.sleep'):
                try:
                    self.game.show_intro()
                except Exception as e:
                    pytest.fail(f"show_intro raised an exception: {e}")
    
    def test_show_rules_no_exception(self):
        """Test that show_rules method doesn't raise exceptions."""
        with patch('builtins.print'):
            try:
                self.game.show_rules()
            except Exception as e:
                pytest.fail(f"show_rules raised an exception: {e}")
    
    @patch('builtins.print')
    def test_show_summary_saves_session(self, mock_print):
        """Test that show_summary saves the game session."""
        self.game.wins = 3
        self.game.losses = 2
        
        # Mock the database manager's save method
        with patch.object(self.game.db_manager, 'save_game_session') as mock_save:
            self.game.show_summary()
            
            # Verify the save method was called with correct game data
            mock_save.assert_called_once()
            call_args = mock_save.call_args[0]
            
            assert call_args[0] == self.game.difficulty.value  # difficulty
            assert call_args[1] == self.game.game_mode.value   # game_mode
            assert call_args[2] == 3                          # wins
            assert call_args[3] == 2                          # losses
            # Duration can be None or a number, we don't need to test exact value


class TestGameSelectionFunctions:
    """Test cases for game selection functions."""
    
    @patch('builtins.input')
    def test_select_difficulty_easy(self, mock_input):
        """Test selecting easy difficulty."""
        mock_input.return_value = "1"
        
        from cup_game_enhanced import select_difficulty
        result = select_difficulty()
        
        assert result == Difficulty.EASY
    
    @patch('builtins.input')
    def test_select_difficulty_medium(self, mock_input):
        """Test selecting medium difficulty."""
        mock_input.return_value = "2"
        
        from cup_game_enhanced import select_difficulty
        result = select_difficulty()
        
        assert result == Difficulty.MEDIUM
    
    @patch('builtins.input')
    def test_select_difficulty_hard(self, mock_input):
        """Test selecting hard difficulty."""
        mock_input.return_value = "3"
        
        from cup_game_enhanced import select_difficulty
        result = select_difficulty()
        
        assert result == Difficulty.HARD
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_select_difficulty_invalid_then_valid(self, mock_print, mock_input):
        """Test handling invalid input then valid input for difficulty selection."""
        mock_input.side_effect = ["4", "invalid", "1"]
        
        from cup_game_enhanced import select_difficulty
        result = select_difficulty()
        
        assert result == Difficulty.EASY
        assert mock_input.call_count == 3
    
    @patch('builtins.input')
    def test_select_game_mode_classic(self, mock_input):
        """Test selecting classic game mode."""
        mock_input.return_value = "1"
        
        from cup_game_enhanced import select_game_mode
        result = select_game_mode()
        
        assert result == GameMode.CLASSIC
    
    @patch('builtins.input')
    def test_select_game_mode_timed(self, mock_input):
        """Test selecting timed game mode."""
        mock_input.return_value = "2"
        
        from cup_game_enhanced import select_game_mode
        result = select_game_mode()
        
        assert result == GameMode.TIMED
    
    @patch('builtins.input')
    def test_select_game_mode_streak(self, mock_input):
        """Test selecting streak game mode."""
        mock_input.return_value = "3"
        
        from cup_game_enhanced import select_game_mode
        result = select_game_mode()
        
        assert result == GameMode.STREAK


class TestIntegration:
    """Integration tests for the complete game flow."""
    
    def setup_method(self):
        """Setup method for integration tests."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
    
    def teardown_method(self):
        """Cleanup method for integration tests."""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    @patch('cup_game_enhanced.DatabaseManager')
    @patch('random.choice')
    @patch('builtins.input')
    @patch('time.sleep')
    @patch('time.time')
    @patch('builtins.print')
    def test_complete_game_flow(self, mock_print, mock_time, mock_sleep, mock_input, mock_choice, mock_db_class):
        """Test a complete game flow from start to finish."""
        # Setup mocks
        mock_db = DatabaseManager(self.temp_db.name)
        mock_db_class.return_value = mock_db
        
        mock_time.return_value = 20  # Fixed time for duration calculation
        mock_choice.side_effect = ["left", "a Ferrari", "right", "a giraffe"]  # Two rounds
        mock_input.side_effect = [
            "n",  # Don't show rules
            "n",  # Don't show statistics
            "left",  # First round choice (will win since prize is also "left")
            "y",  # Play again
            "left",  # Second round choice (will lose since prize is "right")
            "n"   # Don't play again
        ]
        
        game = CupGame(Difficulty.EASY, GameMode.CLASSIC)
        game.run()
        
        # Verify game state (first round wins, second round loses)
        assert game.wins == 1  # Won first round
        assert game.losses == 1  # Lost second round
        
        # Verify database interaction
        stats = mock_db.get_statistics()
        assert stats['overall']['total_sessions'] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])