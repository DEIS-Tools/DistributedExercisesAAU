import threading
import random

from emulators.Medium import Medium


class Device:
    """
    Base class representing a device in a simulation.

    Args:
        index (int): The unique identifier for the device.
        number_of_devices (int): The total number of devices in the simulation.
        medium (Medium): The communication medium used by the devices.

    Attributes:
        _id (int): The unique identifier for the device.
        _medium (Medium): The communication medium used by the device.
        _number_of_devices (int): The total number of devices in the simulation.
        _finished (bool): A flag indicating if the device has finished its task.
    """

    def __init__(self, index: int, number_of_devices: int, medium: Medium):
        self._id = index
        self._medium = medium
        self._number_of_devices = number_of_devices
        self._finished = False

    def run(self):
        """
        Abstract method representing the main functionality of the device.
        """

        raise NotImplementedError("You have to implement a run-method!")

    def print_result(self):
        """
        Abstract method for the result printer
        """
        raise NotImplementedError("You have to implement a result printer!")

    def index(self):
        """
        The unique identifier for the device.

        Returns:
            int: The unique identifier of the device.
        """
        return self._id

    def number_of_devices(self):
        """
        Get the total number of devices in the simulation.

        Returns:
            int: The total number of devices.
        """
        return self._number_of_devices

    def medium(self):
        """
        Get the communication medium used by the device.

        Returns:
            Medium: The communication medium.
        """
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
