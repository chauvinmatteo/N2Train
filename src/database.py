import sqlite3
import csv
from datetime import datetime


def init_database(database_name):

    conn: sqlite3.Connection = sqlite3.connect(database_name)
    c = conn.cursor()
    request = ('''
    CREATE TABLE IF NOT EXISTS kanjis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        caractere TEXT NOT NULL UNIQUE,
        meaning TEXT NOT NULL,
        reading TEXT,
        srs_stage INTEGER,
        next_review TEXT
    )
''')

    c.execute(request)
    conn.commit()
    conn.close()


def add_kanji(database, kanji_data) -> bool:

    added = False
    conn: sqlite3.Connection = sqlite3.connect(database)
    c = conn.cursor()
    request = ('''
    INSERT OR IGNORE INTO kanjis(caractere, meaning, reading, srs_stage,
               next_review) VALUES (?, ?, ?, ?, ?)
               ''')

    c.execute(request, kanji_data)
    conn.commit()
    added = True
    conn.close()
    return added


def get_all_kanji(database):

    conn = sqlite3.connect(database)
    c = conn.cursor()
    request = ("SELECT * FROM kanjis")
    c.execute(request)
    k_data = c.fetchall()
    conn.close()
    return k_data


def kanji_due_data(database):

    conn = sqlite3.connect(database)
    c = conn.cursor()
    request = ("SELECT * FROM kanjis WHERE next_review <= ?")
    c.execute(request, (datetime.now(),))
    k_data = c.fetchall()
    conn.close()
    return k_data


def update_kanji_srs(database, new_stage, new_date, caractere):

    conn = sqlite3.connect(database)
    c = conn.cursor()
    request = ('''
    UPDATE kanjis
    SET srs_stage = ?, next_review = ?
    WHERE caractere = ?
    ''')
    c.execute(request, (new_stage, new_date, caractere))
    conn.commit()
    conn.close()


def seed_database(database, csv_filepath):

    with open(csv_filepath, mode="r", encoding="utf-8") as file:
        reader = csv.reader(file)
        next(reader)
        for row in reader:
            caractere: str = row[0]
            meaning: str = row[1]
            reading: str = row[2]
            level = 0
            learn_date = datetime.now()
            kanji_data: tuple = (caractere, meaning, reading,
                                 level, learn_date)
            add_kanji(database, kanji_data)
    print("Finished adding all kanji")


def get_random_choice(database, current_kanji):

    conn = sqlite3.connect(database)
    c = conn.cursor()
    request = ('''
    SELECT * FROM kanjis WHERE caractere != ?
    ORDER BY RANDOM() LIMIT 3       
    ''')
    c.execute(request, (current_kanji,))

    distractor = c.fetchall()
    c.close()
    return distractor