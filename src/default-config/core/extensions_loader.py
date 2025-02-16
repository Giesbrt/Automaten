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
import ast
sys.path.append(os.path.join(os.path.dirname(__file__), 'extensions'))

class Extensions_Loader:
    def __init__(self):
        self.cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ext_cache")
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

    def check_module(self, module):
        if self.static_analysis(module) and self.dynamic_analysis(module):
            return True
        else:
            return False
    
    def static_analysis(self, module):
        classes_in_module = []
        classes = [(name, obj) for name, obj in inspect.getmembers(module, inspect.isclass)]
        for name, element in classes:
            if element.__module__ == module.__name__ : 
                classes_in_module.append((name, element))
        check = ["s","a","t"]

        for name, element in classes_in_module:
            if name.endswith("State"):
                if issubclass(element, BaseState):
                    if "s" in  check:
                        implemented_methods = {name for name, _ in inspect.getmembers(BaseState, inspect.isroutine)}
                        abstract_methods = BaseState.__abstractmethods__
                        for method in abstract_methods:
                            if method not in implemented_methods:
                                return False
                            else:
                                break
                        check.remove("s")
                    else:
                        return False
            elif name.endswith("Automaton"):
                if issubclass(element, BaseAutomaton):
                    if "a" in  check:
                        implemented_methods = {name for name, _ in inspect.getmembers(BaseAutomaton, inspect.isroutine)}
                        abstract_methods = BaseAutomaton.__abstractmethods__
                        for method in abstract_methods:
                            if method not in implemented_methods:
                                return False
                            else:
                                break
                        check.remove("a")
                    else:
                        return False
            elif name.endswith("Transition"):
                if issubclass(element, BaseTransition):
                    if "t" in  check:
                        implemented_methods = {name for name, _ in inspect.getmembers(BaseTransition, inspect.isfunction)}
                        abstract_methods = BaseTransition.__abstractmethods__
                        for method in abstract_methods:
                            if method not in implemented_methods:
                                return False
                            else:
                                break
                        check.remove("t")
                else:
                    return False
            else:
                return False
        if check == []:
            return True
        else:
            return False

    def dynamic_analysis(self, module):
        return True
    
    def prioritize(self, path):
        return #self.load_content(onestep = True)

    def is_valid_python_file(self, path):
        try:
            with open(path, "r", encoding="utf-8") as file:
                ast.parse(file.read())
            return True
        except SyntaxError:
            return False
        
    def load_content(self, base_dir: str, onestep = False):
        modules = {}
        extensions_path = os.path.join(base_dir, "extensions", '*.py')
        print("EP",extensions_path)
        dir_list = glob.glob(extensions_path)
        
        for path in dir_list:
            self.content[os.path.splitext(os.path.basename(path))[0]] = lambda: self.prioritise(path)

        for path in dir_list:
            rel_path = os.path.relpath(path, start=base_dir)
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
                                classes.append(element)
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
                    modules[os.path.splitext(os.path.basename(path))[0]] = importlib.import_module(module_path)
                    functioning = self.check_module(modules[os.path.splitext(os.path.basename(path))[0]])
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
                            classes.append(element)
                    self.content[os.path.splitext(os.path.basename(path))[0]] = classes
                else:
                    del self.content[os.path.splitext(os.path.basename(path))[0]]
                self.data["modules"].append(cache_module)

                with open(os.path.join(self.cache_path, "cache.json"), 'w') as file:
                    json.dump(self.data, file, indent=4)
        return self.content

if __name__ == "__main__":
    loader = Extensions_Loader()
    print(loader.load_content())