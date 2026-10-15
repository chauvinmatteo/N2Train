from dataclasses import asdict, dataclass
from string import Template

from PySide6.QtCore import Qt
from PySide6.QtGui import QFontDatabase, QGuiApplication


@dataclass(frozen=True)
class Palette:

    bg: str
    surface: str
    raised: str
    border: str
    fg: str
    muted: str
    accent: str
    accent_hover: str
    accent_fg: str
    accent_soft: str
    good: str
    good_soft: str
    bad: str
    bad_soft: str
    warn: str


# Indigo (藍) ink on cool paper
LIGHT = Palette(
    bg="#F3F4F7", surface="#FFFFFF", raised="#E9ECF2", border="#D9DDE6",
    fg="#1A1F2E", muted="#5C6478", accent="#33509E",
    accent_hover="#2A4489", accent_fg="#FFFFFF", accent_soft="#E2E8F6",
    good="#23784A", good_soft="#E0F2E7", bad="#B8402F", bad_soft="#FAE5E1",
    warn="#B07A12",
)

DARK = Palette(
    bg="#121419", surface="#1B1E26", raised="#252934", border="#2F3441",
    fg="#E6E9F0", muted="#9AA2B4", accent="#8FA9EE",
    accent_hover="#A8BCF3", accent_fg="#10131A", accent_soft="#232E4A",
    good="#6FD49A", good_soft="#163224", bad="#F08C7E", bad_soft="#3A1E1A",
    warn="#E8BE62",
)

KANJI_FONTS = ("Hiragino Mincho ProN", "Yu Mincho", "Noto Serif CJK JP",
               "Noto Serif JP", "MS Mincho")
KANA_FONTS = ("Hiragino Sans", "Hiragino Kaku Gothic ProN", "Yu Gothic",
              "Noto Sans CJK JP", "Noto Sans JP", "Meiryo")

STYLESHEET = Template('''
QWidget { color: $fg; font-size: 14px; }
QWidget#Root, QWidget#Page, QScrollArea, QScrollArea > QWidget > QWidget {
    background: $bg;
}
QScrollArea { border: none; }
QLabel { background: transparent; }

#TopBar { background: $bg; border-bottom: 1px solid $border; }
#Brand { font-size: 17px; font-weight: 700; }
#BrandJp { font-family: "$kana"; color: $muted; font-size: 13px; }
QPushButton#Nav {
    background: transparent; border: none; border-radius: 6px;
    padding: 6px 14px; color: $muted; font-weight: 600;
}
QPushButton#Nav:hover { background: $raised; color: $fg; }
QPushButton#Nav:checked { background: $accent_soft; color: $accent; }

#Title { font-family: "$kanji"; font-size: 40px; }
#Subtitle { color: $muted; font-size: 15px; }
#SectionTitle { font-size: 15px; font-weight: 700; }
#Muted { color: $muted; }

#Card { background: $surface; border: 1px solid $border;
        border-radius: 12px; }
#Tile { background: $surface; border: 1px solid $border;
        border-radius: 10px; }
#TileValue { font-size: 30px; font-weight: 700; }
#TileLabel { color: $muted; font-size: 11px; font-weight: 700;
             letter-spacing: 1px; }

QPushButton#Primary {
    background: $accent; color: $accent_fg; border: none;
    border-radius: 8px; padding: 12px 26px; font-size: 15px;
    font-weight: 700;
}
QPushButton#Primary:hover { background: $accent_hover; }
QPushButton#Primary:disabled { background: $raised; color: $muted; }
QPushButton#Ghost {
    background: transparent; border: 1px solid $border; border-radius: 8px;
    padding: 8px 16px;
}
QPushButton#Ghost:hover { background: $raised; }
QPushButton:focus { outline: none; }

QComboBox {
    background: $surface; border: 1px solid $border; border-radius: 8px;
    padding: 8px 12px; min-width: 64px;
}
QComboBox QAbstractItemView {
    background: $surface; border: 1px solid $border;
    selection-background-color: $accent_soft; selection-color: $fg;
}

QScrollBar:vertical { background: transparent; width: 10px; margin: 4px; }
QScrollBar::handle:vertical { background: $border; border-radius: 3px;
                              min-height: 32px; }
QScrollBar::handle:vertical:hover { background: $muted; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }

QProgressBar { background: $raised; border: none; border-radius: 4px;
               max-height: 8px; min-height: 8px; }
QProgressBar::chunk { background: $accent; border-radius: 4px; }

#Chip { background: $accent_soft; color: $accent; border-radius: 11px;
        padding: 4px 12px; font-weight: 700; }
#Prompt[kind="kanji"] { font-family: "$kanji"; font-size: 116px; }
#Prompt[kind="text"] { font-size: 26px; font-weight: 600; }
#Hint { color: $muted; font-size: 15px; }
#Details { color: $muted; font-size: 15px; font-family: "$kana"; }

#Answer { background: $surface; border: 1px solid $border;
          border-radius: 10px; }
#Answer:hover { border: 1px solid $accent; }
#Answer[state="correct"] { background: $good_soft;
                           border: 2px solid $good; }
#Answer[state="wrong"] { background: $bad_soft; border: 2px solid $bad; }
#Answer[state="dim"] { background: $surface; border: 1px solid $border; }
#AnswerNum { background: $raised; color: $muted; border-radius: 6px;
             font-size: 13px; font-weight: 700; }
#Answer[state="correct"] #AnswerNum { background: $good;
                                      color: $surface; }
#Answer[state="wrong"] #AnswerNum { background: $bad; color: $surface; }
#Answer[state="dim"] #AnswerText { color: $muted; }
#AnswerText[kind="kanji"] { font-family: "$kanji"; font-size: 40px; }
#AnswerText[kind="kana"] { font-family: "$kana"; font-size: 17px; }
#AnswerText[kind="text"] { font-size: 16px; }

#FeedbackGood { color: $good; font-size: 17px; font-weight: 700; }
#FeedbackBad { color: $bad; font-size: 17px; font-weight: 700; }
#KeyHint { color: $muted; font-size: 13px; }
QPushButton#Rate {
    background: $surface; border: 1px solid $border; border-radius: 8px;
    padding: 9px 18px; font-weight: 600;
}
QPushButton#Rate:hover { border: 1px solid $accent; }
QPushButton#Rate[main="true"] { background: $accent; color: $accent_fg;
                                border: 1px solid $accent; }
QPushButton#Rate[main="true"]:hover { background: $accent_hover; }

#MissedKanji { font-family: "$kanji"; font-size: 30px; }
#MissedCount { color: $bad; font-weight: 700; }
''')


def first_available(families: tuple[str, ...]) -> str:

    installed = set(QFontDatabase.families())
    for family in families:
        if family in installed:
            return family
    return families[0]


def current() -> Palette:

    scheme = QGuiApplication.styleHints().colorScheme()
    return DARK if scheme == Qt.ColorScheme.Dark else LIGHT


def stylesheet(palette: Palette) -> str:

    return STYLESHEET.substitute(asdict(palette),
                                 kanji=first_available(KANJI_FONTS),
                                 kana=first_available(KANA_FONTS))
