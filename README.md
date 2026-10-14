# N2Train

Train JLPT N2 kanji from your terminal with a Spaced Repetition System (SRS).

N2Train quizzes you on ~370 N2 kanji with multiple-choice questions. Each correct
answer pushes the kanji further into the future; each mistake brings it back
almost immediately, so you spend your time on the kanji you actually struggle with.

> Status: work in progress. The statistics screen is not implemented yet.

## Features

- **Three question types**, picked at random for each kanji:
  - **意味** (meaning): given the kanji, pick its English meaning
  - **書き方** (writing): given the meaning, pick the right kanji
  - **読み方** (reading): given the kanji, pick its on/kun readings
- **Multiple choice**: 1 correct answer + 3 random distractors taken from the deck
- **SRS scheduling** stored in a local SQLite database
- **Answer log**: every answer is appended to `answer_sheets.txt`
- Colored terminal UI with [rich](https://github.com/Textualize/rich)

## Requirements

- Python **3.13+**
- [uv](https://docs.astral.sh/uv/) (it installs Python 3.13+ for you if needed)
- A Unix-like terminal (the app uses the `clear` command)

## Installation & usage

```bash
git clone <repo-url> N2Train
cd N2Train
make            # install dependencies, then launch the app
```

Or step by step:

```bash
make install    # uv sync
make run        # uv run python src/main.py
```

> Run the commands from the project root: the database, the CSV and the answer
> log are resolved relative to the current directory.

### In the app

```
======================================
              Main Menu
======================================
1. Launch training session!
2. See your statistics! (WIP)
3. Exit
```

1. Choose `1`, then enter how many questions you want.
2. Answer each question by typing the number of your choice (`1`–`4`).
3. Type `q` or `quit` at any time to end the session.

## How the SRS works

Every kanji has an SRS **stage** (0 to 7) and a **next review** date. Only kanji
whose next review date has passed are asked during a session.

| Stage after a correct answer | Next review in |
|------------------------------|----------------|
| 1                            | 4 hours        |
| 2                            | 8 hours        |
| 3                            | 1 day          |
| 4                            | 2 days         |
| 5                            | 7 days         |
| 6                            | 14 days        |
| 7+                           | 30 days        |

A wrong answer resets the kanji to **stage 0** and schedules it again in **5 minutes**.

On first launch, every kanji is inserted at stage 0 and is immediately due.

## Project structure

```
N2Train/
├── Makefile          # install / run / clean rules
├── pyproject.toml    # uv project (dependency: rich)
├── n2_kanji.csv      # kanji deck: caractere, sens (meaning), lecture (reading)
└── src/
    ├── main.py       # menu, training session, SRS logic
    └── database.py   # SQLite schema, seeding from CSV, queries
```

### Data

`n2_kanji.csv` has three columns:

| Column      | Example                | Description                          |
|-------------|------------------------|--------------------------------------|
| `caractere` | `丸`                   | The kanji                            |
| `sens`      | `Round / Full (month)` | English meanings, separated by ` / ` |
| `lecture`   | `がん \| まる まる.める` | On'yomi `\|` kun'yomi (`-` if none)   |

The CSV is (re)imported at each launch with `INSERT OR IGNORE`, so existing
progress is kept and new rows added to the CSV are picked up automatically.

### Generated files

| File                | Content                               |
|---------------------|---------------------------------------|
| `n2train_kanji`     | SQLite database (your SRS progress)   |
| `answer_sheets.txt` | Log of every answer (date, kanji, result) |

## Makefile rules

| Rule           | Effect                                                         |
|----------------|----------------------------------------------------------------|
| `make` / `all` | `install` then `run`                                           |
| `make install` | Install dependencies with uv                                   |
| `make run`     | Launch the app                                                 |
| `make test`    | Run `pytest`                                                   |
| `make clean`   | Remove `__pycache__`, `.pytest_cache` and `.venv`              |
| `make fclean`  | `clean` + remove `uv.lock` and `answer_sheets.txt`             |
| `make reset`   | `fclean` + delete the database (**all progress is lost**)      |
| `make re`      | `fclean` then `all`                                            |

## Roadmap

- [ ] Statistics screen (success rate, kanji per stage, upcoming reviews)
- [ ] Tests
- [ ] Limit the number of new kanji introduced per day

## Author

mchauvin
