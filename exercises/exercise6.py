import math
import random

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


def find_majority(raw: [(int, int)]):
    elements = [x for (_, x) in raw]
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

class King(Device):
    def __init__(self, index: int, number_of_devices: int, medium: Medium, application: ConsensusRequester = None):
        super().__init__(index, number_of_devices, medium)
        if application is not None:
            self._application = application
        else:
            self._application = SimpleRequester()

    def run(self):
        pass

    def print_result(self):
        pass


class PrepareMessage(MessageStub):
    def __init__(self, sender: int, destination: int, uid: int):
        super().__init__(sender, destination)
        self.uid = uid

    def __str__(self):
        return f'PREPARE {self.source} -> {self.destination}: {self.uid}'


class PromiseMessage(MessageStub):
    def __init__(self, sender: int, destination: int, uid: int, prev_uid: int, prev_value):
        super().__init__(sender, destination)
        self.uid = uid
        self.prev_uid = prev_uid
        self.prev_value = prev_value

    def __str__(self):
        return f'PROMISE {self.source} -> {self.destination}: {self.uid}' + \
               ('' if self.prev_uid == 0 else f'accepted {self.prev_uid}, {self.prev_value}')


class RequestAcceptMessage(MessageStub):
    def __init__(self, sender: int, destination: int, uid: int, value):
        super().__init__(sender, destination)
        self.uid = uid
        self.value = value

    def __str__(self):
        return f'ACCEPT-REQUEST {self.source} -> {self.destination}: {self.uid}, {self.value}'


class AcceptMessage(MessageStub):
    def __init__(self, sender: int, destination: int, uid: int, value):
        super().__init__(sender, destination)
        self.uid = uid
        self.value = value

    def __str__(self):
        return f'ACCEPT {self.source} -> {self.destination}: {self.uid}, {self.value}'


class PAXOSNetwork:
    def __init__(self, index: int, medium: Medium, acceptors: list[int], learners: list[int]):
        self._acceptors = acceptors
        self._learners = learners
        self._medium = medium
        self._index = index
        self._majority = math.ceil(len(acceptors) / 2.0)

    def prepare(self, uid: int):
        for dest in self._acceptors:
            msg = PrepareMessage(self._index, dest, uid)
            self._medium.send(msg)

    def promise(self, destination: int, uid: int, prev_uid: int, prev_value):
        msg = PromiseMessage(self._index, destination, uid, prev_uid, prev_value)
        self._medium.send(msg)

    def request_accept(self, uid: int, value):
        for dest in self._acceptors:
            msg = RequestAcceptMessage(self._index, dest, uid, value)
            self._medium.send(msg)

    def accept(self, destination: int, uid: int, value):
        msg = AcceptMessage(self._index, destination, uid, value)
        self._medium.send(msg)

        for dest in self._learners:
            msg = AcceptMessage(self._index, dest, uid, value)
            self._medium.send(msg)

    @property
    def majority(self):
        return self._majority

    @property
    def index(self):
        return self._index


class PAXOS(Device):
    def __init__(self, index: int, number_of_devices: int, medium: Medium, application: ConsensusRequester = None):
        super().__init__(index, number_of_devices, medium)
        if application is not None:
            self._application = application
        else:
            self._application = SimpleRequester()
        # assumes everyone has every role
        config = PAXOSNetwork(index, self.medium(), self.medium().ids(), self.medium().ids())
        self._proposer = Proposer(config, self._application)
        self._acceptor = Acceptor(config)
        self._learner = Learner(config, self._application)

    def run(self):
        while True:
            self._proposer.check_prepare()
            if self._proposer.done() and self._acceptor.done() and self._learner.done():
                return
            for ingoing in self.medium().receive_all():
                self.handle_ingoing(ingoing)
            self.medium().wait_for_next_round()

    def handle_ingoing(self, ingoing: MessageStub):
        if isinstance(ingoing, PrepareMessage):
            self._acceptor.handle_prepare(ingoing)
            pass  # to Acceptor
        elif isinstance(ingoing, PromiseMessage):
            self._proposer.handle_promise(ingoing)
            pass  # to Proposer
        elif isinstance(ingoing, RequestAcceptMessage):
            self._acceptor.handle_request_accept(ingoing)
            pass  # to Acceptor
        elif isinstance(ingoing, AcceptMessage):
            self._proposer.handle_accept(ingoing)
            self._learner.handle_accept(ingoing)
            pass  # to Proposer and Learner

    def print_result(self):
        pass


class Proposer:
    def __init__(self, network: PAXOSNetwork, application: ConsensusRequester):
        self._network = network
        self._preference = application.initial_value
        self._promises = []
        self._has_proposed = False
        self._proposed_id = 0
        self._done = False

    def check_prepare(self):
        if self._done:
            return
        # TODO

    def handle_promise(self, msg: PromiseMessage):
        if self._done:
            return

        if msg.uid != self._proposed_id:
            raise Exception("Illegal promise received")
        # TODO

    def handle_accept(self, msg: AcceptMessage):
        self._done = True
        pass

    def done(self):
        return self._done


class Acceptor:
    def __init__(self, network: PAXOSNetwork):
        self._network = network
        self._promised_id = 0
        self._accepted_id = 0
        self._accepted_value = None
        self._done = False

    def handle_prepare(self, msg: PrepareMessage):
        # TODO
        pass

    def handle_request_accept(self, msg: RequestAcceptMessage):
        # TODO
        pass

    def done(self):
        return self._done


class Learner:
    def __init__(self, network: PAXOSNetwork, application: ConsensusRequester):
        self._network = network
        self._done = False
        self._application = application

    def handle_accept(self, msg: AcceptMessage):
        # Learner is aware of consensus
        if self._done:
            return
        self._done = True
        print(f'CONSENSUS {self._network.index} LEARNER on {msg.value}')
        self._application.consensus_reached(msg.value)

    def done(self):
        return self._done
