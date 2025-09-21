from flask import Flask, render_template, request, jsonify, session
import random
import time
from datetime import datetime
from cup_game_enhanced import DatabaseManager, Difficulty, GameMode
import logging

app = Flask(__name__)
app.secret_key = 'cup_game_secret_key_change_in_production'  # Change this in production!

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database
db_manager = DatabaseManager('web_cup_game.db')


@app.route('/')
def index():
    """Main game page."""
    return render_template('index.html')


@app.route('/api/start_game', methods=['POST'])
def start_game():
    """Start a new game session."""
    try:
        data = request.get_json()
        difficulty = data.get('difficulty', 'easy')
        game_mode = data.get('game_mode', 'classic')
        
        # Validate inputs
        if difficulty not in ['easy', 'medium', 'hard']:
            return jsonify({'error': 'Invalid difficulty'}), 400
        if game_mode not in ['classic', 'timed', 'streak']:
            return jsonify({'error': 'Invalid game mode'}), 400
        
        # Configure game based on difficulty
        game_config = {
            'easy': {'cups': ['left', 'right'], 'shuffle_time': 2.0},
            'medium': {'cups': ['left', 'middle', 'right'], 'shuffle_time': 1.5},
            'hard': {'cups': ['left', 'middle-left', 'middle-right', 'right'], 'shuffle_time': 1.0}
        }
        
        config = game_config[difficulty].copy()
        
        # Add mode-specific configuration
        if game_mode == 'timed':
            config['time_limit'] = 30
        elif game_mode == 'streak':
            config['max_rounds'] = 10
        
        # Initialize session data
        session['game_active'] = True
        session['difficulty'] = difficulty
        session['game_mode'] = game_mode
        session['config'] = config
        session['wins'] = 0
        session['losses'] = 0
        session['start_time'] = time.time()
        session['round_number'] = 1
        
        logger.info(f"Started new game: {difficulty} {game_mode}")
        
        return jsonify({
            'success': True,
            'config': config,
            'message': f'Started {difficulty} {game_mode} game!'
        })
        
    except Exception as e:
        logger.error(f"Error starting game: {e}")
        return jsonify({'error': 'Failed to start game'}), 500


@app.route('/api/play_round', methods=['POST'])
def play_round():
    """Play a single round of the game."""
    try:
        if not session.get('game_active'):
            return jsonify({'error': 'No active game'}), 400
        
        data = request.get_json()
        user_choice = data.get('choice', '').lower().strip()
        
        config = session['config']
        
        # Validate user choice
        if user_choice not in config['cups']:
            return jsonify({'error': 'Invalid cup choice'}), 400
        
        # Check time limit for timed mode
        if session['game_mode'] == 'timed':
            elapsed = time.time() - session['start_time']
            if elapsed >= config.get('time_limit', 30):
                session['game_active'] = False
                return jsonify({
                    'game_over': True,
                    'reason': 'Time limit exceeded',
                    'final_score': {'wins': session['wins'], 'losses': session['losses']}
                })
        
        # Generate random prize and cup
        prizes = [
            "a Disney Cruise ticket", "a Ferrari", "a mansion in Beverly Hills",
            "a giraffe", "Jordan Air 1s", "a golden watch", "a private jet",
            "a treasure chest", "a magical sword", "a diamond ring"
        ]
        
        prize_cup = random.choice(config['cups'])
        prize = random.choice(prizes)
        
        # Determine if player won
        won_round = user_choice == prize_cup
        
        if won_round:
            session['wins'] += 1
        else:
            session['losses'] += 1
            
            # In streak mode, end game on first loss
            if session['game_mode'] == 'streak':
                session['game_active'] = False
                duration = time.time() - session['start_time']
                db_manager.save_game_session(
                    session['difficulty'], 
                    session['game_mode'], 
                    session['wins'], 
                    session['losses'], 
                    duration
                )
                return jsonify({
                    'won_round': False,
                    'prize_cup': prize_cup,
                    'prize': prize,
                    'game_over': True,
                    'reason': 'Streak broken',
                    'final_score': {'wins': session['wins'], 'losses': session['losses']},
                    'duration': duration
                })
        
        session['round_number'] += 1
        
        # Check if max rounds reached
        if config.get('max_rounds'):
            total_rounds = session['wins'] + session['losses']
            if total_rounds >= config['max_rounds']:
                session['game_active'] = False
                duration = time.time() - session['start_time']
                db_manager.save_game_session(
                    session['difficulty'], 
                    session['game_mode'], 
                    session['wins'], 
                    session['losses'], 
                    duration
                )
                return jsonify({
                    'won_round': won_round,
                    'prize_cup': prize_cup,
                    'prize': prize,
                    'game_over': True,
                    'reason': 'Max rounds completed',
                    'final_score': {'wins': session['wins'], 'losses': session['losses']},
                    'duration': duration
                })
        
        # Calculate time remaining for timed mode
        time_remaining = None
        if session['game_mode'] == 'timed':
            elapsed = time.time() - session['start_time']
            time_remaining = max(0, config.get('time_limit', 30) - elapsed)
        
        logger.info(f"Round {session['round_number']}: {user_choice} vs {prize_cup}, won: {won_round}")
        
        return jsonify({
            'won_round': won_round,
            'prize_cup': prize_cup,
            'prize': prize,
            'current_score': {'wins': session['wins'], 'losses': session['losses']},
            'round_number': session['round_number'],
            'time_remaining': time_remaining,
            'shuffle_time': config['shuffle_time'],
            'game_over': False
        })
        
    except Exception as e:
        logger.error(f"Error playing round: {e}")
        return jsonify({'error': 'Failed to play round'}), 500


