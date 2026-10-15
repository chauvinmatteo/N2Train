from datetime import timedelta

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

import theme
from dates import utc_now

WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def nice_step(maximum: int, ticks: int = 4) -> int:

    for step in (1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000):
        if maximum / step <= ticks:
            return step
    return maximum // ticks + 1


class ForecastChart(QWidget):

    """Number of reviews due on each of the next days."""

    def __init__(self) -> None:

        super().__init__()
        self.values: list[int] = []
        self.setMinimumHeight(220)
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Fixed)

    def set_values(self, values: list[int]) -> None:

        self.values = values
        self.update()

    def paintEvent(self, event) -> None:

        if not self.values:
            return
        p = theme.current()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        small = QFont(self.font())
        small.setPixelSize(11)
        painter.setFont(small)

        left, right, top, bottom = 34, 8, 18, 26
        width = self.width() - left - right
        height = self.height() - top - bottom
        step = nice_step(max(max(self.values), 1))
        scale_max = step * -(-max(max(self.values), 1) // step)

        # Grid and value axis
        for tick in range(0, scale_max + 1, step):
            y = top + height - height * tick / scale_max
            painter.setPen(QPen(QColor(p.border), 1))
            painter.drawLine(left, int(y), left + width, int(y))
            painter.setPen(QColor(p.muted))
            painter.drawText(QRectF(0, y - 8, left - 8, 16),
                             Qt.AlignmentFlag.AlignRight
                             | Qt.AlignmentFlag.AlignVCenter, str(tick))

        # Bars
        slot = width / len(self.values)
        bar = min(28.0, slot * 0.62)
        today = utc_now().astimezone().date()
        for i, value in enumerate(self.values):
            x = left + slot * i + (slot - bar) / 2
            h = height * value / scale_max
            color = QColor(p.accent if i else p.warn)
            if value:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(color)
                painter.drawRoundedRect(QRectF(x, top + height - h, bar, h),
                                        3, 3)
                painter.setPen(QColor(p.fg))
                painter.drawText(QRectF(x - 10, top + height - h - 16,
                                        bar + 20, 14),
                                 Qt.AlignmentFlag.AlignCenter, str(value))
            day = today + timedelta(days=i)
            label = "Today" if i == 0 else WEEKDAYS[day.weekday()]
            painter.setPen(QColor(p.fg if i == 0 else p.muted))
            painter.drawText(QRectF(left + slot * i - 4, top + height + 6,
                                    slot + 8, 16),
                             Qt.AlignmentFlag.AlignCenter,
                             label if i == 0 or slot > 30 or i % 2 == 0
                             else "")
        painter.end()


class LevelBar(QWidget):

    """Stacked bar of the deck split by learning level, with a legend."""

    LABELS = {"new": "New", "learning": "Learning", "young": "Young",
              "mature": "Mastered"}

    def __init__(self) -> None:

        super().__init__()
        self.levels: dict[str, int] = {}
        self.setMinimumHeight(52)
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Fixed)

    def set_levels(self, levels: dict[str, int]) -> None:

        self.levels = levels
        self.update()

    def colors(self) -> dict[str, QColor]:

        p = theme.current()
        young = QColor(p.accent)
        young.setAlphaF(0.45)
        return {"new": QColor(p.raised), "learning": QColor(p.warn),
                "young": young, "mature": QColor(p.accent)}

    def paintEvent(self, event) -> None:

        total = sum(self.levels.values())
        if not total:
            return
        p = theme.current()
        colors = self.colors()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Bar, clipped to a rounded rectangle
        bar = QRectF(0, 0, self.width(), 14)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(colors["new"])
        painter.drawRoundedRect(bar, 7, 7)
        x = 0.0
        painter.save()
        painter.setClipRect(bar)
        for level, count in self.levels.items():
            w = self.width() * count / total
            if level != "new" and w:
                painter.setBrush(colors[level])
                painter.drawRect(QRectF(x, 0, w, 14))
            x += w
        painter.restore()

        # Legend
        small = QFont(self.font())
        small.setPixelSize(12)
        painter.setFont(small)
        metrics = painter.fontMetrics()
        x = 0.0
        for level, count in self.levels.items():
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(colors[level])
            painter.drawRoundedRect(QRectF(x, 32, 10, 10), 2, 2)
            text = f"{self.LABELS[level]} {count}"
            painter.setPen(QColor(p.fg))
            painter.drawText(int(x + 16), 42, text)
            x += 16 + metrics.horizontalAdvance(text) + 22
        painter.end()
