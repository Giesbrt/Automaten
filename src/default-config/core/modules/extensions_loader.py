import os
import glob
import importlib
import sys
import json
import inspect
from datetime import datetime
import ast
import textwrap
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.modules.automaton.base.state import State as BaseState
from core.modules.automaton.base.transition import Transition as BaseTransition
from core.modules.automaton.base.automaton import Automaton as BaseAutomaton
from core.modules.automaton.base.settings import Settings as BaseSettings


sys.path.append(os.path.join(os.path.dirname(__file__), 'extensions'))

class Extensions_Loader:
    def __init__(self, base_dir: str):
        self.base_dir: str = base_dir
        self.cache_path = os.path.join(base_dir, "ext_cache")
        if not os.path.exists(self.cache_path):
            os.mkdir(self.cache_path)
            with open(os.path.join(self.cache_path, "cache.json"), 'w') as file:
                json.dump({"modules": []}, file, indent=4)
        if not os.path.exists(os.path.join(self.cache_path, "cache.json")):
            with open(os.path.join(self.cache_path, "cache.json"), 'w') as file:
                json.dump({"modules": []}, file, indent=4)
        open(os.path.join(self.cache_path, "log_file.log"), "a").close()
        with open(os.path.join(self.cache_path, "cache.json"), 'r') as file:
            self.data = json.load(file)
        if "modules" not in self.data:
            self.data["modules"] = []
        self.content: dict = {}
        self.log_file = os.path.join(self.cache_path, "log_file.log")

    def get_content(self):
        return self.content
    
    def remove_dublicates(self):

        module_aliases = {}

        for mod_name in list(sys.modules.keys()):
            parts = mod_name.split('.')

            for i in range(1, len(parts)):
                alias = ".".join(parts[i:]) 
                if alias in sys.modules and sys.modules[alias] is sys.modules[mod_name]:
                    module_aliases[alias] = mod_name

        for alias, full_name in module_aliases.items():
            sys.modules[alias] = sys.modules[full_name] 

        for mod_name in set(module_aliases.values()):
            importlib.reload(sys.modules[mod_name])


    def save_log_report(self, module_name, error_message, details="", suggestion="", max_logs = 10):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = (
            f"[{timestamp}] Error in: {module_name}\n"
            f"Description: {error_message}\n"
        )
        if details:
            log_entry += f"Details: {details}\n"
        if suggestion:
            log_entry += f"possible Solution: {suggestion}\n"

        log_entry += "-" * 80 + "\n"
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                logs = f.readlines()
        except FileNotFoundError:
            logs = []
            
        log_blocks = "".join(logs).split("-" * 80 + "\n")
        log_blocks = [log.strip() for log in log_blocks if log.strip()] 

        log_blocks.append(log_entry.strip())
        for i in range(len(log_blocks)):
            if i != len(log_blocks) - 1:
                log_blocks[i] = log_blocks[i] + "\n" + "-" * 80
        if len(log_blocks) > max_logs:
            log_blocks = log_blocks[-max_logs:]

        with open(self.log_file, "w", encoding="utf-8") as f:
            f.write("\n".join(log_blocks) + "\n")

    def clear_cache(self): 
        with open(os.path.join(self.cache_path, "cache.json"), 'w') as file:
                json.dump({"modules": []}, file, indent=4)
        
    def sort_list(self, classes, element, position = None):
        self.remove_dublicates()
        if position == None:
            if issubclass(element, BaseAutomaton):
                position = 0
            elif issubclass(element, BaseState):
                position = 1
            elif issubclass(element, BaseTransition):
                position = 2
            elif issubclass(element, BaseSettings):
                position = 3
            else: 
                position = len(classes)
        while len(classes) <= position:
            classes.append(None)  

        classes[position] = element
        return classes
    
    def check_module(self, module):
        importlib.reload(module)
        self.remove_dublicates()
        
        classes_in_module = []
        classes = [(name, obj) for name, obj in inspect.getmembers(module, inspect.isclass)]
        for name, element in classes:
            if element.__module__ == module.__name__:
                classes_in_module.append((name, element))
        
        required_checks = {
            "State": False,
            "Automaton": False,
            "Transition": False,
            "Settings": False
        }
        
        for name, element in classes_in_module:
            if issubclass(element, BaseState):
                if not required_checks["State"]:
                    implemented_methods = {name for name, _ in inspect.getmembers(element, inspect.isroutine)}
                    abstract_methods = BaseState.__abstractmethods__
                    for method in abstract_methods:
                        if method not in implemented_methods:
                            self.save_log_report(f"{name} in module {module.__name__}", f"{method} is not implemented.", "Abstract methods have to be implemented. Please implement this method.")
                            return False
                    if self.check_for_constructor(element, name, module):
                        required_checks["State"] = True
                    else:
                        return False
                else:
                    self.save_log_report(f"{name} in module {module.__name__}", f"There are multiple {name} Classes.",
                                         "These classes can only exist once")
                    return False
            elif issubclass(element, BaseAutomaton):
                if not required_checks["Automaton"]:
                    implemented_methods = {name for name, _ in inspect.getmembers(element, inspect.isroutine)}
                    abstract_methods = BaseAutomaton.__abstractmethods__
                    for method in abstract_methods:
                        if method not in implemented_methods:
                            self.save_log_report(f"{name} in module {module.__name__}", f"{method} is not implemented.", "Abstract methods have to be implemented. Please implement this method.")
                            return False
                    if self.check_for_constructor(element, name, module):
                        required_checks["Automaton"] = True
                    else:
                        return False
                else:
                    self.save_log_report(f"{name} in module {module.__name__}", f"There are multiple {name} Classes.",
                                         "These classes can only exist once")
                    return False
            elif issubclass(element, BaseTransition):
                if not required_checks["Transition"]:
                    implemented_methods = {name for name, _ in inspect.getmembers(element, inspect.isfunction)}
                    abstract_methods = BaseTransition.__abstractmethods__
                    for method in abstract_methods:
                        if method not in implemented_methods:
                            self.save_log_report(f"{name} in module {module.__name__}", f"{method} is not implemented.", "Abstract methods have to be implemented. Please implement this method.")
                            return False
                        
                    if self.check_for_constructor(element, name, module):
                        required_checks["Transition"] = True
                    else:
                        return False
                else:
                    self.save_log_report(f"{name} in module {module.__name__}", f"There are multiple {name} Classes.", "These classes can only exist once")
                    return False
            elif issubclass(element, BaseSettings):
                if not required_checks["Settings"]:
                    if self.check_for_constructor(element, name, module):
                        required_checks["Settings"] = True
                    else:
                        return False
                else:
                    self.save_log_report(f"{name} in module {module.__name__}", f"There are multiple {name} Classes.", "These classes can only exist once")
                    return False
                
        if any(requirement is False for requirement in required_checks.values()):
            missing = ""
            for key, value in  required_checks.items():
                if value == False:
                    if missing != "":
                        missing += f", {key} Class"
                    else:
                        missing += f"{key} Class"
            self.save_log_report(f"module {module.__name__}", "Some classes are missing.", "Please implement " + missing )
            return False
        else:
            return True
        
    def check_for_constructor(self, element, name, module):
        functioning = False
        if "__init__" in element.__dict__:
            try:
                source = inspect.getsource(element.__init__)
                source = textwrap.dedent(source)
                tree = ast.parse(source)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                        if isinstance(node.func.value, ast.Call) and node.func.value.func.id == "super":
                            if node.func.attr == "__init__":
                                functioning = True
                if functioning:
                    return functioning
                else:
                    self.save_log_report(f"{name} in module {module.__name__}", f"The constructor of the parent class is not initialized.", "You have to call super().__init__()")
                    return functioning
                
            except Exception as e:
                self.save_log_report(f"{name} in module {module.__name__}", f"Error while analyzing this code: {e}", "No suggestion.")
                return functioning
        else:
            self.save_log_report(f"{name} in module {module.__name__}", "There is no __init__ method", "This is a requirement, so you have to implement this method")
            return functioning

    def is_valid_python_file(self, path):
        try:
            with open(path, "r", encoding="utf-8") as file:
                ast.parse(file.read())
            return True
        except SyntaxError:
            return False
        
    def load_content(self):
        modules = {}
        extensions_path = os.path.join(self.base_dir, "extensions", '*.py')
        dir_list = glob.glob(extensions_path)
        
        for path in dir_list:
            self.content[os.path.splitext(os.path.basename(path))[0]] = lambda: self.prioritise(path)

        for path in dir_list:
            rel_path = os.path.relpath(path, start=self.base_dir)
            rel_path_m = os.path.splitext(rel_path)[0]
            module_path = rel_path_m.replace(os.path.sep, ".")
            last_change = os.path.getmtime(path)

            for module in self.data["modules"]:
                if path == module["path"] and last_change == module["last_change"]:
                    if module["functioning"] == True:
                        modules[os.path.splitext(os.path.basename(path))[0]] = importlib.import_module(module_path)
                        all_classes = [(name, obj) for name, obj in inspect.getmembers(modules[os.path.splitext(os.path.basename(path))[0]], inspect.isclass)]
                        classes = []
                        for name, element in all_classes:
                            if element.__module__ == modules[os.path.splitext(os.path.basename(path))[0]].__name__ : 
                                classes = self.sort_list(classes, element)
                        self.content[os.path.splitext(os.path.basename(path))[0]] = classes
                        break
                    else:
                        del self.content[os.path.splitext(os.path.basename(path))[0]]
                        break
                elif path == module["path"]:
                    self.data["modules"] = [d for d in self.data["modules"] if d.get("path") != path]
                    continue 
            else:
                if self.is_valid_python_file(path):
                    try:
                        module_name = os.path.splitext(os.path.basename(path))[0]
                        modules[module_name] = importlib.import_module(module_path)
                        functioning = self.check_module(modules[module_name])

                    except Exception as e:
                        self.save_log_report(f"module{os.path.splitext(os.path.basename(path))[0]}", f"This module isn't able to load: {e}",
                                             "no suggestion.")
                        functioning = False
                else:
                    self.save_log_report(f"module {os.path.splitext(os.path.basename(path))[0]}",
                                         f"There is a syntax error in this module","Please check the code.")
                    functioning = False
                cache_module = {
                                "path": path,
                                "last_change": last_change,
                                "functioning": functioning
                                }

                if cache_module["functioning"]:
                    all_classes = [(name, obj) for name, obj in inspect.getmembers(modules[os.path.splitext(os.path.basename(path))[0]], inspect.isclass)]
                    classes = []
                    for name, element in all_classes:
                        if element.__module__ == modules[os.path.splitext(os.path.basename(path))[0]].__name__ : 
                            classes = self.sort_list(classes, element)
                    self.content[os.path.splitext(os.path.basename(path))[0]] = classes
                else:
                    del self.content[os.path.splitext(os.path.basename(path))[0]]
                self.data["modules"].append(cache_module)

                with open(os.path.join(self.cache_path, "cache.json"), 'w') as file:
                    json.dump(self.data, file, indent=4)
        return self.content

if __name__ == "__main__":
    loader = Extensions_Loader(os.path.dirname(__file__))
    print(loader.load_content())
