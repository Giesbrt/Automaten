from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLineEdit,
                               QLabel, QScrollBar,
                               QApplication, QProgressDialog, QWidget, QListWidget, QSizePolicy, QListWidgetItem,
                               QStyledItemDelegate, QComboBox, QLayout)
from PySide6.QtCore import Qt, Signal, QThread, QTimer, Slot, QSize, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPainter, QBrush, QColor, QPen, QPalette, QIcon, QPixmap, QFont, QWheelEvent
from aplustools.io import environment as env
from typing import Literal
import threading
import importlib
import random
import ctypes
import queue
import time
import os
from aplustools.package.timid import TimidTimer


class CustomLabel(QLabel):
    def paintEvent(self, event):
        painter = QPainter(self)

        if self.text():
            main_window = self.window()
            while main_window.parent() is not None:
                main_window = main_window.parent()
            # If the label has text, apply background color based on the current theme
            if main_window.theme == "light":
                painter.setBrush(QBrush(QColor('#d0d0d0')))
            else:
                painter.setBrush(QBrush(QColor('#555555')))

            painter.setPen(QPen(Qt.NoPen))  # No border outline
            radius = 5
            painter.drawRoundedRect(self.rect(), radius, radius)

        painter.end()
        # super().paintEvent(event)


class TaskRunner(QThread):
    task_completed = Signal(bool, object)
    progress_signal = Signal(int)

    def __init__(self, new_thread, func, *args, **kwargs):
        super().__init__()
        self.new_thread = new_thread
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.is_running = True
        self.worker_thread = None
        self.result = None
        self.success = False
        if new_thread:
            self.progress_queue = queue.Queue()

    class TaskCanceledException(Exception):
        """Exception to be raised when the task is canceled"""
        def __init__(self, message="A intended error occured"):
            self.message = message
            super().__init__(self.message)

    def run(self):
        if not self.is_running:
            return

        try:
            if self.new_thread:
                self.worker_thread = threading.Thread(target=self.worker_func)
                self.worker_thread.start()
                while self.worker_thread.is_alive():
                    try:
                        progress = self.progress_queue.get_nowait()
                        self.progress_signal.emit(progress)
                    except queue.Empty:
                        pass
                    self.worker_thread.join(timeout=0.1)
                print("Worker thread died. Emitting result now ...")
            else:
                print("Directly executing")
                update = False
                for update in self.func(*self.args, **self.kwargs)():
                    if isinstance(update, int):
                        self.progress_signal.emit(update)
                self.result = update
                print("RES", self.result)
            self.task_completed.emit(self.success, self.result)

        except Exception as e:
            self.task_completed.emit(False, None)
            print(e)

    def worker_func(self):
        try:
            if self.new_thread:
                self.result = self.func(*self.args, **self.kwargs, progress_queue=self.progress_queue)
            else:
                return self.func(*self.args, **self.kwargs)
            self.success = True
        except SystemExit:
            self.success = False
            self.result = None
            print("Task was forcefully stopped.")
        except Exception as e:
            self.success = False
            self.result = None
            print(f"Error in TaskRunner: {e}")

    def stop(self):
        print("Task is stopping.")
        self.is_running = False
        if not self.isFinished():
            self.raise_exception()
            self.wait()

    def get_thread_id(self):
        if self.worker_thread:
            return self.worker_thread.ident

    def raise_exception(self):
        thread_id = self.get_thread_id()
        if thread_id:
            res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread_id), ctypes.py_object(SystemExit))
            if res > 1:
                ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
                print("Exception raise failure")


