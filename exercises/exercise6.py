import random
import threading
import time

import copy

from emulators.Device import Device
from emulators.Medium import Medium
from emulators.MessageStub import MessageStub


class ConsensusRequester:
    def consensus_reached(self, element: int):
        raise NotImplementedError

    def initial_value(self):
        raise NotImplementedError

class PAXOS(Device):

    def __init__(self, index: int, number_of_devices: int, medium: Medium, application: ConsensusRequester = None):
        super().__init__(index, number_of_devices, medium)
        """if application is not None:
            self._application = application
        else:
            self._application = ConsensusApp(index, self)"""