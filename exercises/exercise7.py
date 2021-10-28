import math
import random
import threading
import time

from emulators.Medium import Medium
from emulators.Device import Device
from emulators.MessageStub import MessageStub


class Vote(MessageStub):

    def __init__(self, sender: int, destination: int, vote: int, decided: bool):
        super().__init__(sender, destination)
        self._vote = vote
        self._decided = decided

    def vote(self):
        return self._vote

    def decided(self):
        return self._decided

    def __str__(self):
        return f'Vote: {self.source} -> {self.destination}, voted for {self._vote}, decided? {self._decided}'


class Bully(Device):

    def __init__(self, index: int, number_of_devices: int, medium: Medium):
        super().__init__(index, number_of_devices, medium)
        self._leader = None
        self._shut_up = False
        self._election = False

    def largest(self):
        return self.index() == max(self.medium().ids())

    def run(self):
        """TODO"""

    def start_election(self):
        """TODO"""

    def print_result(self):
        print(f'Leader seen from {self._id} is {self._leader}')