from state import State

class TransitionFunction:
    def __init__(self, targetState: State, condition: str) -> None:
        self.condition: str = condition
        self.targetState: State = targetState

    def canTransition(self, charInWord: str) -> bool:
        return charInWord == self.condition
    
    def getTargetState(self) -> State:
        return self.targetState
    
    def getCondition(self) -> str:
        return self.condition