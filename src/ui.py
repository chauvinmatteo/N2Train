import time

from fsrs import Rating
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QGuiApplication, QKeySequence, QShortcut
from PySide6.QtWidgets import (QComboBox, QFrame, QGridLayout, QHBoxLayout,
                               QLabel, QMainWindow, QProgressBar,
                               QPushButton, QScrollArea, QSizePolicy,
                               QStackedWidget, QVBoxLayout, QWidget)

import stats
import theme
from charts import ForecastChart, LevelBar
from database import Database
from dates import format_interval, from_iso, local_day_start, utc_now
from quiz import Question, format_reading
from session import NEW_PER_DAY, Session

SESSION_SIZES = (10, 20, 30, 50)
MONTHS = ("January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December")
DAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday",
        "Sunday")
RATING_KEYS = {"1": Rating.Hard, "2": Rating.Good, "3": Rating.Easy}


def repolish(widget: QWidget) -> None:

    # Needed after changing a property used by a stylesheet selector
    for w in [widget, *widget.findChildren(QWidget)]:
        w.style().unpolish(w)
        w.style().polish(w)


def label(text: str = "", name: str | None = None,
          wrap: bool = False) -> QLabel:

    widget = QLabel(text)
    if name:
        widget.setObjectName(name)
    widget.setWordWrap(wrap)
    return widget


def plural(count: int, word: str) -> str:

    return f"{count} {word}" if count == 1 else f"{count} {word}s"


def button(text: str, name: str) -> QPushButton:

    widget = QPushButton(text)
    widget.setObjectName(name)
    widget.setCursor(Qt.CursorShape.PointingHandCursor)
    # Keyboard shortcuts drive the app, buttons never keep the focus
    widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    return widget


class Tile(QFrame):

    def __init__(self, caption: str) -> None:

        super().__init__()
        self.setObjectName("Tile")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(2)
        self.value = label("–", "TileValue")
        self.detail = label("", "Muted")
        layout.addWidget(label(caption.upper(), "TileLabel"))
        layout.addWidget(self.value)
        layout.addWidget(self.detail)

    def set(self, value: str, detail: str = "") -> None:

        self.value.setText(value)
        self.detail.setText(detail)


def card_frame() -> tuple[QFrame, QVBoxLayout]:

    frame = QFrame()
    frame.setObjectName("Card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(22, 18, 22, 18)
    layout.setSpacing(12)
    return frame, layout


class AnswerButton(QFrame):

    clicked = Signal(int)

    def __init__(self, index: int) -> None:

        super().__init__()
        self.index = index
        self.setObjectName("Answer")
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(76)
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Expanding)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(14)
        number = label(str(index + 1), "AnswerNum")
        number.setFixedSize(26, 26)
        number.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text = label("", "AnswerText", wrap=True)
        self.text.setSizePolicy(QSizePolicy.Policy.Expanding,
                                QSizePolicy.Policy.Preferred)
        layout.addWidget(number)
        layout.addWidget(self.text, 1)
        self.locked = False

    def set_choice(self, text: str, style: str) -> None:

        self.text.setText(text)
        self.text.setProperty("kind", style)
        self.set_state("")
        self.locked = False

    def set_state(self, state: str) -> None:

        self.setProperty("state", state)
        repolish(self)

    def mousePressEvent(self, event) -> None:

        if not self.locked and event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.index)


