import sqlite3
import random
from typing import Any
from database import (init_database, get_all_kanji, kanji_due_data,
                      update_kanji_srs, seed_database, get_random_choice)
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


def main() -> None:
    print("Hello N2 Kanji Trainee!")
    init_database(database_name)
    seed_database(database_name, "n2_kanji.csv")

    print("======================================")

    kanji_due: list[Any] = kanji_due_data(database_name)

    if not kanji_due:
        print("Nothing left to study!")
    for k in kanji_due:
        
        wrong_answer = get_random_choice(database_name, k[1])
        choices = []
        choices.append(k[2])
        for wk in wrong_answer:
            choices.append(wk[2])
        random.shuffle(choices)
        for number, choice in enumerate(choices, 1):
            print(f"{number}: {choice}")

        answer: str = input(f"Whats the meaning of {k[1]} ?"
                            "(press 'quit' to exit)\n")

        try:
            clean_answer= int(answer) - 1
            player_answer = choices[clean_answer]

            if clean_answer < 1 or len(clean_answer) > len(choices):
                raise ValueError()

            if player_answer == k[2]:
                print("[bold green]SUCCES")
                new_level = k[4] + 1
                delay: timedelta = SRS_INTERVALS.get(new_level, timedelta(days=30))
                new_date: datetime = datetime.now() + delay
                update_kanji_srs(database_name, new_level, new_date, k[1])

            else:
                print(f"[bold red]ERROR: The meaning is {k[2]}!")
                new_level = 0
                new_date = datetime.now() + timedelta(minutes=5)
                update_kanji_srs(database_name, new_level, new_date, k[1])
        except (ValueError, IndexError):
            print("[bold red]Error: wrong input, counted as a mistake!")


if __name__ == "__main__":
    main()
