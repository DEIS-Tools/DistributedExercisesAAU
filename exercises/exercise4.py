import math
import random
import threading
import time

from emulators.Medium import Medium
from emulators.Device import Device, WorkerDevice
from emulators.MessageStub import MessageStub
import enum


class Ping(MessageStub):
    def __init__(self, sender: int, destination: int):
        super().__init__(sender, destination)

    def __str__(self):
        return f'Ping: {self.source} -> {self.destination}'


class Pinger(Device):

    def __init__(self, index: int, number_of_devices: int, medium: Medium):
        super().__init__(index, number_of_devices, medium)
        self._output_ping = False

    def run(self):
        while True:
            ingoing = self.medium().receive()
            if isinstance(ingoing, Ping):
                if self._output_ping:
                    print("Ping")
                    self._output_ping = False
                else:
                    print("Pong")
                    self._output_ping = True
            self.medium().wait_for_next_round()

    def print_result(self):
        print("Done!")


class Type(enum.Enum):
    REQUEST = 0
    RELEASE = 1
    GRANT = 2


class MutexMessage(MessageStub):

    def __init__(self, sender: int, destination: int, message_type: Type):
        super().__init__(sender, destination)
        self._type = message_type

    def is_request(self):
        return self._type == Type.REQUEST

    def is_grant(self):
        return self._type == Type.GRANT

    def is_release(self):
        return self._type == Type.RELEASE

    def __str__(self):
        if self._type == Type.REQUEST:
            return f'Request: {self.source} -> {self.destination}'
        if self._type == Type.RELEASE:
            return f'Release: {self.source} -> {self.destination}'
        if self._type == Type.GRANT:
            return f'Grant: {self.source} -> {self.destination}'


class Centralised:
    def __new__(cls, index: int, number_of_devices: int, medium: Medium):
        if index == 0:
            return Coordinator(index, number_of_devices, medium)
        else:
            return Requester(index, number_of_devices, medium)


class Coordinator(Device):

    def __init__(self, index: int, number_of_devices: int, medium: Medium):
        super().__init__(index, number_of_devices, medium)
        assert (self.index() == 0)  # we assume that the coordinator is fixed at index 0.
        self._granted = None
        self._waiting = []

    def run(self):
        while True:
            while True:
                ingoing = self.medium().receive()
                if ingoing is None:
                    break
                if ingoing.is_request():
                    self._waiting.append(ingoing.source)
                elif ingoing.is_release():
                    assert (self._granted == ingoing.source)
                    self._granted = None

                if len(self._waiting) > 0 and self._granted is None:
                    self._granted = self._waiting.pop(0)
                    self.medium().send(MutexMessage(self.index(), self._granted, Type.GRANT))
            self.medium().wait_for_next_round()

    def print_result(self):
        print("Coordinator Terminated")


class Requester(WorkerDevice):

    def __init__(self, index: int, number_of_devices: int, medium: Medium):
        super().__init__(index, number_of_devices, medium)
        assert (self.index() != 0)  # we assume that the coordinator is fixed at index 0.
        self._requested = False

    def run(self):
        while True:
            ingoing = self.medium().receive()
            if ingoing is not None:
                if ingoing.is_grant():
                    assert (self._requested)
                    self.do_work()
                    self._requested = False
                    self.medium().send(
                        MutexMessage(self.index(), 0, Type.RELEASE))

            if self.has_work() and not self._requested:
                self._requested = True
                self.medium().send(
                    MutexMessage(self.index(), 0, Type.REQUEST))

            self.medium().wait_for_next_round()

    def print_result(self):
        print(f"Requester {self.index()} Terminated with request? {self._requested}")


class TokenRing(WorkerDevice):
    def __init__(self, index: int, number_of_devices: int, medium: Medium):
        super().__init__(index, number_of_devices, medium)
        self._has_token = False
        if index == 0:
            self._has_token = True

    def run(self):
        while True:
            while True:
                ingoing = self.medium().receive()
                if ingoing is None:
                    break
                if ingoing.is_grant():
                    self._has_token = True
            if self._has_token:
                if self.has_work():
                    self.do_work()
                nxt = (self.index() + 1) % self.number_of_devices()
                self._has_token = False
                self.medium().send(MutexMessage(self.index(), nxt, Type.GRANT))
            self.medium().wait_for_next_round()

    def print_result(self):
        print(f"Token Ring {self.index()} Terminated with request? {self._requested}")


class StampedMessage(MutexMessage):

    def __init__(self, sender: int, destination: int, message_type: Type, time: int):
        super().__init__(sender, destination, message_type)
        self._stamp = time

    def stamp(self) -> int:
        return self._stamp

    def __str__(self):
        return super().__str__() + f' [stamp={self._stamp}]'


class State(enum.Enum):
    HELD = 0
    WANTED = 1
    RELEASED = 3