class HomeView(QWidget):

    start_requested = Signal(int)

    def __init__(self, db: Database) -> None:

        super().__init__()
        self.db = db
        self.setObjectName("Page")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 32, 40, 32)
        layout.setSpacing(22)

        layout.addWidget(label("おかえり", "Title"))
        self.subtitle = label("", "Subtitle")
        layout.addWidget(self.subtitle)

        tiles = QHBoxLayout()
        tiles.setSpacing(14)
        self.due_tile = Tile("Due now")
        self.new_tile = Tile("New today")
        self.streak_tile = Tile("Streak")
        for tile in (self.due_tile, self.new_tile, self.streak_tile):
            tiles.addWidget(tile)
        layout.addLayout(tiles)

        deck, deck_layout = card_frame()
        self.deck_title = label("", "SectionTitle")
        self.level_bar = LevelBar()
        deck_layout.addWidget(self.deck_title)
        deck_layout.addWidget(self.level_bar)
        layout.addWidget(deck)

        start = QHBoxLayout()
        start.setSpacing(12)
        start.addWidget(label("Cards per session", "Muted"))
        self.size_box = QComboBox()
        self.size_box.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        for size in SESSION_SIZES:
            self.size_box.addItem(str(size), size)
        self.size_box.setCurrentIndex(1)
        self.size_box.currentIndexChanged.connect(self.refresh)
        start.addWidget(self.size_box)
        start.addStretch()
        self.status = label("", "Muted")
        start.addWidget(self.status)
        self.start_button = button("Start session", "Primary")
        self.start_button.clicked.connect(self.request_start)
        start.addWidget(self.start_button)
        layout.addLayout(start)
        layout.addStretch()

        for key in ("Return", "Enter"):
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            shortcut.activated.connect(self.request_start)

    def request_start(self) -> None:

        if self.start_button.isEnabled():
            self.start_requested.emit(self.size_box.currentData())

    def refresh(self, *_args) -> None:

        now = utc_now()
        local = now.astimezone()
        self.subtitle.setText(f"Welcome back · {DAYS[local.weekday()]} "
                              f"{local.day} {MONTHS[local.month - 1]}")
        data = stats.compute(self.db, now)
        due = self.db.count_due(now)
        introduced = self.db.count_introduced_since(local_day_start(now))
        new_left = min(max(0, NEW_PER_DAY - introduced), self.db.count_new())

        self.due_tile.set(str(due), "reviews waiting")
        self.new_tile.set(str(new_left), f"of {NEW_PER_DAY} per day")
        self.streak_tile.set(plural(data.streak, "day"),
                             plural(data.reviews_today, "answer") + " today")
        mastered = data.levels["mature"]
        self.deck_title.setText(
            f"N2 deck · {mastered} of {data.total} kanji mastered")
        self.level_bar.set_levels(data.levels)

        ready = due + new_left > 0
        size = min(due + new_left, self.size_box.currentData())
        self.start_button.setEnabled(ready)
        self.start_button.setText(
            f"Start session · {plural(size, 'card')}" if ready
            else "All caught up")
        next_due = self.db.next_due()
        if not ready and next_due:
            self.status.setText(
                "Next review in "
                + format_interval(from_iso(next_due) - now))
        else:
            self.status.setText("")


