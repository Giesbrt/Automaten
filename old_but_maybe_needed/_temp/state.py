from utils import Result
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from transitionFunction import TransitionFunction # nessecary to bypass circular import

class State:
    def __init__(self, name: str) -> None:
        self.transitionFunctions: set["TransitionFunction"] = set()
        self.name: str = name

    def addTransitionFunction(self, transitionFunction: "TransitionFunction") -> None:
        self.transitionFunctions.add(transitionFunction)

    def getName(self) -> str:
        return self.name

    def getTransitionFunctions(self) -> set["TransitionFunction"]:
        return self.transitionFunctions

    def transitionToPossibleStates(self, currentWordChar: str) -> Result:
        allfunctionConditions: list[str] = [i.canTransition(currentWordChar) for i in self.getTransitionFunctions()]
        if allfunctionConditions.count(True) > 1:
            return Result(False, message=f"There are multiple functions for a single char {currentWordChar if currentWordChar != '' else 'N/A'}!")

        for function in self.getTransitionFunctions():
            if not function.canTransition(currentWordChar):
                continue
            return Result(True, returnValue=function.getTargetState())
        
        return Result(False, "No transition function found!")
