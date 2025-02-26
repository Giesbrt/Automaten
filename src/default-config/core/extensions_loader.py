import os
import glob
import importlib
import sys
import json
import inspect
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.modules.automaton.base.state import State as BaseState
from core.modules.automaton.base.transition import Transition as BaseTransition
from core.modules.automaton.base.automaton import Automaton as BaseAutomaton
from core.modules.automaton.base.settings import Settings as BaseSettings
import ast

sys.path.append(os.path.join(os.path.dirname(__file__), 'extensions'))

class Extensions_Loader:
    def __init__(self, base_dir: str):
        self.base_dir: str = base_dir
        self.cache_path = os.path.join(base_dir, "ext_cache")
        if not os.path.exists(self.cache_path):
            os.mkdir(self.cache_path)
            with open(os.path.join(self.cache_path, "cache.json"), 'w') as file:
                json.dump({"modules": []}, file, indent=4)
        with open(os.path.join(self.cache_path, "cache.json"), 'r') as file:
            self.data = json.load(file)
        if "modules" not in self.data:
            self.data["modules"] = []
        self.content: dict = {}

    def get_content(self):
        return self.content

    def clear_cache(self): 
        with open(os.path.join(self.cache_path, "cache.json"), 'w') as file:
                json.dump({"modules": []}, file, indent=4)
        
    def sort_list(self, classes, element, position = None):
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

        classes_in_module = []
        classes = [(name, obj) for name, obj in inspect.getmembers(module, inspect.isclass)]
        for name, element in classes:
            if element.__module__ == module.__name__ : 
                classes_in_module.append((name, element))
        required_checks = {
                            "State": False,
                            "Automaton": False,
                            "Transition": False,
                            "Settings": False
                          }

        for name, element in classes_in_module:
            if issubclass(element, BaseState):
                if required_checks["State"] == False:
                    implemented_methods = {name for name, _ in inspect.getmembers(BaseState, inspect.isroutine)}
                    abstract_methods = BaseState.__abstractmethods__
                    for method in abstract_methods:
                        if method not in implemented_methods:
                            return False
                    required_checks["State"] = True
                else:
                    return False
            elif issubclass(element, BaseAutomaton):
                if required_checks["Automaton"] == False:
                    implemented_methods = {name for name, _ in inspect.getmembers(BaseAutomaton, inspect.isroutine)}
                    abstract_methods = BaseAutomaton.__abstractmethods__
                    for method in abstract_methods:
                        if method not in implemented_methods:
                            return False
                    required_checks["Automaton"] = True
                else:
                    return False
            elif issubclass(element, BaseTransition):
                if required_checks["Transition"] == False:
                    implemented_methods = {name for name, _ in inspect.getmembers(BaseTransition, inspect.isfunction)}
                    abstract_methods = BaseTransition.__abstractmethods__
                    for method in abstract_methods:
                        if method not in implemented_methods:
                            return False
                    required_checks["Transition"] = True
                else:
                    return False
            elif issubclass(element, BaseSettings):
                if required_checks["Settings"] == False:
                    implemented_methods = {name for name, _ in inspect.getmembers(BaseSettings, inspect.isfunction)}
                    if "__init__" in implemented_methods:
                        source = inspect.getsource(element.__init__)
                        if "super().__init__" in source:
                            required_checks["Settings"] = True
                        else:
                            return False
                    else:
                        return False
                else:
                    return False
        if any(requirement is False for requirement in required_checks.values()):
            return False
        else:
            return True

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
                        modules[os.path.splitext(os.path.basename(path))[0]] = importlib.import_module(module_path)
                        functioning = self.check_module(modules[os.path.splitext(os.path.basename(path))[0]])
                    except:
                        functioning = False
                else:
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
