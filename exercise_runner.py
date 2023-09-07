import argparse
import inspect
from os import name
from threading import Thread
from emulators.exercise_overlay import Window

import exercises.exercise1
import exercises.exercise2
import exercises.exercise4
import exercises.exercise5
import exercises.exercise6
import exercises.exercise7
import exercises.exercise8
import exercises.exercise9
import exercises.exercise10
import exercises.exercise11
import exercises.exercise12
import exercises.demo
from emulators.AsyncEmulator import AsyncEmulator
from emulators.SyncEmulator import SyncEmulator
from emulators.SteppingEmulator import SteppingEmulator

if name == "posix":
    RESET = "\u001B[0m"
    CYAN = "\u001B[36m"
    GREEN = "\u001B[32m"
else:
    RESET = ""
    CYAN = ""
    GREEN = ""

def fetch_alg(lecture: str, algorithm: str):
    if '.' in algorithm or ';' in algorithm:
        raise ValueError(f'"." and ";" are not allowed as names of solutions.')
    try:
        alg = eval(f'exercises.{lecture}.{algorithm}')
        if not inspect.isclass(alg):
            raise TypeError(f'Could not find "exercises.{lecture}.{algorithm} class')
    except:
        raise TypeError(f'Could not find "exercises.{lecture}.{algorithm} class')
    return alg


def run_exercise(lecture_no: int, algorithm: str, network_type: str, number_of_devices: int, gui:bool):
    print(
        f'Running Lecture {lecture_no} Algorithm {algorithm} in a network of type [{network_type}] using {number_of_devices} devices')
    if number_of_devices < 2:
        raise IndexError(f'At least two devices are needed as an input argument, got {number_of_devices}')
    emulator = None
    if network_type == 'async':
        emulator = AsyncEmulator
    elif network_type == 'sync':
        emulator = SyncEmulator
    elif network_type == 'stepping':
        emulator = SteppingEmulator
    instance = None
    if lecture_no == 0:
        alg = fetch_alg('demo', 'PingPong')
        instance = emulator(number_of_devices, alg)
    else:
        alg = fetch_alg(f'exercise{lecture_no}', algorithm)
        instance = emulator(number_of_devices, alg)
    def run_instance():
        if instance is not None:
            instance.run()
            print(f'{CYAN}Execution Complete{RESET}')
            instance.print_result()
            print(f'{CYAN}Statistics{RESET}')
            instance.print_statistics()
        else:
            raise NotImplementedError(
                f'You are trying to run an exercise ({algorithm}) of a lecture ({lecture_no}) which has not yet been released')
    Thread(target=run_instance).start()
    if isinstance(instance, SteppingEmulator) and gui:
        window = Window(number_of_devices, lambda: run_exercise(lecture_no, algorithm, network_type, number_of_devices, True), instance)
        window.show()
        return window
    if not gui and isinstance(instance, SteppingEmulator):
        instance.shell.start()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='For exercises in Distributed Systems.')
    parser.add_argument('--lecture', metavar='N', type=int, nargs=1,
                        help='Lecture number', required=True, choices=[0, 1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12])
    parser.add_argument('--algorithm', metavar='alg', type=str, nargs=1,
                        help='Which algorithm from the exercise to run', required=True)
    parser.add_argument('--type', metavar='nw', type=str, nargs=1,
                        help='whether to use [async] or [sync] network', required=True, choices=['async', 'sync', 'stepping'])
    parser.add_argument('--devices', metavar='N', type=int, nargs=1,
                        help='Number of devices to run', required=True)
    parser.add_argument("--gui", action="store_true", help="Toggle the gui or cli", required=False)
    args = parser.parse_args()
    import sys
    if args.gui and args.type[0] == 'stepping':
        from PyQt6.QtWidgets import QApplication
        app = QApplication(sys.argv)
        run_exercise(args.lecture[0], args.algorithm[0], args.type[0], args.devices[0], True)
        app.exec()
    else:
        run_exercise(args.lecture[0], args.algorithm[0], args.type[0], args.devices[0], False)
        