class RicartAgrawala(WorkerDevice):

    def __init__(self, index: int, number_of_devices: int, medium: Medium):
        super().__init__(index, number_of_devices, medium)
        self._state = State.RELEASED
        self._time = 0
        self._waiting = []
        self._grants = 0

    def run(self):
        while True:
            if self.has_work():
                self.acquire()
            while True:
                ingoing = self.medium().receive()
                if ingoing is not None:
                    if ingoing.is_grant():
                        self.handle_grant(ingoing)
                    elif ingoing.is_request():
                        self.handle_request(ingoing)
                else:
                    break
            self.medium().wait_for_next_round()

    def handle_request(self, message: StampedMessage):
        new_time = max(self._time, message.stamp()) + 1
        if self._state == State.HELD or (self._state == State.WANTED and
                                         (self._time, self.index()) < (message.stamp(), message.source)):
            self._time = new_time
            self._waiting.append(message.source)
        else:
            new_time += 1
            self.medium().send(StampedMessage(self.index(), message.source, Type.GRANT, new_time))
            self._time = new_time

    def handle_grant(self, message: StampedMessage):
        self._grants += 1
        self._time = max(self._time, message.stamp()) + 1
        if self._grants == self.number_of_devices() - 1:
            self._state = State.HELD
            self.do_work()
            self.release()

    def release(self):
        self._grants = 0
        self._state = State.RELEASED
        self._time += 1
        for id in self._waiting:
            self.medium().send(
                StampedMessage(self.index(), id, Type.GRANT, self._time)
            )
        self._waiting.clear()

    def acquire(self):
        if self._state == State.WANTED:
            return
        self._state = State.WANTED
        self._time += 1
        for id in self.medium().ids():
            if id != self.index():
                self.medium().send(
                    StampedMessage(self.index(), id,
                                   Type.REQUEST, self._time))

    def print_result(self):
        print(f"RA {self.index()} Terminated with request? {self._state == State.WANTED}")


class Maekawa(WorkerDevice):

    def __init__(self, index: int, number_of_devices: int, medium: Medium):
        super().__init__(index, number_of_devices, medium)
        self._state = State.RELEASED
        self._waiting = []
        self._voted = False
        self._grants = 0
        # Generate quorums/ voting set
        self._voting_set = set()
        dimension = int(math.sqrt(self.number_of_devices()))
        offset_x = self.index() % dimension
        offset_y = int(self.index() / dimension)
        for i in range(0, dimension):
            # same "column"
            if i * dimension + offset_x < self.number_of_devices():
                self._voting_set.add(i * dimension + offset_x)
            # same "row"
            if offset_y * dimension + i < self.number_of_devices():
                self._voting_set.add(offset_y * dimension + i)

    def run(self):
        while True:
            ingoing = self.medium().receive()
            if ingoing is not None:
                if ingoing.is_grant():
                    self.handle_grant(ingoing)
                elif ingoing.is_request():
                    self.handle_request(ingoing)
                elif ingoing.is_release():
                    self.handle_release(ingoing)
            if self.has_work():
                self.acquire()
            self.medium().wait_for_next_round()

    def acquire(self):
        if self._state == State.WANTED:
            return
        self._state = State.WANTED
        for id in self._voting_set:
            self.medium().send(MutexMessage(self.index(), id, Type.REQUEST))

    def handle_grant(self, message: MutexMessage):
        self._grants += 1
        if self._grants == len(self._voting_set):
            self._state = State.HELD
            self.do_work()
            self.release()

    def release(self):
        self._grants = 0
        self._state = State.RELEASED
        for id in self._voting_set:
            self.medium().send(MutexMessage(self.index(), id, Type.RELEASE))

    def handle_request(self, message: MutexMessage):
        if self._state == State.HELD or self._voted:
            self._waiting.append(message.source)
        else:
            self._voted = True
            self.medium().send(MutexMessage(self.index(), message.source, Type.GRANT))

    def handle_release(self, message: MutexMessage):
        if len(self._waiting) > 0:
            nxt = self._waiting.pop(0)
            self._voted = True
            self.medium().send(MutexMessage(self.index(), nxt, Type.GRANT))
        else:
            self._voted = False

    def print_result(self):
        print(f"MA {self.index()} Terminated with request? {self._state == State.WANTED}")


class SKToken(MessageStub):
    def __init__(self, sender: int, destination: int, queue: [int], ln: [int]):
        super().__init__(sender, destination)
        self._queue = queue
        self._ln = ln

    def queue(self):
        return self._queue

    def ln(self):
        return self._ln

    def __str__(self):
        return f"Token: {self.source} -> {self.destination}, \n" \
               f"\t\tQueue {str(self._queue)}\n" \
               f"\t\tLN {str(self._ln)}"


