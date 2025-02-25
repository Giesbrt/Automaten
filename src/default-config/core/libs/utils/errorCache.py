"""TBA"""

from utils.OrderedSet import OrderedSet
from aplustools.io import ActLogger
from queue import Queue
from utils.staticContainer import StaticContainer
from logging import ERROR, WARNING, INFO, DEBUG
# import src.config as config

# Standard typing imports for aps
import collections.abc as _a
import abc as _abc
import typing as _ty
import types as _ts


class ErrorSeverity:
    FATAL = "fatal"
    NORMAL = "normal"

    def __str__(self) -> str:
        """
        Returns the string representation of the ErrorSeverity.
        :return: A string representing the error severity.
        """
        return "undefined"

    def __repr__(self) -> str:
        """
        Returns the string representation of the ErrorSeverity for debugging.
        :return: A string representing the error severity.
        """
        return self.__str__()


class ErrorCache:
    _do_not_show_again: OrderedSet[str] = OrderedSet()
    _currently_displayed: OrderedSet[str] = OrderedSet()
    _button_display_callable: StaticContainer[_ty.Callable] = StaticContainer()
    _is_indev: StaticContainer[bool] = StaticContainer()
    _popup_queue: _ty.List[_ty.Callable] = []

    _logger: ActLogger = ActLogger()

    def __init__(self) -> None:
        pass

    def has_cached_errors(self) -> bool:
        """
        Returns if there are popups cached which have not been displayed yet
        :return: bool
        """
        return len(self._popup_queue) > 0

    def invoke_popup(self) -> None:
        """

        :return:
        """
        if not self.has_cached_errors():
            return

        popup_callable: _ty.Callable = self._popup_queue[0]
        self._popup_queue.pop(0)

        popup_callable()

    def init(self, popup_creation_callable: _ty.Callable, is_indev: bool) -> None:
        """
        Initializes the ErrorCache with a popup creation callable and development mode flag.
        :param popup_creation_callable: Callable used to create popups.
        :param is_indev: Boolean indicating whether the application is in development mode.
        :return: None
        """
        self._button_display_callable.set_value(popup_creation_callable)

        self._is_indev.set_value(is_indev)

    def _show_dialog(self, title: str, text: str, description: str,
                     icon: _ty.Literal["Information", "Critical", "Question", "Warning", "NoIcon"],
                     custom_buttons: _ty.Dict[str, _ty.Callable] | None = None) -> None:
        """
        Displays a dialog box with the provided information.
        :param title: Title of the dialog box.
        :param text: Main text content of the dialog box.
        :param description: Additional description text.
        :param icon: Type of icon to display in the dialog box.
        :return: None
        """
        if text in self._currently_displayed:
            # Error is currently displayed
            return

        if text in self._do_not_show_again:
            # Error should not be displayed again
            return

        if not self._button_display_callable.has_value():
            return

        self._currently_displayed.add(text)

        checkbox_text: str = "Do not show again"
        buttons_list: _ty.List[str] = ["Ok"]
        default_button: str = buttons_list[0]

        # add custom buttons
        if custom_buttons is not None:
            for key in list(custom_buttons.keys()):
                buttons_list.append(key)

        popup_creation_callable: _ty.Callable = self._button_display_callable.get_value()
        popup_return: tuple[str | None, bool] = popup_creation_callable(title, text, description, icon,
                                                                        buttons_list, default_button, checkbox_text)

        if popup_return[1]:
            self._do_not_show_again.add(text)
        self._currently_displayed.remove(text)

        # invoke button commands
        button_name: str = popup_return[0]
        if custom_buttons is not None:
            if button_name in custom_buttons:
                custom_buttons[button_name]()

    def _handle_dialog(self, show_dialog: bool, title: str, log_message: str, description: str,
                       icon: _ty.Literal["Information", "Critical", "Question", "Warning", "NoIcon"],
                       custom_buttons: _ty.Dict[str, _ty.Callable] | None = None) -> None:
        """
        Handles the process of displaying a dialog based on parameters.
        :param show_dialog: Boolean indicating whether to show the dialog.
        :param title: Title of the dialog.
        :param log_message: Log message associated with the dialog.
        :param description: Additional description text.
        :param icon: Type of icon to display in the dialog.
        :return: None
        """
        if not show_dialog:
            return

        self._popup_queue.append(lambda: self._show_dialog(title, log_message, description, icon, custom_buttons))

    # "Errors"

    def warn(self, log_message: str, description: str, show_dialog: bool = False,
             print_log: bool = True,
             icon: _ty.Literal["Information", "Critical", "Question", "Warning", "NoIcon"] = "Warning",
             popup_title: str | None = None,
             custom_buttons: _ty.Dict[str, _ty.Callable] | None = None) -> None:
        """
        Logs a warning message and optionally displays a warning dialog.
        :param popup_title: Sets the popup window title
        :param custom_buttons: Defines additional buttons for the popup window
        :param log_message: The warning message to log.
        :param description: Additional description of the warning.
        :param show_dialog: Whether to show a dialog for the warning.
        :param print_log: Whether to print the log message.
        :param icon: Icon type for the dialog.
        :return: None
        """
        return self.warning(log_message, description, show_dialog, print_log, icon, popup_title, custom_buttons)

    def info(self, log_message: str, description: str, show_dialog: bool = False,
             print_log: bool = True,
             icon: _ty.Literal["Information", "Critical", "Question", "Warning", "NoIcon"] = "Information",
             popup_title: str | None = None,
             custom_buttons: _ty.Dict[str, _ty.Callable] | None = None) -> None:
        """
        Logs an informational message and optionally displays an information dialog.
        :param log_message: The informational message to log.
        :param description: Additional description of the information.
        :param show_dialog: Whether to show a dialog for the information.
        :param print_log: Whether to print the log message.
        :param icon: Icon type for the dialog.
        :param popup_title: Sets the popup window title
        :param custom_buttons: Defines additional buttons for the popup window
        :return: None
        """
        title: str = "Information"
        if popup_title is not None:
            title += f": {popup_title}"

        if print_log:
            self._logger.info(f"{log_message} {f'({description})' if description else ''}")

        if ActLogger().logging_level >= INFO:
            return

        self._handle_dialog(show_dialog, title, log_message, description, icon, custom_buttons)

    def warning(self, log_message: str, description: str, show_dialog: bool = False,
                print_log: bool = True,
                icon: _ty.Literal["Information", "Critical", "Question", "Warning", "NoIcon"] = "Warning",
                popup_title: str | None = None,
                custom_buttons: _ty.Dict[str, _ty.Callable] | None = None) -> None:
        """
        Logs a warning message and optionally displays a warning dialog.
        :param log_message: The warning message to log.
        :param description: Additional description of the warning.
        :param show_dialog: Whether to show a dialog for the warning.
        :param print_log: Whether to print the log message.
        :param icon: Icon type for the dialog.
        :param popup_title: Sets the popup window title
        :param custom_buttons: Defines additional buttons for the popup window
        :return: None
        """
        title: str = "Warning"
        if popup_title is not None:
            title += f": {popup_title}"

        if print_log:
            self._logger.warning(f"{log_message} {f'({description})' if description else ''}")

        if ActLogger().logging_level >= WARNING:
            return

        self._handle_dialog(show_dialog, title, log_message, description, icon, custom_buttons)

    def error(self, log_message: str, description: str, show_dialog: bool = False,
              print_log: bool = True,
              error_severity: ErrorSeverity = ErrorSeverity.NORMAL,
              icon: _ty.Literal["Information", "Critical", "Question", "Warning", "NoIcon"] = "Critical",
              popup_title: str | None = None,
              custom_buttons: _ty.Dict[str, _ty.Callable] | None = None) -> None:
        """
        Logs an error message and optionally displays an error dialog.
        :param log_message: The error message to log.
        :param description: Additional description of the error.
        :param show_dialog: Whether to show a dialog for the error.
        :param print_log: Whether to print the log message.
        :param error_severity: Severity level of the error.
        :param icon: Icon type for the dialog.
        :param popup_title: Sets the popup window title
        :param custom_buttons: Defines additional buttons for the popup window
        :return: None
        """
        title: str = f"{str(error_severity).capitalize()} Error"
        if popup_title is not None:
            title += f": {popup_title}"

        if print_log:
            self._logger.error(f"{str(error_severity)}: {log_message} {f'({description})' if description else ''}")

        if ActLogger().logging_level >= ERROR:
            return

        self._handle_dialog(show_dialog, title, log_message, description, icon, custom_buttons)

    def debug(self, log_message: str, description: str, show_dialog: bool = False,
              print_log: bool = True,
              icon: _ty.Literal["Information", "Critical", "Question", "Warning", "NoIcon"] = "Information",
              popup_title: str | None = None,
              custom_buttons: _ty.Dict[str, _ty.Callable] | None = None) -> None:
        """
        Logs a debug message and optionally displays a debug dialog, only if in development mode.
        :param log_message: The debug message to log.
        :param description: Additional description of the debug information.
        :param show_dialog: Whether to show a dialog for the debug information.
        :param print_log: Whether to print the log message.
        :param icon: Icon type for the dialog.
        :param popup_title: Sets the popup window title
        :param custom_buttons: Defines additional buttons for the popup window
        :return: None
        """
        if not self._is_indev.has_value():
            return

        INDEV: bool = self._is_indev.get_value()  # config.INDEV
        if not INDEV:
            return

        title: str = "Debug"
        if popup_title is not None:
            title += f": {popup_title}"

        if print_log:
            self._logger.debug(f"{log_message} {f'({description})' if description else ''}")

        if ActLogger().logging_level >= DEBUG:
            return

        self._handle_dialog(show_dialog, title, log_message, description, icon, custom_buttons)
