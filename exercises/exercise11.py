import math
import random
import sys
from typing import Optional

from emulators.Device import Device
from emulators.Medium import Medium
from emulators.MessageStub import MessageStub

import json
import time


# if you need controlled repetitions:
# random.seed(100)


# size for the chord addresses in bits
address_size = 6
# only for initialization:
all_nodes: list[int] = []
all_routing_data: list["RoutingData"] = []


class RoutingData:
    # all tuples ("prev" and the ones in the finger_table) are (index, chord_id)
    def __init__(self, index: int, chord_id: int, prev: tuple[int, int], finger_table: list[tuple[int, int]]):
        self.index = index
        self.chord_id = chord_id
        self.prev = prev
        self.finger_table = finger_table

    def to_string(self):
        ret = f"Node ({self.index}, {self.chord_id}) prev {self.prev} finger_table {self.finger_table}"
        return ret


def in_between(candidate: int, low: int, high: int):
    # the function returns False when candidate == low or candidate == high
    # take care of those cases in the calling function
    if low == high:
        return False
    if low < high:
        return candidate > low and candidate < high
    else:
        return candidate > low or candidate < high


class ChordNode(Device):
    def __init__(self, index: int, number_of_devices: int, medium: Medium, connected: bool, routing_data: Optional[RoutingData]):
        super().__init__(index, number_of_devices, medium)
        self.connected = connected
        self.routing_data = routing_data
        self.saved_data: list[str] = []

    def run(self):
        # a chord node acts like a server
        while True:
            for ingoing in self.medium().receive_all():
                if not self.handle_ingoing(ingoing):
                    return
            self.medium().wait_for_next_round()

    def is_request_for_me(self, guid: int) -> bool:
        # TODO: implement this function that checks if the routing process is over
        pass

    def next_hop(self, guid: int) -> int:
        # TODO: implement this function with the routing logic
        pass

    def handle_ingoing(self, ingoing: MessageStub):
        if isinstance(ingoing, PutMessage):
            # TODO: implement the test "is_request_for_me"
            if self.is_request_for_me(ingoing.guid):
                self.saved_data.append(ingoing.data)
            else:
                # TODO: route the message
                # you can fill up the next_hop function for this
                next_hop = self.next_hop(ingoing.guid)
                message = PutMessage(self.index(), next_hop, ingoing.guid, ingoing.data)
                self.medium().send(message)
        if isinstance(ingoing, GetReqMessage):
            # maybe TODO, but the GET is not very interesting
            pass
        if isinstance(ingoing, StartJoinMessage):
            # here you start the join process
            pass
        if isinstance(ingoing, JoinReqMessage):
            # TODO
            pass
        if isinstance(ingoing, JoinRspMessage):
            # TODO
            pass
        if isinstance(ingoing, NotifyMessage):
            # TODO
            pass
        if isinstance(ingoing, StabilizeMessage):
            # TODO
            pass
        if isinstance(ingoing, QuitMessage):
            return False
        return True

    def print_result(self):
        if self.routing_data is not None:
            my_range = self.routing_data.chord_id - self.routing_data.prev[1]
            if my_range < 0:
                my_range += pow(2, address_size)
            print(f"Chord node {self.index()} quits, it managed {my_range} addresses, it had {len(self.saved_data)} data blocks")
        else:
            print(f"Chord node {self.index()} quits, it was still disconnected")


class ChordClient(Device):
    def __init__(self, index: int, number_of_devices: int, medium: Medium):
        super().__init__(index, number_of_devices, medium)

    def run(self):
        for i in range(pow(2, address_size)):
            guid = i # I send a message to each address, to check if each node stores one data for each address it manages
            # if your chord address space gets too big, use the following code:
            # for i in range(pow(2, address_size)):
            # guid = random.randint(0, pow(2,address_size)-1)
            message = PutMessage(self.index(), 2, guid, "hello")
            self.medium().send(message)

        # TODO: uncomment this code to start the JOIN process
        #new_chord_id = random.randint(0, pow(2,address_size)-1)
        #while new_chord_id in all_nodes:
        #   new_chord_id = random.randint(0, pow(2,address_size)-1)
        #message = StartJoinMessage(self.index(), 1, new_chord_id)
        #self.medium().send(message)

        time.sleep(10) # or use some smart trick to wait for the routing process to be completed before shutting down the distributed system
        for i in range(1, self.number_of_devices()):
            message = QuitMessage(self.index(), i)
            self.medium().send(message)
        return

        # currently, I do not manage incoming messages
        # while True:
        #     for ingoing in self.medium().receive_all():
        #         if not self.handle_ingoing(ingoing):
        #             return
        #     self.medium().wait_for_next_round()

    def handle_ingoing(self, ingoing: MessageStub):
        if isinstance(ingoing, QuitMessage):
            return False
        return True

    def print_result(self):
        print(f"client {self.index()} quits")


