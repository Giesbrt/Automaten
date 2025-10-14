import stat

from PySide6.QtCore import QProcess
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QCheckBox, QVBoxLayout, QWidget, QPushButton, \
    QTextEdit, QLineEdit, QDialog, QHBoxLayout, QComboBox
from aplustools.io.env import OperatingSystem
import subprocess
import os.path
import sys

import typing as _ty

from dancer.qt import QQuickMessageBox, MBoxIcon


class QTerminal(QDialog):
    def __init__(self, absolute_script_path: str, operating_system: OperatingSystem, parent: QWidget | None = None, /,
                 auto_close: bool = True) -> None:
        super().__init__(parent=parent)
        self.setWindowTitle("Terminal Dialog")

        layout: QVBoxLayout = QVBoxLayout(self)

        self._output: QTextEdit = QTextEdit(readOnly=True)
        self._input: QLineEdit = QLineEdit()
        layout.addWidget(self._output)
        layout.addWidget(self._input)

        self._process: QProcess = QProcess(self)

        if operating_system == OperatingSystem.NT:
            self._process.setProgram("cmd.exe")
            self._process.setArguments(["/Q", "/C", f'"{absolute_script_path}"'])  # Quiet mode / no banner mode
        elif operating_system in {OperatingSystem.DARWIN, OperatingSystem.GNU_LINUX, OperatingSystem.BSD}:
            self._process.setProgram("bash")
            self._process.setArguments(["-c", f'"{absolute_script_path}"'])  # This is so to ensure spaces are dealt with
        else:
            raise RuntimeError(f"Unsupported OS: {operating_system}")

        self._error_occurred: bool = False
        self._process.errorOccurred.connect(lambda: setattr(self, "_error_occurred", True))
        self._process.finished.connect(self.complete)
        self._auto_close: bool = auto_close

        self._process.readyReadStandardOutput.connect(self._read_stdout)
        self._process.readyReadStandardError.connect(self._read_stderr)
        self._input.returnPressed.connect(self._send_input)

    def complete(self, exit_code: int, exit_status: QProcess.ExitStatus) -> None:
        if self._error_occurred or exit_code != 0 or exit_status == QProcess.ExitStatus.CrashExit:
            self._output.append("\nAn error occurred, please close this window.")
            return None
        elif not self._auto_close:
            self._output.append("\nThe program has exited, please close this window.")
            return None
        self.close()

    def _read_stdout(self) -> None:
        text: str = self._process.readAllStandardOutput().data().decode()
        self._output.append(text)
        return None

    def _read_stderr(self) -> None:
        text: str = self._process.readAllStandardError().data().decode()
        self._output.append(f"<span style='color:red;'>{text}</span>")
        return None

    def _send_input(self) -> None:
        inp: str = self._input.text() + "\n"
        self._process.write(inp.encode("utf-8"))
        self._input.clear()
        return None

    def send_inputs(self, inps: list[str]) -> None:
        for inp in inps:
            self._process.write((inp + "\n").encode("utf-8"))
        return None

    def start(self) -> None:
        self._process.start()
        return None

    def closeEvent(self, arg__1, /):
        """Ensure QProcess is terminated before closing the window."""
        if self._process and self._process.state() != QProcess.ProcessState.NotRunning:
            self._process.terminate()
            if not self._process.waitForFinished(3000):  # wait up to 3s
                self._process.kill()
        super().closeEvent(arg__1)


class AIOWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("AIO Assistant")

        central: QWidget = QWidget()
        main_layout = QVBoxLayout(central)
        # main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)

        self.os: OperatingSystem = OperatingSystem.detect()

        if self.os is OperatingSystem.NT:
            nt_script_type_layout: QHBoxLayout = QHBoxLayout()
            nt_script_type_layout.setContentsMargins(0, 0, 0, 0)
            nt_script_type_layout.addWidget(QLabel("NT Script Type:"))
            self.nt_script_type_combobox: QComboBox = QComboBox(self)
            self.nt_script_type_combobox.addItems(["Batch", "PowerShell"])
            nt_script_type_layout.addWidget(self.nt_script_type_combobox)
            main_layout.addLayout(nt_script_type_layout)
        else:
            self.nix_checkbox: QCheckBox = QCheckBox("Is Nix", self)
            self.nix_checkbox.setChecked(self._is_nixos())
            main_layout.addWidget(self.nix_checkbox)

        main_layout.addWidget(QLabel(text="Run"))

        install_env_layout: QHBoxLayout = QHBoxLayout()
        install_env_layout.setContentsMargins(0, 0, 0, 0)
        install_env_btn: QPushButton = QPushButton("Install Python Environment")
        install_env_btn.clicked.connect(self.install_environment)
        install_env_layout.addWidget(install_env_btn)

        self.install_env_reinstall_checkbox: QCheckBox = QCheckBox("Reinstall", self)
        install_env_layout.addWidget(self.install_env_reinstall_checkbox)

        main_layout.addLayout(install_env_layout)

        run_btn: QPushButton = QPushButton("Run NEFS")
        run_btn.clicked.connect(self.start_app)
        main_layout.addWidget(run_btn)

        test_btn: QPushButton = QPushButton("Test NEFS")
        test_btn.clicked.connect(self.test_app)
        main_layout.addWidget(test_btn)

        self.setCentralWidget(central)

    @staticmethod
    def _is_nixos() -> bool:
        try:
            with open("/etc/os-release") as f:
                for line in f:
                    if line.strip().startswith("ID=") and "nixos" in line:
                        return True
        except FileNotFoundError:
            return False
        return False

    def _unknown_or_unsupported_os(self) -> None:
        box = QQuickMessageBox(self, MBoxIcon.Warning, "Warn: Unknown or unsupported OS",
                               f"The operating system ({self.os.value}) you are currently using is unknown or unsupported.")
        box.exec()
        return None

    def _create_subprocess_dialog(self, relative_script_path: str, inps: list[str], auto_close: bool) -> bool:
        try:
            abs_path: str = os.path.abspath(relative_script_path)
            if not os.path.exists(abs_path):
                box = QQuickMessageBox(self, MBoxIcon.Critical, "Error: Script not found",
                                       f"Could not find script:\n{abs_path}")
                box.exec()
                return False
            elif not os.access(abs_path, os.X_OK):
                if self.os != OperatingSystem.NT:
                    try:
                        st = os.stat(abs_path)
                        os.chmod(abs_path, st.st_mode | stat.S_IXUSR)
                    except Exception as e:
                        box = QQuickMessageBox(self, MBoxIcon.Critical, "Error: Script not executable",
                                               f"Could not execute script:\n{abs_path}, due to error {e}")
                        box.exec()
                        return False
                else:
                    box = QQuickMessageBox(self, MBoxIcon.Critical, "Error: Script not executable",
                                           f"Could not execute script:\n{abs_path}")
                    box.exec()
                    return False
            dialog: QTerminal = QTerminal(abs_path, self.os, self, auto_close=auto_close)
            dialog.start()
            dialog.send_inputs(inps)
            dialog.show()
        except Exception as e:
            box = QQuickMessageBox(self, MBoxIcon.Critical, "Error: Unknown", f"{e}")
            box.exec()
            return False
        return True

    def _execute_script(self, name: str, arg_count: int, /, auto_close: bool = True, extra_nix: bool = False) -> bool:
        if self.install_env_reinstall_checkbox.isChecked():
            inps = ["y"] * arg_count
        else:
            inps = [""] * arg_count

        result: bool = False
        match self.os:
            case OperatingSystem.NT:
                ext: str = {"Batch": "bat", "PowerShell": "ps1"}[self.nt_script_type_combobox.currentText()]
                os.chdir("nt")
                result = self._create_subprocess_dialog(f"{name}.{ext}", inps, auto_close)
                os.chdir("../")
            case OperatingSystem.UNKNOWN:
                self._unknown_or_unsupported_os()
            case _:
                os.chdir("unix")
                if self.nix_checkbox.isChecked() and extra_nix:
                    result = self._create_subprocess_dialog(f"nix-{name}.sh", inps, auto_close)
                else:
                    result = self._create_subprocess_dialog(f"{name}.sh", inps, auto_close)
                os.chdir("../")
        return result

    def install_mainpkg(self, method: _ty.Literal["editable", "symlink"]) -> bool:
        if method == "symlink":
            box = QQuickMessageBox(self, MBoxIcon.Warning, "Warn: Unsupported method",
                                   f"The symlink method is not yet supported.")
            box.exec()
            return None
        else:
            return self._execute_script("install-mainpkg", 0, extra_nix=True)

    def count_loc(self) -> int:
        ...

    def compile_app(self, graphically: bool) -> bool:
        ...  #! Include the automatic paths to remove fix in the shell!!

    def test_app(self) -> bool:
        return self._execute_script("run-tests", 0, auto_close=False, extra_nix=True)

    def install_environment(self) -> bool:
        return self._execute_script("python", 4, extra_nix=True) and self.install_mainpkg("editable")

    def start_app(self) -> bool:
        return self._execute_script("start", 0, extra_nix=True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    wind = AIOWindow()
    wind.show()
    sys.exit(app.exec())
