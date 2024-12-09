from transitionFunction import TransitionFunction
from state import State
from utils import Result


class Automaton:
    def __init__(self) -> None:
        self.states: set[State] = set()
        self.transitionFunctions: dict[State, TransitionFunction] = {}
        self.currentState: State = None
        self.startState: State = None
        self.endStates: set[State] = set()

        self.word: str = ""
        self.wordIndex: int = 0
        self.currentChar: str = ""

    def setWord(self, word: str) -> None:
        self.word = word
        self.currentChar = self.word[0]

    def nextChar(self) -> None:
        self.wordIndex += 1
        self.currentChar: str = self.word[
            max(0, min(self.wordIndex, len(self.word) - 1))]  # Clamp the index between 0 and word length -1

    def nextState(self) -> Result:
        possibleState: Result = self.currentState.transitionToPossibleStates(self.currentChar)

        if not possibleState.success:
            return Result(False, possibleState.message)

        transitionedState: State = possibleState.returnValue
        if transitionedState not in self.states:
            return Result(False, "State is not in the automatons states!")

        self.currentState = transitionedState

        return Result(True)

    def addState(self, state: State) -> None:
        self.__ifNotStateAdd(state)

    def setStartState(self, startState: State) -> None:
        self.__ifNotStateAdd(startState)
        self.startState = startState

    def addEndstate(self, endState: State) -> None:
        self.__ifNotStateAdd(endState)
        self.endStates.add(endState)

    def addTransitionalFunction(self, startState: State, transitionFunction: TransitionFunction) -> None:
        if startState not in self.states:
            return

        self.transitionFunctions[startState] = transitionFunction

    def removeState(self, state: State) -> None:
        self.states.remove(state)
        self.endStates.remove(state)
        del self.transitionFunctions[state]

        if self.startState == state:
            self.startState = None

        if self.currentState == state:
            self.currentState = None

    def __ifNotStateAdd(self, state: State) -> bool:
        if state in self.states:
            return True
        self.states.add(state)

    def simulate(self) -> Result:
        if not self.startState:
            return Result(False, "Start State is None!")
        self.currentState = self.startState

        while True:
            print(self.startState)
            print(self.word)
            print(self.currentChar)
            print(self.wordIndex)

            print(self.currentState.getName(), self.currentChar)
            self.nextState()
            self.nextChar()

            if self.wordIndex >= len(self.word):
                break

        if self.currentState in self.endStates:
            return Result(True, "Automaton terminated in an endstate!")
        else:
            return Result(False, "Automaton did not terminate in an endstate!")


if __name__ == '__main__':
    automaton = Automaton()

    s1 = State("q0")
    s2 = State("q1")

    s1f1 = TransitionFunction(s1, 'a')
    s1f2 = TransitionFunction(s2, 'b')

    s2f1 = TransitionFunction(s2, 'b')
    s2f2 = TransitionFunction(s1, 'a')

    s1.addTransitionFunction(s1f1)
    s1.addTransitionFunction(s1f2)

    s2.addTransitionFunction(s2f1)
    s2.addTransitionFunction(s2f2)

    automaton.setStartState(s1)
    automaton.addEndstate(s2)

    automaton.setWord("aaaaabaaab")
    print(automaton.simulate().message)
