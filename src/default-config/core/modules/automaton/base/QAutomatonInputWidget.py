from PySide6.QtWidgets import QApplication, QFrame, QTextEdit, QPushButton, QScrollArea, QLabel, QWidget, QLayoutItem, \
    QLayout, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt, QSize, QRect, QPoint
from PySide6.QtGui import QShowEvent, QTextCursor, QTextCharFormat, QColor

from aplustools.io.qtquick import QQuickBoxLayout, QBoxDirection, QNoSpacingBoxLayout


class QFlowLayout(QLayout):  # Not by me
    """
    A custom flow layout class that arranges child widgets horizontally and wraps as needed.
    """

    def __init__(self, parent=None, margin=0, hSpacing=6, vSpacing=6):
        super().__init__(parent)
        self.setContentsMargins(margin, margin, margin, margin)
        self.hSpacing = hSpacing
        self.vSpacing = vSpacing
        self.items = []

    def addItem(self, item):
        self.items.append(item)

    def horizontalSpacing(self) -> int:
        return self.hSpacing

    def verticalSpacing(self) -> int:
        return self.vSpacing

    def count(self) -> int:
        return len(self.items)

    def itemAt(self, index) -> QLayoutItem:
        if 0 <= index < len(self.items):
            return self.items[index]
        return None

    def takeAt(self, index) -> QLayoutItem:
        if 0 <= index < len(self.items):
            return self.items.pop(index)
        return None

    def expandingDirections(self) -> Qt.Orientations:
        return Qt.Horizontal | Qt.Vertical

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        return self.doLayout(QRect(0, 0, width, 0), testOnly=True)

    def setGeometry(self, rect: QRect):
        super().setGeometry(rect)
        self.doLayout(rect, testOnly=False)

    def sizeHint(self) -> QSize:
        return self.calculateSize()

    def minimumSize(self) -> QSize:
        return self.calculateSize()

    def calculateSize(self) -> QSize:
        size = QSize()
        for item in self.items:
            size = size.expandedTo(item.minimumSize())
        size += QSize(2 * self.contentsMargins().top(), 2 * self.contentsMargins().top())
        return size

    def doLayout(self, rect: QRect, testOnly: bool) -> int:
        x, y, lineHeight = rect.x(), rect.y(), 0

        for item in self.items:
            wid = item.widget()
            spaceX, spaceY = self.horizontalSpacing(), self.verticalSpacing()
            nextX = x + item.sizeHint().width() + spaceX
            if nextX - spaceX > rect.right() and lineHeight > 0:
                x = rect.x()
                y += lineHeight + spaceY
                nextX = x + item.sizeHint().width() + spaceX
                lineHeight = 0

            if not testOnly:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = nextX
            lineHeight = max(lineHeight, item.sizeHint().height())

        return y + lineHeight - rect.y()


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

    def simulationStep(self, output: list[str], index: int) -> None:
        raise NotImplementedError

    def getContent(self) -> bytes:
        raise NotImplementedError

    def set_input_tokens(self, tokens: list[str]) -> None:
        raise NotImplementedError


