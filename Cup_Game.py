import random
import time
from colorama import init, Fore

# Initialize colorama for colorful terminal output
init(autoreset=True)


class CupGame:
    def __init__(self):
        self.choices = ["left", "middle", "right"]
        self.prizes = [
            "a Disney Cruise ticket",
            "a Ferrari",
            "a mansion in Beverly Hills",
            "a giraffe",
            "Jordan Air 1s"
        ]
        self.wins = 0
        self.losses = 0

    def show_intro(self):
        print(Fore.CYAN + "|| Welcome to the Legendary Cup Game ||")
        time.sleep(1)
        print("Try to guess which cup hides the prize!\n")

    def show_rules(self):
        print(Fore.YELLOW + "Game Rules:")
        print("- Choose a cup: left, middle, or right.")
        print("- Guess correctly to win a random prize.")
        print("- Incorrect guesses don't win anything.")
        print("- Your score will be tracked.\n")

    def validate_choice(self, choice):
        return choice in self.choices

    def play_round(self):
        prize_cup = random.choice(self.choices)
        prize = random.choice(self.prizes)
        user_choice = input("Choose a cup (left, middle, right): ").lower()

        while not self.validate_choice(user_choice):
            user_choice = input("Invalid input. Choose left, middle, or right: ").lower()

        time.sleep(0.5)
        print(Fore.MAGENTA + "Shuffling cups...")
        time.sleep(1)

        if user_choice == prize_cup:
            self.wins += 1
            print(Fore.GREEN + f"You guessed right! 🎉 You won {prize} in the {prize_cup} cup.\n")
        else:
            self.losses += 1
            print(Fore.RED + f"Nope! The prize was in the {prize_cup} cup. Try again!\n")

    def show_summary(self):
        print(Fore.CYAN + f"\nGame Over. You won {self.wins} time(s) and lost {self.losses} time(s).")
        self.save_score()

    def save_score(self):
        with open("score_history.txt", "a") as f:
            f.write(f"Wins: {self.wins}, Losses: {self.losses}\n")

    def run(self):
        self.show_intro()
        if input("Would you like to see the rules? (y/n): ").lower() == "y":
            self.show_rules()

        while True:
            self.play_round()
            again = input("Play again? (y/n): ").lower()
            if again != "y":
                break

        self.show_summary()


# Run the game
if __name__ == "__main__":
    game = CupGame()
    game.run()
