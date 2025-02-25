from PySide6.QtWidgets import QApplication, QFrame, QTextEdit, QPushButton, QScrollArea, QLabel, QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QShowEvent

from aplustools.io.qtquick import QQuickBoxLayout, QBoxDirection


class SmartTextEdit(QTextEdit):
    """
    A smart text edit that automatically adjusts it's size
    """
    def __init__(self, max_height: int = 100, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.max_height: int = max_height
        self.textChanged.connect(self._adjustHeight)

    def _adjustHeight(self) -> None:
        """
        Adjusts the height of the text edit
        """
        doc_height: float = self.document().size().height()
        if doc_height > self.max_height:
            self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.setFixedHeight(self.max_height)
        else:
            self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.setFixedHeight(int(doc_height))

    def showEvent(self, event: QShowEvent) -> None:
        """
        QTextEdit show event
        """
        super().showEvent(event)
        self._adjustHeight()

    def text(self) -> str:
        """
        Returns the plaintext of the text edit
        """
        return self.toPlainText()


class QAutomatonInputOutput(QFrame):
    def __init__(self) -> None:
        super().__init__()

    def reset(self) -> None:
        raise NotImplementedError

    def simulationStep(self) -> None:
        raise NotImplementedError

    def getContent(self) -> bytes:
        raise NotImplementedError


class QAutomatonTokenIO(QAutomatonInputOutput):
    def __init__(self) -> None:
        super().__init__()
        self.input_edit: SmartTextEdit = SmartTextEdit()
        self.output_edit: SmartTextEdit = SmartTextEdit()
        self.input_edit.textChanged.connect(lambda: self.output_edit.setText(self.input_edit.text()))
        self.input_edit.verticalScrollBar().valueChanged.connect(lambda: self.output_edit.verticalScrollBar().setValue(self.input_edit.verticalScrollBar().value()))
        self.enableWidgets()
        main_layout = QQuickBoxLayout(QBoxDirection.TopToBottom)
        main_layout.addWidget(self.input_edit)
        main_layout.addWidget(self.output_edit)
        buttons_layout = QQuickBoxLayout(QBoxDirection.LeftToRight)
        self.add_token_button: QPushButton = QPushButton()
        self.add_token_button.setText("Add Token")
        self.remove_token_button: QPushButton = QPushButton()
        self.remove_token_button.setText("Remove Token")
        self.token_seperator_button: QPushButton = QPushButton()
        self.token_seperator_button.setText("Seperator: \";\"")
        buttons_layout.addWidget(self.add_token_button)
        buttons_layout.addWidget(self.remove_token_button)
        buttons_layout.addWidget(self.token_seperator_button)
        main_layout.addLayout(buttons_layout)
        self.setLayout(main_layout)

    def reset(self) -> None:
        ...

    def simulationStep(self) -> None:
        ...

    def getContent(self) -> bytes:
        ...

    def enableWidgets(self) -> None:
        self.output_edit.setEnabled(False)


if __name__ == "__main__":
    app = QApplication()
    widget = QAutomatonTokenIO()
    widget.show()
    exit(app.exec())