class QAutomatonTokenIO(QAutomatonInputOutput):
    def __init__(self) -> None:
        super().__init__()
        # Class Vars
        self._regulated_separators: list[str] = []
        self._separators: list[str] = [",", ":", ";", " ", ":", "|", "/", "\\"]
        self._active_separator: str = self._separators[0] if self._separators else ""
        self._previous_separator: str = self._active_separator
        self._input_tokens: list[str] = []
        self._error: str = ""

        # Layout
        main_layout = QQuickBoxLayout(QBoxDirection.TopToBottom)

        self.input_edit: SmartTextEdit = SmartTextEdit()
        self.output_edit: SmartTextEdit = SmartTextEdit()
        self.input_edit.textChanged.connect(lambda: (self.output_edit.setText(self.input_edit.text()),
                                                     self.output_edit.verticalScrollBar().setValue(
                                                         self.input_edit.verticalScrollBar().value()),
                                                     self._check_for_errors()))
        self.input_edit.verticalScrollBar().valueChanged.connect(
            lambda: self.output_edit.verticalScrollBar().setValue(self.input_edit.verticalScrollBar().value()))
        self.enableWidgets()

        self.error_text_edit: QTextEdit = QTextEdit("Hallo Sa")
        self.error_text_edit.setReadOnly(True)
        self.error_frame: QFrame = QFrame()
        self.error_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        self.error_frame.hide()
        error_frame_layout: QNoSpacingBoxLayout = QNoSpacingBoxLayout(QBoxDirection.LeftToRight,
                                                                      apply_layout_to=self.error_frame)
        error_frame_layout.addWidget(self.error_text_edit)

        main_layout.addWidget(self.error_frame)
        main_layout.addWidget(self.input_edit)
        main_layout.addWidget(self.output_edit)

        self.remove_token_button: QPushButton = QPushButton()
        self.remove_token_button.setText("Remove Token")
        self.remove_token_button.clicked.connect(self.remove_input_token)

        self.token_selector: QScrollArea = QScrollArea(self)
        self.token_selector.setWidgetResizable(True)
        # self.token_selector.setMaximumHeight(200)

        self.token_separator_selector: QScrollArea = QScrollArea(self)
        self.token_separator_selector.setWidgetResizable(True)
        self.token_separator_selector.setMinimumHeight(50)

        central_widget_tokens: QWidget = QWidget()
        self.token_selector_layout: QFlowLayout = QFlowLayout(central_widget_tokens)
        self.token_selector.setWidget(central_widget_tokens)

        central_widget_separator: QWidget = QWidget()
        self.token_separator_selector_layout: QFlowLayout = QFlowLayout(central_widget_separator)
        self.token_separator_selector.setWidget(central_widget_separator)

        # knopf

        for token in self._input_tokens:
            token_button: QPushButton = QPushButton()
            token_button.setText(token)
            token_button.clicked.connect(lambda checked, tok=token: self.add_input_token(tok))
            self.token_selector_layout.addWidget(token_button)

        self._update_separator_buttons()

        scroll_layout = QVBoxLayout()
        scroll_layout.addWidget(self.token_selector)
        scroll_layout.addWidget(self.token_separator_selector)

        scroll_layout.setStretch(0, 2)  # 2/3 für token_selector
        scroll_layout.setStretch(1, 1)  # 1/3 für token_separator_selector

        widget_layout = QQuickBoxLayout(QBoxDirection.LeftToRight)
        widget_layout.addLayout(scroll_layout)
        widget_layout.addWidget(self.remove_token_button)

        main_layout.addLayout(widget_layout)
        self.setLayout(main_layout)

    def display_text_error(self) -> None:
        if not self.get_error():
            return
        self.error_text_edit.setText(self.get_error())
        self._error = ""
        self.error_frame.show()

    def _hide_text_error(self) -> None:
        self._error = ""
        self.error_frame.hide()

    def reset(self) -> None:
        input_value = self.input_edit.text()
        self.output_edit.setText(input_value)

    def simulationStep(self, output: list[str], index: int, color: QColor = QColor("red")) -> None:  # TODO maybe rework
        """Colorizes the output at the given index"""
        output_str = self._active_separator.join(output)
        self.set_output(output_str)

        if index < 0 or index >= len(output):
            return

        # Calculation of the character index
        char_index = sum(len(word) + len(self._active_separator) for word in output[:index])

        # Move Cursor to output index
        cursor = self.output_edit.textCursor()
        cursor.movePosition(QTextCursor.Start)
        cursor.movePosition(QTextCursor.Right, QTextCursor.MoveAnchor, char_index)

        # color
        fmt = QTextCharFormat()
        fmt.setForeground(color)

        # colorize output at the given index
        cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, len(output[index]))
        cursor.mergeCharFormat(fmt)

    def getContent(self) -> bytes:
        return self.input_edit.text().encode()

    def enableWidgets(self) -> None:
        self.output_edit.setReadOnly(True)

    def add_error(self, error: str, is_generic: bool) -> None:
        if error in self._error:
            return
        if is_generic:
            self._error = error + "\n" + self._error
        else:
            self._error += error + "\n"
        print("ADDED ERRORS", error)

    def get_error(self) -> str:
        return self._error

    def clear_error(self) -> None:
        self._error = ""

    def set_input_tokens(self, tokens: list[str]) -> None:
        if self._input_tokens == tokens:
            return

        self._input_tokens = tokens

        # clear existing token buttons
        for i in range(self.token_selector_layout.count()):
            self.token_selector_layout.itemAt(i).widget().deleteLater()

        # add new token buttons
        for token in tokens:
            print(token)
            token_button: QPushButton = QPushButton()
            token_button.setText(token)
            token_button.clicked.connect(lambda checked, tok=token: self.add_input_token(tok))
            self.token_selector_layout.addWidget(token_button)

        self._input_token_changed()

    def get_input_tokens(self) -> list[str]:
        return self._input_tokens

    def set_output(self, output: str) -> None:
        self.output_edit.setText(output)

    def set_separator(self, separator: str) -> None:
        if separator not in self._separators:
            print(separator)
            raise ValueError(f"Separator {separator} not in separators")

        if separator in self._regulated_separators:
            return

        self._previous_separator = self._active_separator
        self._active_separator = separator
        self._separator_changed()

    def get_separator(self) -> str:
        return self._active_separator

    def get_separators(self) -> list[str]:
        return self._separators

    def set_separators(self, separators: list[str]) -> None:
        if self._separators == separators:
            return

        self._separators = separators
        self._separator_changed()
        self._update_separator_buttons()

    def _update_separator_buttons(self) -> None:
        # delete existing separator buttons
        while self.token_separator_selector_layout.count():
            item = self.token_separator_selector_layout.takeAt(0)  # Take the first item from the layout
            widget = item.widget()  # Get the widget
            if widget:
                widget.deleteLater()  # Delete the widget

        # add new separator buttons
        for separator in self._separators:
            token_separator_button: QPushButton = QPushButton()
            token_separator_button.setText(f"'{separator}'")
            token_separator_button.clicked.connect(lambda checked, sep=separator: self.set_separator(sep))
            self.token_separator_selector_layout.addWidget(token_separator_button)

    def _contents_changed(self) -> None:
        self._check_for_errors()

    def _separator_changed(self):
        print("separator changed", self._active_separator, self._previous_separator)
        # input:
        input_text = self.input_edit.text()

        input_tokens: list = [input_text]
        if self._previous_separator in input_text:
            input_tokens = input_text.split(self._previous_separator)

        input_text = self._active_separator.join(input_tokens)
        self.input_edit.setText(input_text)
        self._check_for_errors()

    def _input_token_changed(self) -> None:
        self._check_for_errors()

        for token in self._input_tokens:
            for separator in self._separators:
                if separator not in token:
                    continue
                self._regulated_separators.append(separator)

        self._update_separator_buttons()

    def remove_input_token(self) -> None:
        # Remove the latest token where the cursor is
        self._check_for_errors()

        print(f"removed token at {self.input_edit.textCursor().position()}")
        cursor = self.input_edit.textCursor()
        text = self.input_edit.toPlainText()
        if not text:
            return

        position = cursor.position()
        tokens: list[str] = text.split(self.get_separator())
        if not tokens:
            return

        start: int = 0
        end: int = 0
        for i, token in enumerate(tokens):
            if start + len(token) >= position:
                tokens.pop(i)
                end = start + len(token)
                break
            start += len(token) + len(self.get_separator())

        joined_text: str = self.get_separator().join(tokens)
        self.input_edit.setText(joined_text)

    def add_input_token(self, token: str) -> None:
        self._check_for_errors()

        if not self.getContent():
            self.input_edit.setText(token)
        else:
            if self.input_edit.text().endswith(self.get_separator()):
                self.input_edit.setText(self.input_edit.text() + token)
                return
            self.input_edit.setText(self.input_edit.text() + self.get_separator() + token)

    def _check_for_errors(self) -> None:
        print("error check")

        for token in self._input_tokens:
            for seperator in self._regulated_separators:
                if seperator in token:
                    self.add_error(f"Token '{token}' contains separator '{seperator}'", is_generic=True)

        # check for unknown tokens
        input_text = self.input_edit.text()
        for token in input_text.split(self.get_separator()):
            if not token:
                continue
            if token in self.get_input_tokens():
                continue
            self.add_error(f"Unknown token '{token}'", is_generic=True)

        if self.get_error():
            self.display_text_error()
        else:
            self._hide_text_error()
