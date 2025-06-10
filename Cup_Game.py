import random

listOfChoices = ["left", "middle", "right"]
listOfPrizes = ["Disney Cruise ticket", "a Ferrari", "a mansion in Beverly Hills", "a giraffe", "Jordan Air 1s"]

def myIntro():
    print("|| Welcome to my Cup game. Please follow the instructions in order to play. ||")

def showPrizes():
    print("Here are the available prizes:")
    for prize in listOfPrizes:
        print(f"- {prize}")

def showRules():
    print("Here are the rules of the game:")
    print("- You must choose which cup you think the prize is in (left, middle, or right).")
    print("- If you guess correctly, you win the prize in the cup!")
    print("- If you guess incorrectly, you don't win anything :(")
    print("- You can play as many times as you want until you choose to stop. Keep in mind the winning cup will be switched each time.")

def Points():
    numWins = 0
    numLosses = 0
    while True:
        userSelect = input("Choose which cup you think the prize is in (left, middle, right): ").lower()
        prizeCup = random.choice(listOfChoices)
        bigPrize = random.choice(listOfPrizes)
        if userSelect == prizeCup:
            numWins += 1
            print(f"You guessed correctly. You won {bigPrize}!!! It was the {prizeCup} cup. \n")
        else: 
            numLosses += 1
            print(f"You lost!!! It was the {prizeCup}.\n")
        play_again = input("Would you like to play again? (y/n):").lower()
        if play_again == "n":
            print(f"You won {numWins} times and lost {numLosses} times. Thanks for playing!")
            return numWins, numLosses
            break

myIntro()
showRulesPrompt = input("Do you want to see the rules of the game? (y/n)").lower()
if showRulesPrompt == "y":
    showRules()

    begin = input("Would you like to play the Legendary Cup Game? (y/n):").lower()
    if begin != "y":
        userSelect
    Points()
while True:
    play_again = input("Are you sure you would like to quit the game? Saying 'n' will restart the game. (y/n): ").lower()
    if play_again == "n":
        Points()
    elif play_again == "y":
        print("Thanks for playing the game. Now get lost!")
        break