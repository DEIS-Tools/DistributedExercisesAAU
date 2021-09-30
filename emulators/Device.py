import threading
import random

from emulators.Medium import Medium


class Device:
    def __init__(self, index: int, number_of_devices: int, medium: Medium):
        self._id = index
        self._medium = medium
        self._number_of_devices = number_of_devices

    def run(self):
        raise NotImplementedError("You have to implement a run-method!")

    def print_result(self):
        raise NotImplementedError("You have to implement a result printer!")

    def index(self):
        return self._id

    def number_of_devices(self):
        return self._number_of_devices

    def medium(self):
        return self._medium


class WorkerDevice(Device):
    _concurrent_workers = 0
    _lock = threading.Lock()

    def __init__(self, index: int, number_of_devices: int, medium: Medium):
        super().__init__(index, number_of_devices, medium)
        self._has_work = False

    def has_work(self) -> bool:
        # The random call emulates that a concurrent process asked for the
        self._has_work = self._has_work or random.randint(0, self.number_of_devices()) == self.index()
        return self._has_work

    def do_work(self):
        # Emulates waiting for some time to do work
        # In practice we would notify another thread that we have acquired the mutex, as later protocols
        # might require continued interaction. The "working" thread would then notify our Requester class back
        # when the mutex is done being used.
        self._lock.acquire()
        print(f'Device {self.index()} has started working')
        self._concurrent_workers += 1
        if self._concurrent_workers > 1:
            self._lock.release()
            raise Exception("More than one concurrent worker!")
        self._lock.release()

        assert (self.has_work())
        amount_of_work = random.randint(1, 4)
        for i in range(0, amount_of_work):
            self.medium().wait_for_next_round()
        self._lock.acquire()
        print(f'Device {self.index()} has ended working')
        self._concurrent_workers -= 1
        self._lock.release()
        self._has_work = False
