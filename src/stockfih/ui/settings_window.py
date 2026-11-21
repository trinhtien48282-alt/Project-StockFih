from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QSlider,
    QSpinBox,
    QWidget,
)

from stockfih.personality.cultural_rules import COUNTRIES, NAME_ORIGINS
from stockfih.personality.settings import (
    LANGUAGES,
    MAX_ELO,
    MIN_ELO,
    PROFANITY_LEVELS,
    PersonalitySettings,
)
from stockfih.ui.app_theme import THEMES
from stockfih.ui.themes import PIECE_THEMES, SQUARE_THEMES

MODE_LABELS = {"toxic_comedian": "Toxic Comedian", "professional": "Professional", "silent": "Silent"}
FREQUENCY_LABELS = {"silent": "Silent", "normal": "Normal", "chaotic": "Chaotic", "unhinged": "Unhinged"}


def _combo(names, current: str) -> QComboBox:
    box = QComboBox()
    box.addItems(list(names))
    box.setCurrentIndex(box.findText(current))  # setCurrentText does nothing on a plain combo
    return box


def _keyed(options: dict[str, str], current: str) -> QComboBox:
    # Shows the labels, stores the keys (read them back with currentData()).
    box = QComboBox()
    for key, label in options.items():
        box.addItem(label, key)
    box.setCurrentIndex(max(0, box.findData(current)))
    return box


def _line() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    return line


def ask_settings(parent: QWidget, values: dict) -> dict | None:
    # values/result keys: theme, square, piece (names), animate, sound (bool), volume (0-100),
    # personality (a PersonalitySettings). Returns the new values, or None if cancelled.
    dialog = QDialog(parent)
    dialog.setWindowTitle("Settings")
    dialog.setMinimumWidth(420)
    form = QFormLayout(dialog)
    theme = _combo(THEMES, values["theme"])
    square = _combo(SQUARE_THEMES, values["square"])
    piece = _combo(PIECE_THEMES, values["piece"])
    animate = QCheckBox("Animate moves")
    animate.setChecked(values["animate"])
    sound = QCheckBox("Sound effects")
    sound.setChecked(values["sound"])
    volume = QSlider(Qt.Orientation.Horizontal)
    volume.setRange(0, 100)
    volume.setValue(values["volume"])
    form.addRow("App theme", theme)
    form.addRow("Square theme (this profile)", square)
    form.addRow("Piece theme (this profile)", piece)
    form.addRow(animate)
    form.addRow(sound)
    form.addRow("Volume", volume)

    p: PersonalitySettings = values["personality"]
    form.addRow(_line())
    mode = _keyed(MODE_LABELS, p.mode)
    frequency = _keyed(FREQUENCY_LABELS, p.frequency)
    profanity = _keyed({level: level.capitalize() for level in PROFANITY_LEVELS}, p.profanity)
    language = _keyed(LANGUAGES, p.language)
    elo = QCheckBox("Rating-based attitude")
    elo.setChecked(p.elo_personality)
    assumed = QSpinBox()
    assumed.setRange(0, MAX_ELO)
    assumed.setSpecialValueText("Not set")  # 0 shown as "Not set"
    assumed.setValue(p.stockfih_elo or 0)
    cultural = QCheckBox("Identity jokes (use the country and name origin below)")
    cultural.setChecked(p.cultural)
    country = _keyed({"": "Not set", **COUNTRIES}, p.country)
    origin = _keyed({"": "Not set", **{k: v[0] for k, v in NAME_ORIGINS.items()}}, p.origin)
    alien = QCheckBox("Alien mode while the identity is not set")
    alien.setChecked(p.alien)
    muted = QCheckBox("Mute commentary")
    muted.setChecked(p.muted)
    form.addRow("Personality (this profile)", mode)
    form.addRow("Commentary frequency", frequency)
    form.addRow("Profanity level", profanity)
    form.addRow("Commentary language", language)
    form.addRow(elo)
    form.addRow("StockFih assumed rating (a personality number, not measured)", assumed)
    form.addRow(cultural)
    form.addRow("Country", country)
    form.addRow("Name origin", origin)
    form.addRow(alien)
    form.addRow(muted)

    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
    )
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    form.addRow(buttons)
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return None
    rating = assumed.value()
    return {
        "theme": theme.currentText(),
        "square": square.currentText(),
        "piece": piece.currentText(),
        "animate": animate.isChecked(),
        "sound": sound.isChecked(),
        "volume": volume.value(),
        "personality": PersonalitySettings(
            mode=mode.currentData(),
            frequency=frequency.currentData(),
            profanity=profanity.currentData(),
            elo_personality=elo.isChecked(),
            cultural=cultural.isChecked(),
            country=country.currentData(),
            origin=origin.currentData(),
            alien=alien.isChecked(),
            language=language.currentData(),
            muted=muted.isChecked(),
            stockfih_elo=rating if rating >= MIN_ELO else None,
        ),
    }
