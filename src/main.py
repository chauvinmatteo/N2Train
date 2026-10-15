import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from database import Database
from ui import MainWindow

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "n2train.db"
CSV_PATH = ROOT / "n2_kanji.csv"


def main() -> None:

    db = Database(DB_PATH)
    db.seed(CSV_PATH)

    app = QApplication(sys.argv)
    app.setApplicationName("N2Train")
    window = MainWindow(db)
    window.show()
    code = app.exec()

    db.close()
    sys.exit(code)


if __name__ == "__main__":
    main()
