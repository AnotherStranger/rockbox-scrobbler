from pathlib import Path

from pydantic import ValidationError
from PySide6 import QtWidgets
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from rockbox_listenbrainz_scrobbler.exceptions import (
    InvalidAuthTokenException,
    InvalidSubmitListensPayloadException,
)
from rockbox_listenbrainz_scrobbler.scrobbling import (
    ListenBrainzScrobbler,
    read_rockbox_log,
)

# Global constants
LISTENBRAINZ_AUTH_TOKEN_SETTING_KEY: str = "Listenbrainz/auth-token"


def launch():
    qt_app = QtWidgets.QApplication([])
    widget = ListenbrainzWidget()
    widget.resize(800, 600)
    widget.show()
    return qt_app.exec()


def show_error(text: str):
    """
    Display an error message with the given text
    """
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setText("Error")
    msg.setInformativeText(text)
    msg.setWindowTitle("Error")
    msg.exec()


def show_info(text: str):
    """
    Display an error message with the given text
    """
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Information)
    msg.setText("Success")
    msg.setInformativeText(text)
    msg.setWindowTitle("Success")
    msg.exec()


class ListenbrainzWidget(QWidget):
    """
    Main GUI widget for the Rockbox Listenbrainz Scrobbler
    """

    def __init__(self):
        super().__init__()

        self.settings = QSettings("AnotherStranger", "Rockbox Listenbrainz Scrobbler")

        self.setWindowTitle("Rockbox Listenbrainz Scrobbler")

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Input field for auth token
        settings_group = QGroupBox("Settings")
        auth_layout = QHBoxLayout()
        # layout.addLayout(auth_layout)

        auth_label = QLabel("Enter User Token:", self)
        auth_layout.addWidget(auth_label)

        self.auth_token_input = QLineEdit(self)
        self.auth_token_input.setPlaceholderText("User Token")
        self.auth_token_input.setToolTip(
            "Your personal auth token for ListenBrainz. Get it here: https://listenbrainz.org/settings/"
        )
        self.auth_token_input.setEchoMode(QLineEdit.EchoMode.Password)
        if self.settings.value(LISTENBRAINZ_AUTH_TOKEN_SETTING_KEY):
            self.auth_token_input.setText(
                self.settings.value(LISTENBRAINZ_AUTH_TOKEN_SETTING_KEY)
            )

        auth_layout.addWidget(self.auth_token_input)
        settings_group.setLayout(auth_layout)
        layout.addWidget(settings_group)

        # Button for selecting log file
        self.file_button = QPushButton("Select Logfile...", self)
        self.file_button.clicked.connect(self.select_file)

        # Submit button
        self.submit_button = QPushButton("Submit", self)
        self.submit_button.clicked.connect(self.submit_data)
        self.submit_button.setEnabled(False)

        # Horizontal layout for both buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.file_button)
        buttons_layout.addWidget(self.submit_button)
        layout.addLayout(buttons_layout)

        # Read-only text edit area
        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)

    def select_file(self):
        """
        Opens a file dialog allowing the user to select a log file and configures the UI accordingly
        """
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("Rockbox Scrobbler Log (*.log);;All Files (*)")
        if file_dialog.exec_():
            selected_file = Path(file_dialog.selectedFiles()[0])
            if selected_file.exists():
                self.selected_file = selected_file
                self.submit_button.setEnabled(True)
                content = selected_file.open("r", encoding="utf8").read()
                self.text_edit.setText(content)
            else:
                show_error("Selected file does not exist.")
        else:
            self.submit_button.setEnabled(False)

    def submit_data(self):
        """
        Retrieves the auth token, saves it in the settings, reads the log file, sends scrobbles to
        the ListenBrainz server, and updates the UI accordingly
        """
        auth_token = self.auth_token_input.text()
        if not auth_token:
            show_error(
                "You have to set your Auth Token. See: https://listenbrainz.org/settings/"
            )
            return

        self.settings.setValue(LISTENBRAINZ_AUTH_TOKEN_SETTING_KEY, auth_token)

        try:
            scrobbles = read_rockbox_log(self.selected_file)
            client = ListenBrainzScrobbler(auth_token)

            client.scrobble_multiple(scrobbles)
            show_info("Successfully uploaded your Listens.")
        except ValidationError:
            show_error(
                "Could not parse the given File. Did you choose a Rockbox .scrobbler.log?"
            )
        except InvalidAuthTokenException:
            show_error("The given auth token is invalid.")
        except InvalidSubmitListensPayloadException:
            show_error("Could not submit listen. Maybe your log file is ill formatted.")


if __name__ == "__main__":
    launch()