class CustomProgressDialog(QProgressDialog):
    def __init__(self, parent, window_title, window_icon, window_label="Doing a task...", button_text="Cancel",
                 new_thread=True, func=lambda: None, *args, **kwargs):
        super().__init__(parent=parent, cancelButtonText=button_text, minimum=0, maximum=100)
        self.ttimer = TimidTimer()
        self.setWindowTitle(window_title)
        # self.setValue(0)
        # self.setWindowIcon(QIcon(window_icon))

        self.customLayout = QVBoxLayout(self)
        self.customLabel = QLabel(window_label, self)
        self.customLayout.addWidget(self.customLabel)
        self.customLayout.setAlignment(self.customLabel, Qt.AlignTop | Qt.AlignHCenter)

        self.taskRunner = TaskRunner(new_thread, func, *args, **kwargs)
        self.taskRunner.task_completed.connect(self.onTaskCompleted)
        self.taskRunner.progress_signal.connect(self.set_value)  # Connect progress updates
        self.task_successful = False

        self.setAutoClose(False)
        self.setAutoReset(False)
        self.setWindowModality(Qt.ApplicationModal)
        self.canceled.connect(self.cancelTask)
        self.show()

        self.last_value = 0
        self.current_value = 0
        QTimer.singleShot(50, self.taskRunner.start)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateProgress)
        self.timer.start(100)
        print(self.ttimer.tick(), "INIT DONE")

    def updateProgress(self):
        if self.value() <= 100 and not self.wasCanceled() and self.taskRunner.isRunning():
            if self.current_value == 0 and self.value() < 10:
                self.setValue(self.value() + 1)
                time.sleep(random.randint(2, 10) * 0.1)
            elif self.current_value >= 10:
                self.smooth_value()
            QApplication.processEvents()

    def set_value(self, v):
        self.current_value = v

    def smooth_value(self):
        # If the difference is significant, set the value immediately
        if abs(self.current_value - self.last_value) > 10:  # You can adjust this threshold
            self.setValue(self.current_value)
            self.last_value = self.current_value
            return

        for i in range(max(10, self.last_value), self.current_value):
            self.setValue(i + 1)
            self.last_value = i + 1
            time.sleep(0.1)
        # print(f"Exiting go_to_value with value {self.current_value} and last_value {self.last_value}") # Debug

    def resizeEvent(self, event):
        super(CustomProgressDialog, self).resizeEvent(event)

        # Attempt to find the label as a child widget
        label: QLabel = self.findChild(QLabel)
        if label:
            label.setStyleSheet("""background: transparent;""")

    @Slot(bool, object)
    def onTaskCompleted(self, success, result):
        print("Task completed method called.")
        self.taskRunner.quit()
        self.taskRunner.wait()

        if not self.wasCanceled():
            if success:
                self.task_successful = True
                self.setValue(100)
                print("Task completed successfully! Result:" + str(
                    "Finished" if result else "Not finished"))  # Adjust as needed
                QTimer.singleShot(1000, self.accept)  # Close after 1 second if successful
            else:
                palette = QPalette(self.palette())
                palette.setColor(QPalette.Highlight, QColor(Qt.red))
                self.setPalette(palette)
                self.customLabel.setText("Task failed!")
                self.setCancelButtonText("Close")
        print("DONE", self.ttimer.end())

    def cancelTask(self):
        self.taskRunner.stop()
        self.taskRunner.wait()
        self.setValue(0)
        self.customLabel.setText("Task cancelled")
        self.close()

    def closeEvent(self, event):
        if self.taskRunner.isRunning():
            self.cancelTask()
        event.accept()


class ImageLabel(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class SearchResultItem(QWidget):
    def __init__(self, title, description, icon_path):
        super().__init__()

        self.layout = QHBoxLayout(self)

        self.icon_label = QLabel(self)
        self.icon_label.setPixmap(QPixmap(icon_path).scaledToWidth(50, Qt.SmoothTransformation))
        self.layout.addWidget(self.icon_label)

        self.text_layout = QVBoxLayout()
        self.title_label = QLabel(title)
        self.title_label.setFont(QFont('Arial', 14, QFont.Bold))
        self.text_layout.addWidget(self.title_label)

        self.description_label = QLabel(description)
        self.description_label.setFont(QFont('Arial', 10))
        self.text_layout.addWidget(self.description_label)

        self.layout.addLayout(self.text_layout)


class QNoSpacingVBoxLayout(QVBoxLayout):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(0)


class QNoSpacingHBoxLayout(QHBoxLayout):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(0)


class AutoProviderManager:
    def __init__(self, path, prov_plug, prov_sub_plugs: list):
        self.path = path
        self.prov_plug = prov_plug
        self.prov_sub_plugs = prov_sub_plugs
        self.providers = self._load_providers()

    def _load_providers(self):
        providers = {}
        for file in os.listdir(self.path):
            if file.endswith('.py') or file.endswith('.pyd') and file != '__init__.py':
                module_name = file.split(".")[0]
                module_path = os.path.join(self.path, file)
                spec = importlib.util.spec_from_file_location(module_name, module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                for attribute_name in dir(module):
                    attribute = getattr(module, attribute_name)
                    if (isinstance(attribute, type) and issubclass(attribute, self.prov_plug) and attribute not in
                            self.prov_sub_plugs):
                        providers[attribute_name] = attribute
        return providers

    def get_providers(self):
        return self.providers


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = QAdvancedSmoothScrollingArea()
    window.setWindowTitle('Custom Scroll Area')
    window.setGeometry(100, 100, 300, 200)

    # Add some example content
    for i in range(20):
        label = QLabel(f"Item {i}" * 30)
        window.content_layout.addWidget(label)

    window.show()
    sys.exit(app.exec_())