class ReviewView(QWidget):

    finished = Signal()

    def __init__(self) -> None:

        super().__init__()
        self.setObjectName("Page")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.session: Session | None = None
        self.question: Question | None = None
        self.phase = "idle"
        self.shown_at = 0.0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 24, 40, 28)
        layout.setSpacing(18)

        top = QHBoxLayout()
        top.setSpacing(14)
        self.counter = label("", "Muted")
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        quit_button = button("End session", "Ghost")
        quit_button.clicked.connect(self.finished.emit)
        top.addWidget(self.counter)
        top.addWidget(self.progress, 1)
        top.addWidget(quit_button)
        layout.addLayout(top)

        card, card_layout = card_frame()
        card_layout.setContentsMargins(28, 22, 28, 22)
        card_layout.setSpacing(8)
        self.chip = label("", "Chip")
        chip_row = QHBoxLayout()
        chip_row.addStretch()
        chip_row.addWidget(self.chip)
        chip_row.addStretch()
        self.prompt = label("", "Prompt", wrap=True)
        self.prompt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.prompt.setMinimumHeight(150)
        self.hint = label("", "Hint")
        self.hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.details = label("", "Details", wrap=True)
        self.details.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addLayout(chip_row)
        card_layout.addWidget(self.prompt)
        card_layout.addWidget(self.hint)
        card_layout.addWidget(self.details)
        layout.addWidget(card)

        grid = QGridLayout()
        grid.setSpacing(12)
        self.answers = [AnswerButton(i) for i in range(4)]
        for answer in self.answers:
            answer.clicked.connect(self.choose)
            grid.addWidget(answer, answer.index // 2, answer.index % 2)
        layout.addLayout(grid, 1)

        layout.addWidget(self.build_feedback())

        for key in ("1", "2", "3", "4", "Return", "Enter", "Space",
                    "Escape"):
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            shortcut.activated.connect(lambda k=key: self.on_key(k))

    def build_feedback(self) -> QStackedWidget:

        self.feedback = QStackedWidget()
        self.feedback.setFixedHeight(48)

        waiting = QWidget()
        row = QHBoxLayout(waiting)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(label("Press 1–4 or click an answer · Esc to stop",
                            "KeyHint"))
        self.feedback.addWidget(waiting)

        wrong = QWidget()
        row = QHBoxLayout(wrong)
        row.setContentsMargins(0, 0, 0, 0)
        self.wrong_text = label("", "FeedbackBad")
        row.addWidget(self.wrong_text)
        row.addStretch()
        row.addWidget(label("It will come back soon", "KeyHint"))
        next_button = button("Continue  ⏎", "Rate")
        next_button.setProperty("main", "true")
        next_button.clicked.connect(self.next_question)
        row.addWidget(next_button)
        self.feedback.addWidget(wrong)

        right = QWidget()
        row = QHBoxLayout(right)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(label("Correct!", "FeedbackGood"))
        row.addStretch()
        row.addWidget(label("How hard was it?", "KeyHint"))
        self.rate_buttons: dict[Rating, QPushButton] = {}
        for key, rating in RATING_KEYS.items():
            rate = button("", "Rate")
            rate.setProperty("main", "true" if rating == Rating.Good
                             else "false")
            rate.clicked.connect(lambda _=False, r=rating: self.grade(r))
            self.rate_buttons[rating] = rate
            row.addWidget(rate)
        self.feedback.addWidget(right)
        return self.feedback

    def start(self, session: Session) -> None:

        self.session = session
        self.next_question()
        self.setFocus()

    def next_question(self) -> None:

        assert self.session is not None
        self.question = self.session.next_question()
        if self.question is None:
            self.phase = "idle"
            self.finished.emit()
            return
        q = self.question
        self.phase = "question"
        self.counter.setText(f"{self.session.done + 1} / "
                             f"{self.session.total}")
        self.progress.setMaximum(self.session.total)
        self.progress.setValue(self.session.done)
        self.chip.setText(f"{q.label_jp}  ·  {q.label}")
        self.prompt.setText(q.prompt)
        self.prompt.setProperty("kind", "kanji" if q.prompt_is_kanji
                                else "text")
        repolish(self.prompt)
        self.hint.setText(q.hint)
        self.details.setText("")
        for answer, choice in zip(self.answers, q.choices):
            answer.set_choice(choice, q.choice_style)
            answer.setVisible(True)
        for answer in self.answers[len(q.choices):]:
            answer.setVisible(False)
        self.feedback.setCurrentIndex(0)
        self.shown_at = time.monotonic()

    def choose(self, index: int) -> None:

        if self.phase != "question" or self.session is None:
            return
        q = self.question
        assert q is not None
        if index >= len(q.choices):
            return
        kanji = self.session.kanji
        assert kanji is not None
        elapsed = int((time.monotonic() - self.shown_at) * 1000)
        correct = self.session.answer(index, elapsed)

        for answer in self.answers:
            answer.locked = True
            if answer.index == q.answer_index:
                answer.set_state("correct")
            elif answer.index == index:
                answer.set_state("wrong")
            else:
                answer.set_state("dim")
        reading = format_reading(kanji["reading"]).replace("\n", "  ")
        self.details.setText(f"{kanji['caractere']}   ·   {reading}   ·   "
                             f"{kanji['meaning']}")

        if correct:
            self.phase = "correct"
            intervals = self.session.intervals()
            for key, rating in RATING_KEYS.items():
                self.rate_buttons[rating].setText(
                    f"{rating.name}  {format_interval(intervals[rating])}"
                    f"   [{key}]")
            self.feedback.setCurrentIndex(2)
        else:
            self.phase = "wrong"
            self.wrong_text.setText("Not quite. The answer is in green.")
            self.feedback.setCurrentIndex(1)

    def grade(self, rating: Rating) -> None:

        if self.phase != "correct" or self.session is None:
            return
        self.session.grade(rating)
        self.next_question()

    def on_key(self, key: str) -> None:

        confirm = key in ("Return", "Enter", "Space")
        if key == "Escape":
            self.finished.emit()
        elif self.phase == "question" and key.isdigit():
            self.choose(int(key) - 1)
        elif self.phase == "wrong" and confirm:
            self.next_question()
        elif self.phase == "correct" and key in RATING_KEYS:
            self.grade(RATING_KEYS[key])
        elif self.phase == "correct" and confirm:
            self.grade(Rating.Good)


class SummaryView(QWidget):

    done = Signal()

    def __init__(self) -> None:

        super().__init__()
        self.setObjectName("Page")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 32, 40, 32)
        layout.setSpacing(22)
        layout.addWidget(label("お疲れ様", "Title"))
        layout.addWidget(label("Session complete", "Subtitle"))

        tiles = QHBoxLayout()
        tiles.setSpacing(14)
        self.answers_tile = Tile("Answers")
        self.accuracy_tile = Tile("Accuracy")
        self.time_tile = Tile("Time")
        for tile in (self.answers_tile, self.accuracy_tile, self.time_tile):
            tiles.addWidget(tile)
        layout.addLayout(tiles)

        missed, self.missed_layout = card_frame()
        self.missed_title = label("", "SectionTitle")
        self.missed_layout.addWidget(self.missed_title)
        self.missed_list = QVBoxLayout()
        self.missed_list.setSpacing(6)
        self.missed_layout.addLayout(self.missed_list)
        layout.addWidget(missed)

        row = QHBoxLayout()
        row.addStretch()
        back = button("Back home  ⏎", "Primary")
        back.clicked.connect(self.done.emit)
        row.addWidget(back)
        layout.addLayout(row)
        layout.addStretch()

        for key in ("Return", "Enter", "Escape"):
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            shortcut.activated.connect(self.done.emit)

    def show_session(self, session: Session) -> None:

        minutes, seconds = divmod(
            int((utc_now() - session.started_at).total_seconds()), 60)
        unique = len({r.kanji["id"] for r in session.results})
        self.answers_tile.set(str(session.done), f"{unique} kanji")
        self.accuracy_tile.set(f"{session.accuracy():.0%}",
                               "first try and retries")
        self.time_tile.set(f"{minutes}:{seconds:02d}", "minutes")

        clear_layout(self.missed_list)
        missed = session.missed()
        self.missed_title.setText(
            f"To review again · {len(missed)}" if missed
            else "No mistakes this time")
        for kanji in missed[:8]:
            self.missed_list.addWidget(kanji_row(kanji))
        self.setFocus()


