import random
import threading

from emulators.Medium import Medium
from emulators.UnitTestMedium import UnitTestMedium, load_execution_sequence
from emulators.MessageStub import MessageStub


class EmulatorStub:

    def __init__(self, number_of_devices: int, kind, is_test, test_file):
        self._nids = number_of_devices
        self._devices = []
        self._threads = []
        self._media = []
        self.sending_execution_sequence = []
        self.receiving_execution_sequence = []
        self.is_test = is_test
        self._progress = threading.Lock()


        for index in self.ids():
            if is_test:
                #execute if running a unit test
                self.sending_execution_sequence = load_execution_sequence(f'emulators/tests/sending/{test_file}')
                self.receiving_execution_sequence = load_execution_sequence(f'emulators/tests/receiving/{test_file}')
                self._media.append(UnitTestMedium(index, self))
            else:
                self._media.append(Medium(index, self))
            self._devices.append(kind(index, number_of_devices, self._media[-1]))
            self._threads.append(threading.Thread(target=self._run_thread, args=[index]))

    def _run_thread(self, index: int):
        self._devices[index].run()
        try:
            self.terminated(index)
        except Exception:
            self.terminated(index)
            raise

    def _start_threads(self):
        cpy = self._threads.copy()
        random.shuffle(cpy)
        print('Starting Threads')
        for thread in cpy:
            thread.start()

    def all_terminated(self) -> bool:
        return all([not self._threads[x].is_alive()
                    for x in self.ids()])

    def ids(self):
        return range(0, self._nids)

    def print_result(self):
        for d in self._devices:
            d.print_result()
        if self.is_test:
            print('Running test on the entire result')
            from importlib import import_module
            if self.lecture == 0:
                module = import_module('emulators.tests.modules.demo')
            else:
                module = import_module(f'emulators.tests.modules.exercise{self.lecture}')
            module.test().run(self._devices)

    def run(self):
        raise NotImplementedError(f'Please contact the instructor')

    def queue(self, message: MessageStub):
        raise NotImplementedError(f'Please contact the instructor')

    def dequeue(self, id) -> MessageStub:
        raise NotImplementedError(f'Please contact the instructor')

    def done(self, id):
        raise NotImplementedError(f'Please contact the instructor')

    def print_statistics(self):
        raise NotImplementedError(f'Please contact the instructor')

    def terminated(self, index: int):
        raise NotImplementedError(f'Please contact the instructor')
