import math
import random
import sys
import threading
from typing import Optional

from emulators.Device import Device
from emulators.Medium import Medium
from emulators.MessageStub import MessageStub

import json
import time

# if you need controlled repetitions:
# random.seed(100)

# probability that each arc is part of the graph
# 0.2 seems good for 10 nodes.
# For more nodes, I suggest a lower probability
# For less nodes, I suggest a higher probability
probability_arc = 0.2


class AodvNode(Device):
    # I am doing a hack for the termination: I have a global variable increasing every time a data message is received. When it is high enough, the device sends a Quit to everybody
    data_messages_received = 0
    messages_lock = threading.Lock()

    def __init__(self, index: int, number_of_devices: int, medium: Medium):
        super().__init__(index, number_of_devices, medium)
        # I get the topology from the singleton
        self.neighbors = TopologyCreator.get_topology(number_of_devices, probability_arc)[index]
        # I initialize the "routing tables". Feel free to create your own structure if you prefer
        self.forward_path: dict[int, int] = {}  # "Destination index" --> "Next-hop index"
        self.reverse_path: dict[int, int] = {}  # "Source index" --> "Next-hop index"
        self.bcast_ids = []  # Type hint left out on purpose due to tasks below
        # data structures to cache outgoing messages, and save received data
        self.saved_data: list[str] = []
        self.outgoing_message_cache: list[DataMessage] = []

    def run(self):
        last = random.randint(0, self.number_of_devices() - 1)
        # I send the message to myself, so it gets routed
        message = DataMessage(self.index(), self.index(), last, f"Hi. I am {self.index()}.")
        self.medium().send(message)
        while True:
            for ingoing in self.medium().receive_all():
                if not self.handle_ingoing(ingoing):
                    return
            self.medium().wait_for_next_round()

    def next_hop(self, last: int) -> Optional[int]:
        return self.forward_path.get(last)  # Returns "None" if key does not exist

    def handle_ingoing(self, ingoing: MessageStub):
        if isinstance(ingoing, DataMessage):
            if self.index() == ingoing.last:
                # the message is for me
                self.saved_data.append(ingoing.data)
                # <hack for the termination>
                AodvNode.messages_lock.acquire()
                AodvNode.data_messages_received += 1
                AodvNode.messages_lock.release()
                if AodvNode.data_messages_received == self.number_of_devices():
                    for i in range(0, self.number_of_devices()):
                        self.medium().send(QuitMessage(self.index(), i))
                # </hack for the termination>
            else:
                next = self.next_hop(ingoing.last) # change self.next_hop if you implement a different data structure for the routing tables
                if next is not None:
                    # I know how to reach the destination
                    message = DataMessage(self.index(), next, ingoing.last, ingoing.data)
                    self.medium().send(message)
                    return True
                # I don't have the route to the destination.
                # I need to save the outgoing message in a cache
                # then, I need to send out a Route Request
                # TODO
                pass
        if isinstance(ingoing, AodvRreqMessage):
            # if I have already seen the bcast_id, I ignore the message.
            # What can I use as a broadcast id?
            # TODO
            pass

            # If I don't have the reverse_path in my routing table, I save it
            # TODO
            pass

            if self.index() == ingoing.last:
                # the message is for me. I can send back a Route Reply
                # TODO
                pass
            else:
                # continue the broadcast
                # TODO
                pass
        if isinstance(ingoing, AodvRrepMessage):
            # If I don't have the forward_path in my routing table, I save it
            # TODO

            if self.index() == ingoing.first:
                # Finally, I can send all the messages I had saved "first -> last" from my cache
                # TODO
                pass
            else:
                # continue the unicast back towards "first".
                # TODO
                pass
        if isinstance(ingoing, QuitMessage):
            return False
        return True

    def print_result(self):
        print(f"AODV node {self.index()} quits: neighbours = {self.neighbors}, forward paths = {self.forward_path}, reverse paths = {self.reverse_path}, saved data = {self.saved_data}, length of message cache (should be 0) = {len(self.outgoing_message_cache)}")


class TopologyCreator:
    # singleton design pattern
    __topology: dict[int, list[int]] = None  # "Node index" --> [neighbor node indices]

    def __check_connected(topology: dict[int, list[int]]) -> Optional[tuple[int, int]]:
        # if the network is connected, it returns None;
        # if not, it returns two nodes belonging to two different partitions
        queue = [0]
        visited = [0]
        while queue:
            s = queue.pop(0)
            for neigh in topology.get(s):
                if neigh not in visited:
                    visited.append(neigh)
                    queue.append(neigh)
        for n in topology:
            if n not in visited:
                return (visited[-1], n)
        return None

    def __create_topology(number_of_devices: int, probability: float):
        topology: dict[int, list[int]] = {}
        for i in range(0, number_of_devices):
            topology[i] = []
        for i in range(0, number_of_devices):
            for j in range(0, i):
                if random.random() < probability:
                    topology[i].append(j)
                    topology[j].append(i)
        while TopologyCreator.__check_connected(topology) is not None:
            (i, j) = TopologyCreator.__check_connected(topology)
            topology[i].append(j)
            topology[j].append(i)
        return topology

    @classmethod
    def get_topology(cls, number_of_devices: int, probability: float):
        if cls.__topology is None:
            cls.__topology = TopologyCreator.__create_topology(number_of_devices, probability)
        return cls.__topology


class QuitMessage(MessageStub):
    def __init__(self, sender: int, destination: int):
        super().__init__(sender, destination)

    def __str__(self):
        return f'QUIT REQUEST {self.source} -> {self.destination}'


class AodvRreqMessage(MessageStub):
    def __init__(self, sender: int, destination: int, first: int, last: int):
        super().__init__(sender, destination)
        self.first = first
        self.last = last

    def __str__(self):
        return f'RREQ MESSAGE {self.source} -> {self.destination}: ({self.first} -> {self.last})'


class AodvRrepMessage(MessageStub):
    def __init__(self, sender: int, destination: int, first: int, last: int):
        super().__init__(sender, destination)
        self.first = first
        self.last = last

    def __str__(self):
        return f'RREP MESSAGE {self.source} -> {self.destination}: ({self.first} -> {self.last})'


class DataMessage(MessageStub):
    def __init__(self, sender: int, destination: int, last: int, data: str):
        super().__init__(sender, destination)
        self.last = last
        self.data = data

    def __str__(self):
        return f'DATA MESSAGE {self.source} -> {self.destination}: (final target = {self.last}, data = "{self.data}")'
