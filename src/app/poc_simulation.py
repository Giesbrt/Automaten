import os
import pathlib
import threading
import time
from time import perf_counter

from dotenv import load_dotenv

from core.backend.backend import start_backend, BackendType
from core.backend.data.simulation import Simulation
from core.backend.data.transition import Transition
from core.backend.default.defaultTape import DefaultTape
from core.backend.loader.automatonProvider import AutomatonProvider
from core.backend.loader.loader import Loader
from core.backend.packets.packetManager import PacketManager as _PacketManager
from core.backend.packets.simulationPackets import SimulationStartPacket
from core.utils.staticSignal import SignalCache

import keyboard

# Standard typing imports for aps
import abc as _abc
import typing as _ty
import types as _ts

backend: BackendType = None
backend_thread: threading.Thread = None
backend_stop_event: threading.Event = threading.Event()


def main():
    loader = Loader(pathlib.Path(os.getenv("BASE_PATH")))
    auto: AutomatonProvider = AutomatonProvider()
    auto.register_automatons(loader.load()[0])

    global backend
    global backend_thread
    global backend_stop_event

    backend = start_backend()  # Backend thread
    backend_thread = threading.Thread(target=backend.run_infinite, args=(backend_stop_event,))
    backend_thread.start()


def run_signal(stop_event: threading.Event):
    while not stop_event.is_set():
        if SignalCache().has_elements() is None:
            continue

        SignalCache().invoke()


simulation_mode: _ty.Literal["step", "all"] = ""
is_paused: bool = False
fps: int = 30


def packet_notifier(simulation: Simulation, step_size: int = 1):
    global simulation_mode
    global is_paused
    global fps

    while True:
        simulation_mode = str(input(" | Simulation-Mode (step, all) >> ")).lower()
        if simulation_mode in ["step", "all"]:
            if simulation_mode == "all":
                print(" | Press 'esc' or 'q' to pause simulation")
                fps = int(input(" | FPS >> ") or 30)
            break
    while True:
        try:
            # time.sleep(0.01)
            if keyboard.is_pressed("esc") or keyboard.is_pressed("q"):
                raise KeyboardInterrupt

            if is_paused:
                while True:
                    sim_mode = str(input(" | Simulation paused (step, all, end, resume) >> "))
                    if sim_mode not in ["step", "all", "end", "resume"]:
                        continue

                    match sim_mode:
                        case "step" | "all":
                            simulation_mode = sim_mode
                            if simulation_mode == "all":
                                fps = int(input(" | FPS >> ") or 30)
                            is_paused = False
                            break

                        case "end":
                            simulation.finish_simulation(True, "Exited Simulation")
                            print(f"Simulation finished: {simulation.simulation_end_cause.get_value()}")
                            raise SystemExit

                        case "resume":
                            is_paused = False
                            break

                        case _:
                            raise ValueError("Unknown Simulation Mode")

            match simulation_mode:
                case "step":
                    _handle_step_simulation(simulation, step_size)
                    continue

                case "all":
                    _handle_all_simulation(simulation, step_size)
                    continue

                case _:
                    raise ValueError("Unknown Simulation Mode")

        except KeyboardInterrupt as e:
            if not is_paused:
                is_paused = True
                print(" | Paused Simulation...", e)
        except SystemExit:
            if backend_stop_event is not None:
                backend_stop_event.set()
            exit(0)


