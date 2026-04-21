import sqlite3
from typing import Any
from database import (init_database, get_all_kanji, kanji_due_data,
                      update_kanji_srs, seed_database)
from datetime import datetime, timedelta
from rich import print  # type: ignore[import-untyped]

database_name = 'n2train_kanji'
sqlite3.register_adapter(datetime, lambda d: d.strftime("%Y-%m-%d %H:%M:%S"))
SRS_INTERVALS = {
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
    kanjis: list[Any] = get_all_kanji(database_name)
    for k in kanjis:
        print(f"[bold green]Kanji :[/bold green] {k[1]} | [bold blue]"
              f"Sens :[/bold blue] {k[2]}")

    print("======================================")

    kanji_due: list[Any] = kanji_due_data(database_name)

    if not kanji_due:
        print("Nothing left to study!")

    for k in kanji_due:

        answer: str = input(f"Whats the meaning of {k[1]} ?"
                            "(press 'quit' to exit\n")
        clean_answer: str = answer.strip(" ")

        if clean_answer.lower() == 'quit':
            print("[bold yellow]Session is over, see you soon!")
            break

        if clean_answer == k[2]:
            print("[bold green]SUCCES")
            new_level = k[4] + 1
            delay: timedelta = SRS_INTERVALS.get(new_level, timedelta(days=30))
            new_date: datetime = datetime.now() + delay
            update_kanji_srs(database_name, new_level, new_date, k[1])

        else:
            print(f"[bold red]ERROR: The meaning is {k[2]}!!")
            new_level = 0
            new_date = datetime.now() + timedelta(minutes=5)
            update_kanji_srs(database_name, new_level, new_date, k[1])


if __name__ == "__main__":
    main()