class SuzukiKasami(WorkerDevice):

    def __init__(self, index: int, number_of_devices: int, medium: Medium):
        super().__init__(index, number_of_devices, medium)
        self._rn = [0 for _ in range(0, number_of_devices)]
        self._waiting = []
        self._token = None

        # By tradition, let index=0 start with the token
        if index == 0:
            self._token = ([], [0 for _ in range(0, number_of_devices)])
        self._working = False
        self._requested = False

    def run(self):
        while True:
            self.handle_messages()
            if self.has_work():
                if self._token is not None:
                    self._working = True
                    self.do_work()
                    # make sure we cleanup the message queue before continuing
                    self.handle_messages()
                    self.release()
                else:
                    self.acquire()

            self.medium().wait_for_next_round()

    def handle_messages(self):
        while True:
            ingoing = self.medium().receive()
            if ingoing is None:
                break
            if isinstance(ingoing, SKToken):
                self._token = (ingoing.queue(), ingoing.ln())
            elif ingoing.is_request():
                self.handle_request(ingoing)

    def handle_request(self, message: StampedMessage):
        self._rn[message.source] = max(self._rn[message.source], message.stamp())
        if self._token is not None and not self._working:
            (queue, ln) = self._token
            if self._rn[message.source] == ln[message.source] + 1:
                self._token = None
                self.medium().send(SKToken(self.index(), message.source, queue, ln))

    def release(self):
        self._working = False
        self._requested = False
        (queue, ln) = self._token
        ln[self.index()] = self._rn[self.index()]
        # let's generate a new queue with all devices with outstanding requests
        for id in self.medium().ids():
            if ln[id] + 1 == self._rn[id]:
                if id not in queue:
                    queue.append(id)
        # if anybody has an outstanding request, grant it
        if len(queue) > 0:
            nxt = queue.pop(0)
            self._token = None
            self.medium().send(SKToken(self.index(), nxt, queue, ln))

    def acquire(self):
        if self._requested:
            return
        # Tell everyone that we want the token!
        self._requested = True
        self._rn[self.index()] += 1
        for id in self.medium().ids():
            if id != self.index():
                self.medium().send(
                    StampedMessage(self.index(), id, Type.REQUEST, self._rn[self.index()]))


# Election Algorithms

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


class ChangRoberts(Device):
    def __init__(self, index: int, number_of_devices: int, medium: Medium):
        super().__init__(index, number_of_devices, medium)
        self._leader = None
        self._participated = False

    def run(self):
        while True:
            nxt = (self.index() + 1) % self.number_of_devices()
            if not self._participated:
                self.medium().send(
                    Vote(self.index(), nxt, self.index(), False))
                self._participated = True
            ingoing = self.medium().receive()
            if ingoing is not None:
                if ingoing.vote() == self.index():
                    if not ingoing.decided():
                        self.medium().send(
                            Vote(self.index(), nxt, self.index(), True))
                    else:
                        self._leader = self.index()
                        return  # this device is the new leader
                elif ingoing.vote() < self.index():
                    continue
                elif ingoing.vote() > self.index():
                    # forward the message
                    self.medium().send(
                        Vote(self.index(), nxt, ingoing.vote(), ingoing.decided()))
                    if ingoing.decided():
                        self._leader = ingoing.vote()
                        return
            self.medium().wait_for_next_round()

    def print_result(self):
        print(f'Leader seen from {self._id} is {self._leader}')


class Bully(Device):

    def __init__(self, index: int, number_of_devices: int, medium: Medium):
        super().__init__(index, number_of_devices, medium)
        self._leader = None
        self._shut_up = False
        self._election = False

    def largest(self):
        return self.index() == max(self.medium().ids())

    def run(self):
        first_round = True
        while True:
            got_input = False
            if not self._shut_up and not self._election:
                self.start_election()

            new_election = False
            while True:
                ingoing = self.medium().receive()
                if ingoing is not None:
                    got_input = True
                    if ingoing.vote() < self.index():
                        self.medium().send(Vote(self.index(), ingoing.source, self.index(), self.largest()))
                        new_election = True
                    else:
                        self._shut_up = True
                        if ingoing.decided():
                            self._leader = ingoing.vote()
                            return
                else:
                    break
            if not self._shut_up and not self._election and new_election:
                self.start_selection()
            # after enough time since election
            if not got_input and not first_round:
                if self._election:
                    if self._shut_up:
                        self._shut_up = False
                        self.start_election()
                    else:
                        # we are the new leader, we could declare everybody else dead
                        for id in self.medium().ids():
                            if id != self.index():
                                self.medium().send(Vote(self.index(), id, self.index(), True))
                        self._leader = self.index()
                        return
            self.medium().wait_for_next_round()
            first_round = False

    def start_election(self):
        if not self._election:
            self._election = True
            for id in self.medium().ids():
                if id > self.index():
                    self.medium().send(Vote(self.index(), id, self.index(), self.largest()))

    def print_result(self):
        print(f'Leader seen from {self._id} is {self._leader}')