def clear_layout(layout: QVBoxLayout) -> None:

    while layout.count():
        item = layout.takeAt(0)
        if item.widget():
            item.widget().deleteLater()


def kanji_row(kanji: dict, misses: int | None = None) -> QWidget:

    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(16)
    character = label(kanji["caractere"], "MissedKanji")
    character.setFixedWidth(44)
    layout.addWidget(character)
    reading = format_reading(kanji["reading"]).replace("\n", "  ")
    text = label(f"{kanji['meaning']}\n{reading}", "Muted", wrap=True)
    layout.addWidget(text, 1)
    if misses is not None:
        layout.addWidget(label(f"{misses} ×", "MissedCount"))
    return row


class StatsView(QScrollArea):

    def __init__(self, db: Database) -> None:

        super().__init__()
        self.db = db
        self.setWidgetResizable(True)
        page = QWidget()
        page.setObjectName("Page")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 32, 40, 32)
        layout.setSpacing(18)
        layout.addWidget(label("統計", "Title"))
        layout.addWidget(label("Your progress on the N2 deck", "Subtitle"))

        tiles = QHBoxLayout()
        tiles.setSpacing(14)
        self.studied_tile = Tile("Studied")
        self.mastered_tile = Tile("Mastered")
        self.accuracy_tile = Tile("Accuracy · 7 d")
        self.reviews_tile = Tile("Answers")
        for tile in (self.studied_tile, self.mastered_tile,
                     self.accuracy_tile, self.reviews_tile):
            tiles.addWidget(tile)
        layout.addLayout(tiles)

        forecast, forecast_layout = card_frame()
        forecast_layout.addWidget(label("Upcoming reviews · next 14 days",
                                        "SectionTitle"))
        self.chart = ForecastChart()
        forecast_layout.addWidget(self.chart)
        forecast_layout.addWidget(label(
            "Today includes the reviews you are late on.", "Muted"))
        layout.addWidget(forecast)

        deck, deck_layout = card_frame()
        deck_layout.addWidget(label("Deck", "SectionTitle"))
        self.level_bar = LevelBar()
        deck_layout.addWidget(self.level_bar)
        deck_layout.addWidget(label(
            "Mastered: the memory is expected to last 21 days or more.",
            "Muted"))
        layout.addWidget(deck)

        missed, missed_layout = card_frame()
        missed_layout.addWidget(label("Most missed", "SectionTitle"))
        self.missed_list = QVBoxLayout()
        self.missed_list.setSpacing(6)
        missed_layout.addLayout(self.missed_list)
        layout.addWidget(missed)
        layout.addStretch()
        self.setWidget(page)

    def refresh(self) -> None:

        data = stats.compute(self.db, utc_now())
        studied = data.total - data.levels["new"]
        self.studied_tile.set(str(studied), f"of {data.total} kanji")
        self.mastered_tile.set(str(data.levels["mature"]),
                               f"{data.levels['young']} getting there")
        self.accuracy_tile.set(
            "–" if data.accuracy_week is None
            else f"{data.accuracy_week:.0%}", "of answers right")
        self.reviews_tile.set(str(data.reviews_total),
                              f"{data.streak}-day streak")
        self.chart.set_values(data.forecast)
        self.level_bar.set_levels(data.levels)

        clear_layout(self.missed_list)
        if not data.missed:
            self.missed_list.addWidget(label("No mistakes yet.", "Muted"))
        for kanji in data.missed:
            self.missed_list.addWidget(kanji_row(kanji, kanji["misses"]))


