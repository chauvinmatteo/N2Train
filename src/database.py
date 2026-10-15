import csv
import sqlite3
from datetime import datetime
from pathlib import Path

from fsrs import Card, Rating

from dates import to_iso

SCHEMA = '''
CREATE TABLE IF NOT EXISTS kanjis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    caractere TEXT NOT NULL UNIQUE,
    meaning TEXT NOT NULL,
    reading TEXT NOT NULL,
    card TEXT,              -- FSRS card as JSON, NULL while never studied
    due TEXT,               -- copy of the card due date, for the queries
    introduced_at TEXT      -- date of the first review
);
CREATE INDEX IF NOT EXISTS idx_kanjis_due ON kanjis(due);

CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kanji_id INTEGER NOT NULL REFERENCES kanjis(id),
    reviewed_at TEXT NOT NULL,
    question_type TEXT NOT NULL,
    correct INTEGER NOT NULL,
    rating INTEGER NOT NULL,
    duration_ms INTEGER
);
CREATE INDEX IF NOT EXISTS idx_reviews_date ON reviews(reviewed_at);
'''

ANSWER_COLUMNS = ("caractere", "meaning", "reading")


class Database:

    def __init__(self, path: Path | str) -> None:

        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA)

    def close(self) -> None:

        self.conn.close()

    def seed(self, csv_path: Path | str) -> int:

        with open(csv_path, encoding="utf-8", newline="") as file:
            reader = csv.reader(file)
            next(reader)
            rows = [(row[0], row[1], row[2]) for row in reader
                    if len(row) >= 3]

        with self.conn:
            before = self.conn.total_changes
            self.conn.executemany('''
                INSERT OR IGNORE INTO kanjis(caractere, meaning, reading)
                VALUES (?, ?, ?)
                ''', rows)
            return self.conn.total_changes - before

    def due_kanji(self, now: datetime, limit: int) -> list[dict]:

        rows = self.conn.execute('''
            SELECT * FROM kanjis
            WHERE card IS NOT NULL AND due <= ?
            ORDER BY due LIMIT ?
            ''', (to_iso(now), limit))
        return [dict(row) for row in rows]

    def new_kanji(self, limit: int) -> list[dict]:

        rows = self.conn.execute('''
            SELECT * FROM kanjis WHERE card IS NULL ORDER BY id LIMIT ?
            ''', (limit,))
        return [dict(row) for row in rows]

    def all_kanji(self) -> list[dict]:

        return [dict(row) for row in self.conn.execute(
            "SELECT * FROM kanjis ORDER BY id")]

    def count_due(self, now: datetime) -> int:

        return self.conn.execute('''
            SELECT COUNT(*) FROM kanjis WHERE card IS NOT NULL AND due <= ?
            ''', (to_iso(now),)).fetchone()[0]

    def count_new(self) -> int:

        return self.conn.execute(
            "SELECT COUNT(*) FROM kanjis WHERE card IS NULL").fetchone()[0]

    def count_introduced_since(self, since: datetime) -> int:

        return self.conn.execute('''
            SELECT COUNT(*) FROM kanjis WHERE introduced_at >= ?
            ''', (to_iso(since),)).fetchone()[0]

    def next_due(self) -> str | None:

        return self.conn.execute(
            "SELECT MIN(due) FROM kanjis WHERE card IS NOT NULL"
        ).fetchone()[0]

    def distractors(self, column: str, good_answer: str,
                    count: int = 3) -> list[str]:

        # The column name can't be a SQL parameter, so it is whitelisted
        if column not in ANSWER_COLUMNS:
            raise ValueError(f"Invalid column: {column}")
        rows = self.conn.execute(f'''
            SELECT DISTINCT {column} FROM kanjis WHERE {column} != ?
            ORDER BY RANDOM() LIMIT ?
            ''', (good_answer, count))
        return [row[0] for row in rows]

    def save_review(self, kanji_id: int, card: Card, question_type: str,
                    correct: bool, rating: Rating, reviewed_at: datetime,
                    duration_ms: int | None = None) -> None:

        with self.conn:
            self.conn.execute('''
                UPDATE kanjis
                SET card = ?, due = ?,
                    introduced_at = COALESCE(introduced_at, ?)
                WHERE id = ?
                ''', (card.to_json(), to_iso(card.due), to_iso(reviewed_at),
                      kanji_id))
            self.conn.execute('''
                INSERT INTO reviews(kanji_id, reviewed_at, question_type,
                                    correct, rating, duration_ms)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (kanji_id, to_iso(reviewed_at), question_type,
                      int(correct), int(rating), duration_ms))

    def review_dates(self) -> list[str]:

        return [row[0] for row in self.conn.execute(
            "SELECT reviewed_at FROM reviews")]

    def accuracy_since(self, since: datetime | None = None) -> tuple[int,
                                                                     int]:

        row = self.conn.execute('''
            SELECT COALESCE(SUM(correct), 0), COUNT(*) FROM reviews
            WHERE reviewed_at >= ?
            ''', (to_iso(since) if since else "",)).fetchone()
        return row[0], row[1]

    def most_missed(self, limit: int = 8) -> list[dict]:

        rows = self.conn.execute('''
            SELECT k.caractere, k.meaning, k.reading,
                   COUNT(*) AS misses
            FROM reviews r JOIN kanjis k ON k.id = r.kanji_id
            WHERE r.correct = 0
            GROUP BY k.id
            ORDER BY misses DESC, MAX(r.reviewed_at) DESC
            LIMIT ?
            ''', (limit,))
        return [dict(row) for row in rows]