def _handle_step_simulation(simulation: Simulation, step_size: int):
    global is_paused

    res = step_simulation(simulation)
    if not res and res is not None:
        print(f"Simulation finished: {simulation.simulation_end_cause.get_value()}")
        raise SystemExit
    else:
        while True:
            step_direction_input: str = str(input(" | Step (next[*steps], previous[*steps], pause) >> "))
            step_direction: _ty.Literal["next", "previous"] | None = None
            steps_in_direction: int = step_size

            if step_direction_input.lower() == "pause":
                is_paused = True
                return


            if step_direction_input.startswith("next"):
                step_direction = "next"

            if step_direction_input.startswith("previous"):
                step_direction = "previous"

            if not step_direction:
                continue

            if "*" in step_direction_input:
                steps = step_direction_input.split("*")
                steps_in_direction = int(steps[1])

            print(f"Displaying {step_direction} {steps_in_direction} Steps")
            directed_steps: int = 0
            match step_direction:
                case "next":
                    directed_steps = steps_in_direction

                case "previous":
                    directed_steps = -steps_in_direction

            simulation.step_index += directed_steps
            if simulation.step_index < 0:
                simulation.step_index = 0

            if simulation.step_index >= len(simulation.simulation_steps) and simulation.finished.get_value():
                simulation.step_index = len(simulation.simulation_steps) - 1
            break

        # Waiting for bulk (happens when skipping a large number of steps)
        while simulation.step_index >= len(simulation.simulation_steps):
            time.sleep(0.1)
            continue


next_signal: float = None
def _handle_all_simulation(simulation: Simulation, step_size: int):
    global fps
    global next_signal

    if not next_signal:
        next_signal = perf_counter()


    if not (perf_counter() >= next_signal):
        return

    next_signal += (1.0 / fps)

    match step_simulation(simulation):
        case True:
            simulation.step_index = simulation.step_index + step_size
        case False:
            print(f"Simulation finished: {simulation.simulation_end_cause.get_value()}")
            raise SystemExit
        case None:
            pass


def step_simulation(simulation: Simulation,
                    MAX_SIMULATION_REPLAY_STEPS: int = 1000) -> bool | None:
    """Returns None when waiting for new results"""

    if (simulation.step_index >= MAX_SIMULATION_REPLAY_STEPS or
            (simulation.step_index >= len(simulation.simulation_steps) and simulation.finished.get_value())):
        simulation.finished.set_value(True)
        print(f"Simulation finished: {simulation.simulation_end_cause.get_value()}")
        return False

    if simulation.step_index >= len(simulation.simulation_steps):
        print(f"Waiting for new simulation steps {simulation.step_index}, {len(simulation.simulation_steps)}")
        return None

    i = simulation.step_index

    step = simulation.simulation_steps[i]
    output = step["complete_output"]
    state_id = step["active_states"]

    print(f"{i + 1} {len(simulation.simulation_steps)} {[output.get_tape()[k] for k in output.get_tape().keys()]} "
          f"State: {state_id[0] + 1}")
    print(
        f"{" " * len(str(i + 1))} {len(simulation.simulation_steps)}   {' ' * 5 * output.get_pointer()}^")
    return True


if __name__ == '__main__':
    load_dotenv(r".env")
    try:
        main()

        # -------------- DFA Automaton -> No loop
        sim_packet = SimulationStartPacket([(0, "default"), (1, "end")],
                                           0,
                                           [
                                               Transition(0, 0, 0, ["a"]),
                                               Transition(1, 0, 1, ["b"]),
                                               Transition(2, 1, 0, ["a"]),
                                               Transition(3, 1, 1, ["b"])
                                           ],
                                           DefaultTape(
                                               ["b", "a", "b", "b"]),
                                           "dfa",
                                           packet_notifier,
                                           1)

        # -------------- TM Automaton -> infinite Loop
        # sim_packet = SimulationStartPacket([(0, "default"), (1, "end")],
        #                                    0,
        #                                    [
        #                                        Transition(0, 1, 0, ["b", "a", "h"]),
        #                                        Transition(1, 0, 1, ["a", "b", "h"])
        #                                    ],
        #                                    DefaultTape(
        #                                        ["a"]),
        #                                    "tm",
        #                                    packet_notifier,
        #                                    100)

        _PacketManager().send_backend_packet(sim_packet)
        print(f"packet send {_PacketManager().has_backend_packets()}")

        print("REPLAY START")
        thread2 = threading.Thread(target=run_signal, args=(backend_stop_event,))
        thread2.start()

    except KeyboardInterrupt:
        if backend_stop_event is not None:
            backend_stop_event.set()
