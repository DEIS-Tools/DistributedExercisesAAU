import random
import threading
import time

import math
import copy

from emulators.Device import Device
from emulators.Medium import Medium
from emulators.MessageStub import MessageStub

class MulticastMessage(MessageStub):
    def __init__(self, sender: int, destination: int, content):
        super().__init__(sender, destination)
        self._content = content

    def content(self):
        return self._content

    def __str__(self):
        return f'Multicast: {self.source} -> {self.destination} [{self._content}]'


class MulticastListener:
    def deliver(self, content):
        raise NotImplementedError

    def forward(self, message):
        raise NotImplementedError


class MulticastService:
    def send(self, content):
        raise NotImplementedError


class Multicaster(MulticastListener):
    def __init__(self, index, multicast: MulticastService):
        self._index = index
        self._multicast = multicast
        self._mid = 0
        self._thread = threading.Thread(target=self.run)
        self._thread.start()

    def run(self):
        while True:
            time.sleep(random.uniform(0.1, 3))
            self._multicast.send(f"Generated message ({self._index}, {self._mid})")
            self._mid += 1

    def deliver(self, content):
        print(f"\t\t\t\t Final Deliver at {self._index}: {content}")

    def forward(self, message):
        self.deliver(message)


class BasicMulticast(Device, MulticastService):

    def __init__(self, index: int, number_of_devices: int, medium: Medium, application: MulticastListener = None):
        super().__init__(index, number_of_devices, medium)
        if application is not None:
            self._application = application
        else:
            self._application = Multicaster(index, self)
        self._outbox = []

    def run(self):
        while True:
            for ingoing in self.medium().receive_all():
                self.handle_ingoing(ingoing)
            while len(self._outbox) > 0:
                msg = self._outbox.pop(0)
                self.send_to_all(msg)
            self.medium().wait_for_next_round()

    def handle_ingoing(self, ingoing: MessageStub):
        if isinstance(ingoing, MulticastMessage):
            self._application.deliver(ingoing.content())
        else:
            self._application.forward(ingoing)

    def send_to_all(self, content):
        for id in self.medium().ids():
            # we purposely send to ourselves also!
            message = MulticastMessage(self.index(), id, content)
            self.medium().send(message)

    def send(self, message):
        self._outbox.append(copy.deepcopy(message))

    def print_result(self):
        print("Done!")


class ReliableMulticast(MulticastListener, MulticastService, Device):

    def __init__(self, index: int, number_of_devices: int, medium: Medium, application: MulticastListener = None):
        super().__init__(index, number_of_devices, medium)
        if application is not None:
            self._application = application
        else:
            self._application = Multicaster(index, self)
        self._b_multicast = BasicMulticast(index, number_of_devices, medium, self)
        self._seq_number = 0  # not strictly needed, but helps giving messages a unique ID
        self._received = set()

    def send(self, content):
        self._b_multicast.send((self.index(), self._seq_number, content))
        self._seq_number += 1

    def deliver(self, message):
        (origin_index, seq_number, content) = message

        if message not in self._received:
            if origin_index is not self.index():
                self._b_multicast.send(message)
            self._received.add(message)
            self._application.deliver(content)

    def run(self):
        self._b_multicast.run()

    def forward(self, message):
        self._application.forward(message)


class NACK(MessageStub):
    def __init__(self, sender: int, destination: int, seq_number: int):
        super().__init__(sender, destination)
        self._seq_number = seq_number

    def seq_number(self):
        return self._seq_number

    def __str__(self):
        return f'NACK: {self.source} -> {self.destination}: {self._seq_number}'


class Resend(MessageStub):
    def __init__(self, sender: int, destination: int, message):
        super().__init__(sender, destination)
        self._message = message

    def message(self):
        return self._message

    def __str__(self):
        return f'Resend: {self.source} -> {self.destination}: {self._message}'


class ReliableIPMulticast(MulticastListener, MulticastService, Device):

    def __init__(self, index: int, number_of_devices: int, medium: Medium, application: MulticastListener = None):
        super().__init__(index, number_of_devices, medium)
        if application is not None:
            self._application = application
        else:
            self._application = Multicaster(index, self)
        self._b_multicast = BasicMulticast(index, number_of_devices, medium, self)
        self._seq_numbers = [0 for _ in medium.ids()]
        self._received = {}

    def deliver(self, message):
        (origin_index, seq_numbers, content) = message
        seq_nr = seq_numbers[origin_index]
        self._received[(origin_index, seq_nr)] = message
        if self._seq_numbers[origin_index] <= seq_nr:
            self.try_deliver()
            self.nack_missing(seq_numbers)

    def send(self, content):
        self._received[(self.index(),
                        self._seq_numbers[self.index()])] = content
        self._b_multicast.send((self.index(), self._seq_numbers, content))
        self.try_deliver()

    def run(self):
        self._b_multicast.run()

    def forward(self, message):
        if isinstance(message, NACK):
            self.medium().send(Resend(self.index(), message.source,
                                      (self.index(), self._seq_numbers,
                                       self._received[(self.index(), message.seq_number())])))
        elif isinstance(message, Resend):
            self.deliver(message.message())
        else:
            self._application.forward(message)

    def try_deliver(self):
        for (oid, seqnr), content in self._received.items():
            if self._seq_numbers[oid] == seqnr:
                self._application.deliver(content)
                self._seq_numbers[oid] += 1
                self.try_deliver()  # recursively!
                return

    def nack_missing(self, n_seq: list[int]):
        for id in range(0, len(n_seq)):
            for mid in range(self._seq_numbers[id] + 1, n_seq[id]):
                self.medium().send(
                    NACK(self.index(), id, mid))