@app.route('/api/end_game', methods=['POST'])
def end_game():
    """End the current game session."""
    try:
        if not session.get('game_active'):
            return jsonify({'error': 'No active game'}), 400
        
        duration = time.time() - session['start_time']
        
        # Save game session to database
        db_manager.save_game_session(
            session['difficulty'], 
            session['game_mode'], 
            session['wins'], 
            session['losses'], 
            duration
        )
        
        final_score = {'wins': session['wins'], 'losses': session['losses']}
        
        # Clear session
        session['game_active'] = False
        
        logger.info(f"Game ended: {final_score}, duration: {duration:.1f}s")
        
        return jsonify({
            'success': True,
            'final_score': final_score,
            'duration': duration
        })
        
    except Exception as e:
        logger.error(f"Error ending game: {e}")
        return jsonify({'error': 'Failed to end game'}), 500


@app.route('/api/statistics')
def get_statistics():
    """Get game statistics."""
    try:
        stats = db_manager.get_statistics()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return jsonify({'error': 'Failed to get statistics'}), 500


@app.route('/api/game_status')
def get_game_status():
    """Get current game status."""
    try:
        if not session.get('game_active'):
            return jsonify({'game_active': False})
        
        time_remaining = None
        if session['game_mode'] == 'timed':
            elapsed = time.time() - session['start_time']
            time_remaining = max(0, session['config'].get('time_limit', 30) - elapsed)
            
            # Check if time expired
            if time_remaining <= 0:
                session['game_active'] = False
                duration = time.time() - session['start_time']
                db_manager.save_game_session(
                    session['difficulty'], 
                    session['game_mode'], 
                    session['wins'], 
                    session['losses'], 
                    duration
                )
                return jsonify({
                    'game_active': False,
                    'game_over': True,
                    'reason': 'Time expired'
                })
        
        return jsonify({
            'game_active': True,
            'difficulty': session['difficulty'],
            'game_mode': session['game_mode'],
            'current_score': {'wins': session['wins'], 'losses': session['losses']},
            'round_number': session['round_number'],
            'time_remaining': time_remaining,
            'config': session['config']
        })
        
    except Exception as e:
        logger.error(f"Error getting game status: {e}")
        return jsonify({'error': 'Failed to get game status'}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)