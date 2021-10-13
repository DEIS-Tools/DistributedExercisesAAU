import math
import random
import threading
import time

import copy

from emulators.Device import Device
from emulators.Medium import Medium
from emulators.MessageStub import MessageStub


class ConsensusRequester:
    def consensus_reached(self, element):
        raise NotImplementedError

    def initial_value(self):
        raise NotImplementedError


class SimpleRequester(ConsensusRequester):

    def __init__(self):
        self._proposal = random.randint(0, 100)

    @property
    def initial_value(self) -> int:
        return self._proposal

    _some = False
    _consensus = None  # for validating result

    def consensus_reached(self, element):
        if not SimpleRequester._some:
            SimpleRequester._some = True
            SimpleRequester._consensus = element
        if SimpleRequester._consensus != element:
            raise ValueError(
                f"Disagreement in consensus, expected {element} but other process already got {SimpleRequester._consensus}")


class Propose(MessageStub):
    def __init__(self, value, sender: int = 0, destination: int = 0):
        super().__init__(0, 0)
        self._value = value

    def value(self):
        return self._value

    def __str__(self):
        return f'Propose: {self.source} -> {self.destination}: {self._value}'


class FResilientConsensus(Device):
    def __init__(self, index: int, number_of_devices: int, medium: Medium, application: ConsensusRequester = None):
        super().__init__(index, number_of_devices, medium)
        if application is not None:
            self._application = application
        else:
            self._application = SimpleRequester()

        self._v = set()
        self._f = number_of_devices - 1

    def run(self):
        self.b_multicast(Propose({self._application.initial_value}))
        self.medium().wait_for_next_round()
        for i in range(0, self._f):  # f + 1 rounds
            v_p = self._v.copy()
            for p in self.medium().receive_all():
                self._v.update(p.value())
            if i != self._f - 1:
                self.b_multicast(Propose(v_p.difference(v_p)))

        self._application.consensus_reached(min(self._v))

    def b_multicast(self, message: MessageStub):
        message.source = self.index()
        for i in self.medium().ids():
            message.destination = i
            self.medium().send(message)

    def print_result(self):
        print(f"Device {self.index()} agrees on {min(self._v)}")


class SingleByzantine(Device):

    def __init__(self, index: int, number_of_devices: int, medium: Medium, application: ConsensusRequester = None):
        super().__init__(index, number_of_devices, medium)
        if application is not None:
            self._application = application
        else:
            self._application = SimpleRequester()
        self._consensus = None

    def run(self):
        if self.index() == 0:
            self.run_commander()
        else:
            self.run_lieutenant()

    def run_commander(self):
        self.b_multicast(Propose(self._application.initial_value))
        """Done!"""

    def run_lieutenant(self):
        self.medium().wait_for_next_round()
        from_commander = self.medium().receive_all()
        assert len(from_commander) <= 1
        v = None
        if from_commander is not None and len(from_commander) > 0:
            v = from_commander[0].value()
        self.b_multicast(Propose((self.index(), v)))
        self.medium().wait_for_next_round()
        from_others = [m.value() for m in self.medium().receive_all()]
        self._consensus = find_majority(from_others)
        self._application.consensus_reached(self._consensus)

    def b_multicast(self, message: MessageStub):
        message.source = self.index()
        for i in self.medium().ids():
            message.destination = i
            self.medium().send(message)

    def print_result(self):
        if self.index() != 0:
            print(f"Device {self.index()} is done, consensus: {self._consensus}")
        else:
            print("Commander is done")


def find_majority(raw: [(int,int)]):
    elements = [x for (_,x) in raw]
    cands = set(elements)
    best = None
    best_count = 0
    for i in cands:
        n = sum(int(x == i) for x in elements)
        if n > best_count:
            best = i
            best_count = n
        elif best_count == n:
            best = None
    return best


class PAXOS(Device):

    def __init__(self, index: int, number_of_devices: int, medium: Medium, application: ConsensusRequester = None):
        super().__init__(index, number_of_devices, medium)
        """if application is not None:
            self._application = application
        else:
            self._application = ConsensusApp(index, self)"""