class MainWindow(QMainWindow):

    def __init__(self, db: Database) -> None:

        super().__init__()
        self.db = db
        self.session: Session | None = None
        self.setWindowTitle("N2Train")
        self.resize(980, 720)
        self.setMinimumSize(760, 600)

        root = QWidget()
        root.setObjectName("Root")
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.build_top_bar())

        self.pages = QStackedWidget()
        self.home = HomeView(db)
        self.review = ReviewView()
        self.summary = SummaryView()
        self.stats = StatsView(db)
        for page in (self.home, self.review, self.summary, self.stats):
            self.pages.addWidget(page)
        layout.addWidget(self.pages, 1)
        self.setCentralWidget(root)

        self.home.start_requested.connect(self.start_session)
        self.review.finished.connect(self.end_session)
        self.summary.done.connect(self.show_home)

        self.apply_theme()
        QGuiApplication.styleHints().colorSchemeChanged.connect(
            self.apply_theme)
        self.show_home()

    def build_top_bar(self) -> QWidget:

        bar = QFrame()
        bar.setObjectName("TopBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(24, 12, 24, 12)
        layout.setSpacing(8)
        layout.addWidget(label("N2Train", "Brand"))
        layout.addWidget(label("漢字トレーナー", "BrandJp"))
        layout.addStretch()
        self.nav_home = button("Home", "Nav")
        self.nav_stats = button("Statistics", "Nav")
        for nav in (self.nav_home, self.nav_stats):
            nav.setCheckable(True)
            layout.addWidget(nav)
        self.nav_home.clicked.connect(self.show_home)
        self.nav_stats.clicked.connect(self.show_stats)
        return bar

    def apply_theme(self, *_args) -> None:

        self.setStyleSheet(theme.stylesheet(theme.current()))
        self.update()

    def set_nav(self, active: QPushButton | None) -> None:

        for nav in (self.nav_home, self.nav_stats):
            nav.setChecked(nav is active)
            nav.setVisible(active is not None)

    def show_home(self) -> None:

        self.home.refresh()
        self.set_nav(self.nav_home)
        self.pages.setCurrentWidget(self.home)
        self.home.setFocus()

    def show_stats(self) -> None:

        self.stats.refresh()
        self.set_nav(self.nav_stats)
        self.pages.setCurrentWidget(self.stats)

    def start_session(self, size: int) -> None:

        self.session = Session(self.db, size)
        self.set_nav(None)
        self.pages.setCurrentWidget(self.review)
        self.review.start(self.session)

    def end_session(self) -> None:

        if self.session is None or self.session.done == 0:
            self.show_home()
            return
        self.summary.show_session(self.session)
        self.set_nav(None)
        self.pages.setCurrentWidget(self.summary)
