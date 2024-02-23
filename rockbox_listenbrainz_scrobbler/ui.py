from pathlib import Path

from pydantic import ValidationError
from pylistenbrainz.errors import (
    InvalidAuthTokenException,
    InvalidSubmitListensPayloadException,
)
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from rockbox_listenbrainz_scrobbler.scrobbling import (
    ListenBrainzScrobbler,
    read_rockbox_log,
)

LISTENBRAINZ_AUTH_TOKEN_SETTING_KEY: str = "Listenbrainz/auth-token"


def show_error(text: str):
    """
    Show a Error message with the given Text
    """
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Critical)
    msg.setText("Error")
    msg.setInformativeText(text)
    msg.setWindowTitle("Error")
    msg.exec_()


class ListenbrainzWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("AnotherStranger", "Rockbox Listenbrainz Scrobbler")

        self.setWindowTitle("Rockbox Listenbrainz Scrobbler")

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Passwortfeld für Auth-Token
        auth_layout = QHBoxLayout()
        layout.addLayout(auth_layout)

        auth_label = QLabel("Enter User Token:", self)
        auth_layout.addWidget(auth_label)

        self.auth_token_input = QLineEdit(self)
        self.auth_token_input.setPlaceholderText("User Token")
        if self.settings.value(LISTENBRAINZ_AUTH_TOKEN_SETTING_KEY):
            self.auth_token_input.setText(
                self.settings.value(LISTENBRAINZ_AUTH_TOKEN_SETTING_KEY)
            )

        auth_layout.addWidget(self.auth_token_input)

        # Dateiauswahl-Button
        self.file_button = QPushButton("Select Logfile...", self)
        self.file_button.clicked.connect(self.select_file)

        # Submit-Button
        self.submit_button = QPushButton("Submit", self)
        self.submit_button.clicked.connect(self.submit_data)
        self.submit_button.setEnabled(False)

        # Horizontales Layout für beide Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.file_button)
        buttons_layout.addWidget(self.submit_button)
        layout.addLayout(buttons_layout)

        # Fortschrittsbalken
        self.progress_bar = QProgressBar(self)
        layout.addWidget(self.progress_bar)

        # Textfeld
        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)

    def select_file(self):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("All Files (*);;Rockbox Scrobbler Log (*.log)")
        if file_dialog.exec_():
            self.selected_file = Path(file_dialog.selectedFiles()[0])
            self.submit_button.setEnabled(True)
            self.text_edit.setText(self.selected_file.open("r", encoding="utf8").read())
        else:
            self.submit_button.setEnabled(False)

    def submit_data(self):
        auth_token = self.auth_token_input.text()
        if not auth_token:
            show_error(
                "You have to set your Auth Token. See: https://listenbrainz.org/settings/"
            )
            return

        self.settings.setValue(LISTENBRAINZ_AUTH_TOKEN_SETTING_KEY, auth_token)

        try:
            scrobbles = read_rockbox_log(self.selected_file)
            self.progress_bar.setMaximum(len(scrobbles))
            client = ListenBrainzScrobbler(auth_token)

            for i, scrobble in enumerate(scrobbles):
                self.progress_bar.setValue(i + 1)
                client.scrobble(scrobble)
        except ValidationError:
            show_error(
                "Could not parse the given File. Did you choose a Rockbox .scrobbler.log?"
            )
        except InvalidAuthTokenException:
            show_error("The given auth token is invalid.")
        except InvalidSubmitListensPayloadException:
            show_error("Could not submit listen. Maybe your log file is ill formatted.")
