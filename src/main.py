import sqlite3
from typing import Any
from database import (init_database, add_kanji, get_all_kanji, kanji_due_data,
                      update_kanji_srs)
from datetime import datetime, timedelta
from rich import print # noqa

database_name = 'n2train_kanji'
sqlite3.register_adapter(datetime, lambda d: d.strftime("%Y-%m-%d %H:%M:%S"))


def main() -> None:
    print("Hello N2 Kanji Trainee!")
    init_database(database_name)
    future_date = datetime.now() + timedelta(days=365)
    kanji_0: tuple = ('権', 'pouvoir / droit', 'ケン', 0, future_date)
    kanji_1: tuple = ('順', 'ordre / tour', 'ジュン', 0, datetime.now())
    success: bool = add_kanji(database_name, kanji_0)
    add_kanji(database_name, kanji_1)
    if success:
        print("Successfully added the kanji!")
    kanjis: list[Any] = get_all_kanji(database_name)
    for k in kanjis:
        print(f"[bold green]Kanji :[/bold green] {k[1]} | [bold blue]"
              f"Sens :[/bold blue] {k[2]}")
    print("======================================")
    kanji_due: list[Any] = kanji_due_data(database_name)
    if not kanji_due:
        print("Nothing left to study!")
    for k in kanji_due:
        answer: str = input(f"Whats the meaning of {k[1]}\n")
        clean_answer: str = answer.strip(" ")
        if clean_answer == k[2]:
            print("[bold green]SUCCES")
            new_level = k[4] + 1
            new_date = datetime.now() + timedelta(days=1)
            update_kanji_srs(database_name, new_level, new_date, k[1])
        else:
            print(f"[bold red]ERROR: The meaning is {k[2]}!!")
            new_level = 0
            new_date = datetime.now() + timedelta(minutes=5)
            update_kanji_srs(database_name, new_level, new_date, k[1])


if __name__ == "__main__":
    main()
