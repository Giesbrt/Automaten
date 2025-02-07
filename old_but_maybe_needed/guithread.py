import sys
import threading
from queue import Queue
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QPushButton, QWidget
from PySide6.QtCore import QTimer


class GuiApp(QMainWindow):
    """PySide6 GUI running in its own thread."""
    def __init__(self, queue: Queue):
        super().__init__()
        self.queue = queue
        self.setWindowTitle("PySide6 in a Side Thread")

        # Layout and widgets
        self.label = QLabel("Waiting for CLI updates...")
        self.button = QPushButton("Send Message to CLI")
        self.button.clicked.connect(self.send_message_to_cli)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.button)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Timer to check for CLI messages
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_updates)
        self.timer.start(100)

    def send_message_to_cli(self):
        """Send a message to the CLI thread."""
        self.queue.put("Message from GUI")

    def check_updates(self):
        """Check the queue for messages from the CLI."""
        while not self.queue.empty():
            msg = self.queue.get()
            self.label.setText(msg)


def start_gui(queue: Queue):
    """Run the PySide6 application in a separate thread."""
    app = QApplication(sys.argv)
    window = GuiApp(queue)
    window.show()
    app.exec()


def cli_main(queue: Queue):
    """CLI main loop running in the main thread."""
    while True:
        user_input = input("CLI> ")
        if user_input == "exit":
            queue.put("exit")
            break
        elif user_input == "start_gui":
            queue.put("start_gui")
        else:
            queue.put(f"CLI says: {user_input}")


if __name__ == "__main__":
    message_queue = Queue()

    # Start the GUI in a side thread
    gui_thread = threading.Thread(target=start_gui, args=(message_queue,))
    gui_thread.start()

    # Start the CLI in the main thread
    cli_main(message_queue)

    # Wait for the GUI thread to finish
    gui_thread.join()
