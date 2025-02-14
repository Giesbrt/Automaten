class Section(QLineEdit):
    def __init__(self, section_width: int, handle_function, parent=None) -> None:
        super().__init__(parent)
        self.setMaxLength(1)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedSize(section_width, section_width)

        validator = QRegularExpressionValidator('[A-Z]')
        self.setValidator(validator)

        self.textChanged.connect(handle_function)

        self.setStyleSheet(f"""
            Section {{
                border: 1px solid #3498db;
                border-radius: 4px;
                background-color: rgba(25, 92, 137, 0.5);
                font-size: {section_width // 1.5}px;
                font-weight: bold;
                color: #ffffff;
                selection-background-color: #2980b9;
            }}
            Section:focus {{
                border: 1px solid #2980b9;
                background-color: rgba(52, 152, 219, 0.2);
            }}
        """)


class MultiSectionLineEdit(QWidget):
    def __init__(self, sections: int, set_condition=None, parent=None) -> None:
        """
        Initialize the multi-section line edit widget.

        Args:
            sections (int): The number of input sections.
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.sections = sections
        self.set_condition = set_condition
        self.layout = QHBoxLayout(self)
        self.layout.setSpacing(2)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.fields = []
        self.section_width = 30
        self.spacing = self.layout.spacing()
        self._create_fields()
        self._adjust_size()

    def _create_fields(self) -> None:
        """
        Create and configure the input fields for each section.

        Each field is set to accept a single uppercase character.
        """
        for _ in range(self.sections):
            field = Section(self.section_width, self._handle_text_change, self)
            field.setObjectName('section')
            self.fields.append(field)
            self.layout.addWidget(field)

    def _adjust_size(self) -> None:
        """
        Adjust the widget size based on the number of sections and spacing.

        This ensures that the widget's fixed size properly fits all input fields.
        """
        total_width = (self.section_width * self.sections) + self.spacing * (self.sections - 1)
        total_height = self.section_width
        self.setFixedSize(total_width, total_height)

    def _handle_text_change(self) -> None:
        """
        Handle the text change event in the input fields.

        When text is entered in a field, focus is automatically moved to the next field.
        """
        for i, field in enumerate(self.fields):
            if field.text() and i < len(self.fields) - 1:
                self.fields[i + 1].setFocus()

        if all(field.text() for field in self.fields):
            if self.set_condition:
                self.set_condition(self.get_text())

    def set_text(self, text: str) -> None:
        """
        Set the text for the multi-section input fields.

        Args:
            text (str): The text to set. Each character is assigned to a field sequentially.
        """
        for i, char in enumerate(text):
            if i < len(self.fields):
                self.fields[i].setText(char)

    def get_text(self) -> _ty.List[str]:
        """
        Retrieve the concatenated text from all input fields.

        Returns:
            _ty.List[str]: The combined text from each section.
        """
        return [field.text() for field in self.fields]