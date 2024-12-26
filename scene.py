from PySide6.QtWidgets import QApplication, QMainWindow, QScrollArea, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt

class ScrollArea(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Scroll Area Test")
        self.setGeometry(100, 100, 400, 300)

        # Create a central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create a scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        # Create a content widget for the scroll area
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_widget.setLayout(content_layout)

        # Add widgets to the content widget (larger than the scroll area)
        for i in range(20):
            row_layout = QHBoxLayout()
            for j in range(10):
                button = QPushButton(f"Button {i},{j}")
                row_layout.addWidget(button)
            content_layout.addLayout(row_layout)

        # Set the content widget to the scroll area
        scroll_area.setWidget(content_widget)

        # Add the scroll area to the central widget layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(scroll_area)
        central_widget.setLayout(main_layout)

if __name__ == "__main__":
    app = QApplication([])
    window = ScrollArea()
    window.setStyleSheet("""
            QScrollBar:horizontal {
                border: none;
                background-color: transparent;
                height: 15px;
                border-radius: 7px;
            }
            QScrollBar::handle:horizontal {
                background-color: #aaaaaa;
                min-height: 15px;
                min-width: 40px;
                border-radius: 7px;
            }
            QScrollBar::handle:hover {
                background-color: #888888;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                border: none;
                background: none;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }

            QScrollBar:vertical {
                border: none;
                background-color: transparent;
                width: 15px;
                border-radius: 7px;
                /*border-top-right-radius: 10px;
                border-bottom-right-radius: 10px;*/
            }
            QScrollBar::handle:vertical {
                background-color: #e0e0e0;
                min-height: 20px;
                border-radius: 7px;
            }
            QScrollBar::handle:hover {
                background-color: #c0c0c0;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }

            QScrollBar::corner {
                border: none;
            }
    """)
    window.show()
    app.exec()