class ChordNetwork:
    def init_routing_tables(number_of_devices: int):
        N = number_of_devices-2 # routing_data 0 will be for device 2, etc
        while len(all_nodes) < N:
            new_chord_id = random.randint(0, pow(2,address_size)-1)
            if new_chord_id not in all_nodes:
                all_nodes.append(new_chord_id)
        all_nodes.sort()

        for id in range(N):
            prev_id = (id-1) % N
            prev = (prev_id+2, all_nodes[prev_id])  # Add 2 to get "message-able" device index
            new_finger_table = []
            for i in range(address_size):
                at_least = (all_nodes[id] + pow(2, i)) % pow(2, address_size)
                candidate = (id+1) % N
                while in_between(all_nodes[candidate], all_nodes[id], at_least):
                    candidate = (candidate+1) % N
                new_finger_table.append((candidate+2, all_nodes[candidate])) # I added 2 to candidate since routing_data 0 is for device 2, and so on
            all_routing_data.append(RoutingData(id+2, all_nodes[id], prev, new_finger_table))
            print(RoutingData(id+2, all_nodes[id], prev, new_finger_table).to_string())

    def __new__(cls, index: int, number_of_devices: int, medium: Medium):
        # device #0 is the client
        # device #1 is a disconnected node
        # since device #2, they are connected nodes

        # if all_nodes is empty, I init it:
        if all_nodes == []:
            cls.init_routing_tables(number_of_devices)

        if index == 0:
            return ChordClient(index, number_of_devices, medium)
        if index == 1:
            return ChordNode(index, number_of_devices, medium, False, None)
        if index > 1:
            return ChordNode(index, number_of_devices, medium, True, all_routing_data[index-2])


class QuitMessage(MessageStub):
    def __init__(self, sender: int, destination: int):
        super().__init__(sender, destination)

    def __str__(self):
        return f'QUIT REQUEST {self.source} -> {self.destination}'


class PutMessage(MessageStub):
    def __init__(self, sender: int, destination: int, guid: int, data: str):
        super().__init__(sender, destination)
        self.guid = guid
        self.data = data

    def __str__(self):
        return f'PUT MESSAGE {self.source} -> {self.destination}: ({self.guid}, {self.data})'


class GetReqMessage(MessageStub):
    def __init__(self, sender: int, destination: int, guid: int):
        super().__init__(sender, destination)
        self.guid = guid

    def __str__(self):
        return f'GET REQUEST MESSAGE {self.source} -> {self.destination}: ({self.guid})'


class GetRspMessage(MessageStub):
    def __init__(self, sender: int, destination: int, guid: int, data: str):
        super().__init__(sender, destination)
        self.guid = guid
        self.data = data

    def __str__(self):
        return f'GET RESPONSE MESSAGE {self.source} -> {self.destination}: ({self.guid}, {self.data})'


class StartJoinMessage(MessageStub):
    def __init__(self, sender: int, destination: int):
        super().__init__(sender, destination)

    def __str__(self):
        return f'StartJoinMessage MESSAGE {self.source} -> {self.destination}'


class JoinReqMessage(MessageStub):
    def __init__(self, sender: int, destination: int): # etc
        super().__init__(sender, destination)

    def __str__(self):
        return f'JoinReqMessage MESSAGE {self.source} -> {self.destination}'


class JoinRspMessage(MessageStub):
    def __init__(self, sender: int, destination: int): # etc
        super().__init__(sender, destination)

    def __str__(self):
        return f'JoinRspMessage MESSAGE {self.source} -> {self.destination}'


class NotifyMessage(MessageStub):
    def __init__(self, sender: int, destination: int): # etc
        super().__init__(sender, destination)

    def __str__(self):
        return f'NotifyMessage MESSAGE {self.source} -> {self.destination}'


class StabilizeMessage(MessageStub):
    def __init__(self, sender: int, destination: int): # etc
        super().__init__(sender, destination)

    def __str__(self):
        return f'StabilizeMessage MESSAGE {self.source} -> {self.destination}'