class Order:
    def __init__(self, message_id: (int, int), order: int):
        self._order = order
        self._message_id = message_id

    def order(self):
        return self._order

    def message_id(self):
        return self._message_id

    def __str__(self):
        return f'Order(<{self.message_id()}> = {self.order()})'

class TOSEQMulticast(MulticastListener, MulticastService, Device):

    def __init__(self, index: int, number_of_devices: int, medium: Medium, application: MulticastListener = None):
        super().__init__(index, number_of_devices, medium)
        if application is not None:
            self._application = application
        else:
            self._application = Multicaster(index, self)
        self._b_multicast = BasicMulticast(index, number_of_devices, medium, self)
        self._l_seq = 0
        self._g_seq = 0
        self._order = {}
        self._received = {}

    def send(self, content):
        self._b_multicast.send((self.index(), self._l_seq, content))
        self._l_seq += 1

    def deliver(self, message):
        if not isinstance(message, Order):
            (sid, sseq, content) = message
            mid = (sid, sseq)
            if self.index() == 0:
                # index 0 is global sequencer
                self._order[mid] = self._g_seq
                self._b_multicast.send(Order(mid, self._g_seq))
                self._application.deliver(message)
                self._g_seq += 1
            else:
                self._received[mid] = content
                self.try_deliver()
        elif self.index() != 0:
            # index 0 is global sequencer
            self._order[message.message_id()] = message.order()
            self.try_deliver()

    def try_deliver(self):
        for mid, order in self._order.items():
            if order == self._g_seq and mid in self._received:
                self._g_seq += 1
                self._application.deliver(self._received[mid])
                self.try_deliver()
                return

    def run(self):
        self._b_multicast.run()

    def forward(self, message):
        self._application.forward(message)


class Vote(MessageStub):
    def __init__(self, sender: int, destination: int, order: (int, int), message_id: (int, int)):
        super().__init__(sender, destination)
        self._order = order
        self._message_id = message_id

    def order(self) -> int:
        return self._order

    def message_id(self) -> (int, int):
        return self._message_id

    def __str__(self):
        return f'Vote: {self.source} -> {self.destination}: <{self.message_id()}> = {self.order()}'


class ISISMulticast(MulticastListener, MulticastService, Device):

    def __init__(self, index: int, number_of_devices: int, medium: Medium, application: MulticastListener = None):
        super().__init__(index, number_of_devices, medium)
        if application is not None:
            self._application = application
        else:
            self._application = Multicaster(index, self)
        self._b_multicast = BasicMulticast(index, number_of_devices, medium, self)
        self._l_seq = 0  # local sequence
        self._g_seq = 0  # global sequence
        self._a_seq = -1  # last agreed
        self._p_seq = -1  # last proposed
        self._order = {}  # order of messages
        self._votes = {}  # votes of messages
        self._hb_q = {}  # holdback of messages

    def run(self):
        self._b_multicast.run()

    def send(self, content):
        self._b_multicast.send((self.index(), self._l_seq, content))
        self._votes[(self.index(), self._l_seq)] = []
        self._l_seq += 1

    def deliver(self, message):
        if isinstance(message, Order):
            self._order[message.message_id()] = message.order()
            self._a_seq = max(self._a_seq, message.order())
            self.try_deliver()
        else:
            (sid, sseq, content) = message
            self._hb_q[(sid, sseq)] = content
            self._p_seq = max(self._a_seq, self._p_seq) + 1
            # We should technically send proposer ID for tie-breaks
            self.medium().send(
                Vote(self.index(), sid, self._p_seq, (sid, sseq))
            )

    def forward(self, message):
        if isinstance(message, Vote):
            votes = self._votes[message.message_id()]
            votes.append(message.order())
            if len(votes) == self.number_of_devices():
                self._b_multicast.send(
                    Order(message.message_id(), max(votes))
                )
        else:
            self._application.forward(message)

    def try_deliver(self):
        for mid, content in self._hb_q.items():
            if mid in self._order:
                if self._order[mid] == self._g_seq:
                    self._g_seq += 1
                    self._application.deliver(content)
                    return self.try_deliver()


class COMulticast(MulticastListener, MulticastService, Device):

    def __init__(self, index: int, number_of_devices: int, medium: Medium, application: MulticastListener = None):
        super().__init__(index, number_of_devices, medium)
        if application is not None:
            self._application = application
        else:
            self._application = Multicaster(index, self)
        self._b_multicast = BasicMulticast(index, number_of_devices, medium, self)
        self._n_vect = [-1 for _ in self.medium().ids()]
        self._hb_q = []

    def send(self, content):
        self._n_vect[self.index()] += 1
        self._b_multicast.send((self._n_vect, self.index(), content))

    def deliver(self, message):
        self._hb_q.append(message)
        self.try_deliver()

    def forward(self, message):
        self._application.forward(message)

    def try_deliver(self):
        for (vec, index, content) in self._hb_q:
            if self.is_next(vec, index):
                self._application.deliver(content)
                self._n_vect[index] += 1
                return self.try_deliver()

    def is_next(self, vec, index):
        if vec[index] != self._n_vect[index] + 1:
            return False
        for i in self.medium().ids():
            if i != index and vec[i] > self._n_vect[i]:
                return False
        return True

    def run(self):
        self._b_multicast.run()
