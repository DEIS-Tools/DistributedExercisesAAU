import argparse

import exercises.exercise1
import exercises.demo
from emulators.AsyncEmulator import AsyncEmulator
from emulators.SyncEmulator import SyncEmulator


def run_exercise(lecture_no: int, algorithm: str, network_type: str, number_of_devices: int):
    if number_of_devices < 2:
        raise IndexError(f'At least two devices are needed as an input argument, got {number_of_devices}')
    emulator = None
    if network_type == 'async':
        emulator = AsyncEmulator
    elif network_type == 'sync':
        emulator = SyncEmulator
    instance = None
    if lecture_no == 0:
        if algorithm == "Demo" or algorithm == "PingPong":
            instance = emulator(number_of_devices, exercises.demo.PingPong)
    elif lecture_no == 1:
        if algorithm == "Gossip":
            instance = emulator(number_of_devices, exercises.exercise1.Gossip)

    if instance is not None:
        print(
            f'Running Lecture {lecture_no} Algorithm {algorithm} in a network of type [{network_type}] using {number_of_devices} devices')
        instance.run()
        print(f'Execution Complete')
        instance.print_result()
        print('Statistics')
        instance.print_statistics()
    else:
        raise NotImplementedError(f'You are trying to run an exercise ({algorithm}) of a lecture ({lecture_no}) which has not yet been released')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='For exercises in Distributed Systems.')
    parser.add_argument('--lecture', metavar='N', type=int, nargs=1,
                        help='Lecture number', required=True, choices=[0,1])
    parser.add_argument('--algorithm', metavar='alg', type=str, nargs=1,
                        help='Which algorithm from the exercise to run', required=True)
    parser.add_argument('--type', metavar='nw', type=str, nargs=1,
                        help='whether to use [async] or [sync] network', required=True, choices=['async', 'sync'])
    parser.add_argument('--devices', metavar='N', type=int, nargs=1,
                        help='Number of devices to run', required=True)
    args = parser.parse_args()

    run_exercise(args.lecture[0], args.algorithm[0], args.type[0], args.devices[0])
