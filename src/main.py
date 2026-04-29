import sqlite3
import random
import os
from typing import Any
from database import (init_database, kanji_due_data, update_kanji_srs,
                      seed_database, get_random_choice)
from datetime import datetime, timedelta
from rich import print  # type: ignore[import-untyped]

database_name = 'n2train_kanji'
sqlite3.register_adapter(datetime, lambda d: d.strftime("%Y-%m-%d %H:%M:%S"))
SRS_INTERVALS: dict[int, timedelta] = {
    1: timedelta(hours=4),
    2: timedelta(hours=8),
    3: timedelta(days=1),
    4: timedelta(days=2),
    5: timedelta(days=7),
    6: timedelta(days=14),
    7: timedelta(days=30)
}


def launch_session(database_name) -> None:

    questions_nb = int(input("Number of question: "))

    print()

    kanji_due: list[Any] = kanji_due_data(database_name)[:questions_nb]
    random.shuffle(kanji_due)

    if not kanji_due:
        print("Nothing left to study!")
    for k in kanji_due:
        print("")
        question_type = random.choice(["meaning", "caractere", "reading"])

        if question_type == "meaning":
            title = "[bold blue]==========意味==========\n"
            good_answer = k[2]
            question = f"\nWhats the meaning of {k[1]} ?"
            index_wrong = 2

        elif question_type == "caractere":
            title = "[bold blue]==========書き方==========\n"
            good_answer = k[1]
            question = f"\nWhats the caractere for {k[2]}"
            index_wrong = 1

        else:
            title = "[bold blue]==========読み方==========\n"
            good_answer = k[3]
            question = f"\nWhats the reading of {k[1]}"
            index_wrong = 3

        os.system("clear")
        wrong_answer = get_random_choice(database_name, k[1])
        choices = []
        choices.append(good_answer)
        for wk in wrong_answer:
            choices.append(wk[index_wrong])
        random.shuffle(choices)
        print(title)
        for number, choice in enumerate(choices, 1):
            print(f"{number}: {choice}")

        answer: str = input(f"{question} ('quit' to exit)\n")

        if answer.lower() in ['quit', 'q']:
            print("[bold yellow]Session over, see you soon!")
            break

        try:
            chosen_number = int(answer)

            if chosen_number < 1 or chosen_number > len(choices):
                raise ValueError()

            clean_nbr = int(answer) - 1
            player_answer = choices[clean_nbr]

            if player_answer == good_answer:
                print("[bold green]SUCCES")
                with open("answer_sheets.txt", "a", encoding="utf=8") as f:
                    f.write(f"[{datetime.now()}] Kanji: {k[1]} | "
                            "Result: Succes\n")
                new_level = k[4] + 1
                delay: timedelta = SRS_INTERVALS.get(new_level,
                                                     timedelta(days=30))
                new_date: datetime = datetime.now() + delay
                update_kanji_srs(database_name, new_level, new_date, k[1])

            else:
                print(f"[bold red]ERROR: The answer is {good_answer}!")
                with open("answer_sheets.txt", "a", encoding="utf=8") as f:
                    f.write(f"[{datetime.now()}] Kanji: {k[1]} | "
                            "Result: Failed\n")
                new_level = 0
                new_date = datetime.now() + timedelta(minutes=5)
                update_kanji_srs(database_name, new_level, new_date, k[1])
        except (ValueError, IndexError):
            print("[bold red]Error: wrong input, counted as a mistake!")
        input("\nPress enter to continue...")


def main() -> None:

    init_database(database_name)
    seed_database(database_name, "n2_kanji.csv")

    while True:
        os.system("clear")
        print("\n======================================")
        print("[bold green]              Main Menu                ")
        print("======================================")
        print("1. [bold blue]Launch training session!")
        print("2. [bold blue]See your statistics! (WIP)")
        print("3. [bold blue]Exit")

        choice = input("What do you want to do? (1/2/3): ")

        if choice == "1":
            launch_session(database_name)

        elif choice == "2":
            print("[bold yellow]This is still a work in progress...")

        elif choice == "3" or choice.lower() in ['q', 'quit']:
            print("[bold yellow]Exiting...")
            break

        else:
            print("[bold red]Error: invalid choice, try again!")


if __name__ == "__main__":
    main()
