#!/usr/bin/env python3
"""
Demo script to showcase the Enhanced Cup Game features.
This script demonstrates testing, web app startup, and basic functionality.
"""

import subprocess
import sys
import time
import webbrowser
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and display the result."""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    print(f"Running: {command}")
    print("-" * 60)
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ SUCCESS")
            if result.stdout:
                print("Output:")
                print(result.stdout)
        else:
            print("❌ FAILED")
            if result.stderr:
                print("Error:")
                print(result.stderr)
                
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("⏰ TIMEOUT - Command took too long")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def check_dependencies():
    """Check if required dependencies are installed."""
    print("🔍 Checking dependencies...")
    
    try:
        import flask
        import pytest
        import colorama
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Run: pip install -r requirements.txt")
        return False

def run_tests():
    """Run the test suite."""
    return run_command("python -m pytest test_cup_game.py -v", "Running Unit Tests")

def start_web_app():
    """Start the web application."""
    print("\n🌐 Starting Flask Web Application...")
    print("The web app will start on http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    
    try:
        # Give user a moment to read the message
        time.sleep(2)
        
        # Try to open browser automatically
        try:
            webbrowser.open('http://localhost:5000')
        except:
            pass
        
        # Start the Flask app
        subprocess.run([sys.executable, "web_app.py"], check=True)
        
    except KeyboardInterrupt:
        print("\n🛑 Web server stopped by user")
    except Exception as e:
        print(f"❌ Error starting web app: {e}")

def demo_cli_game():
    """Demonstrate the CLI version briefly."""
    print("\n🎮 CLI Game Demo")
    print("The command line version offers:")
    print("- Interactive difficulty selection")
    print("- Multiple game modes (Classic, Timed, Streak)")
    print("- Colorful terminal output")
    print("- Statistics tracking")
    print("- Comprehensive logging")
    print("\n💡 To play the CLI version, run: python cup_game_enhanced.py")

def show_project_structure():
    """Display the project structure."""
    print("\n📁 Project Structure:")
    print("-" * 40)
    
    files_to_show = [
        "Cup_Game.py",
        "cup_game_enhanced.py",
        "web_app.py", 
        "test_cup_game.py",
        "requirements.txt",
        "README.md",
        "templates/index.html"
    ]
    
    for file_path in files_to_show:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✅ {file_path:<25} ({size:,} bytes)")
        else:
            print(f"❌ {file_path:<25} (missing)")

def main():
    """Main demo function."""
    print("🏆 Enhanced Cup Game - Feature Demonstration")
    print("=" * 60)
    
    # Check current directory
    current_dir = Path.cwd()
    print(f"📍 Current directory: {current_dir}")
    
    # Show project structure
    show_project_structure()
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Please install dependencies first!")
        return
    
    # Run tests
    print("\n" + "="*60)
    print("🧪 TESTING PHASE")
    print("="*60)
    
    test_success = run_tests()
    
    if test_success:
        print("\n✅ All tests passed! The implementation is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
    
    # Demo CLI features
    demo_cli_game()
    
    # Offer to start web app
    print("\n" + "="*60)
    print("🌐 WEB APPLICATION")
    print("="*60)
    
    choice = input("\nWould you like to start the web application? (y/n): ").lower().strip()
    
    if choice == 'y':
        start_web_app()
    else:
        print("💡 To start the web app later, run: python web_app.py")
    
    print("\n🎉 Demo complete! Thank you for exploring the Enhanced Cup Game.")
    print("\n📚 Features implemented:")
    print("   ✅ Unit tests with pytest")
    print("   ✅ SQLite database for persistence")
    print("   ✅ Flask web application")
    print("   ✅ Error handling and logging")
    print("   ✅ Multiple difficulty levels and game modes")

if __name__ == "__main__":
    main()