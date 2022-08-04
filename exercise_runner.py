import argparse
import inspect

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


def run_exercise(lecture_no: int, algorithm: str, network_type: str, number_of_devices: int, test_file:str, is_test=False):
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
    else:
        alg = fetch_alg(f'exercise{lecture_no}', algorithm)
    instance = emulator(number_of_devices, alg, is_test, test_file, lecture_no)

    if instance is not None:
        instance.run()
        print(f'Execution Complete')
        instance.print_result()
        print('Statistics')
        instance.print_statistics()
    else:
        raise NotImplementedError(
            f'You are trying to run an exercise ({algorithm}) of a lecture ({lecture_no}) which has not yet been released')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='For exercises in Distributed Systems.')
    parser.add_argument('--lecture', metavar='N', type=int, nargs=1,
                        help='Lecture number', required=False, choices=[0, 1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12])
    parser.add_argument('--algorithm', metavar='alg', type=str, nargs=1,
                        help='Which algorithm from the exercise to run', required=False)
    parser.add_argument('--type', metavar='nw', type=str, nargs=1,
                        help='whether to use [async] or [sync] network', required=False, choices=['async', 'sync', 'stepping'])
    parser.add_argument('--devices', metavar='N', type=int, nargs=1,
                        help='Number of devices to run', required=False)
    parser.add_argument('--test', help='run using unit test framework', required=False, action='store_true')
    parser.add_argument('--test_file', help='optional: name of custom test csv', required=False, nargs=1, type=str)
    args = parser.parse_args()

    myArgs = {'lecture':0,'algorithm':'PingPong','type':'async','devices':3,'test':False, 'test_file':'demo.csv'}
    for arg in args._get_kwargs():
        if not arg[1] == None: 
            try:
                myArgs[arg[0]] = arg[1][0] 
            except:
                myArgs[arg[0]] = arg[1]
    
    if myArgs['test_file'] == 'demo.csv':
        myArgs['test_file'] = 'demo.csv' if myArgs['lecture'] == 0 else f'exercise{myArgs["lecture"]}.csv'

    if myArgs['lecture'] == 0 or myArgs['algorithm'] == 'PingPong':
        myArgs['lecture'] = 0
        myArgs['algorithm'] = 'PingPong'
    run_exercise(myArgs['lecture'], myArgs['algorithm'], myArgs['type'], myArgs['devices'], myArgs['test_file'], myArgs['test'])