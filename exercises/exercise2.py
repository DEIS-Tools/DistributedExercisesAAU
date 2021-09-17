from emulators.Device import Device
from emulators.Medium import Medium
from emulators.MessageStub import MessageStub


class RipMessage(MessageStub):
    def __init__(self, sender: int, destination: int, table):
        super().__init__(sender, destination)
        self.table = table

    def __str__(self):
        return f'RipMessage: {self.source} -> {self.destination} : {self.table}'

class RoutableMessage(MessageStub):
    def __init__(self, sender: int, destination: int, first_node: int, last_node: int, content):
        super().__init__(sender, destination)
        self.content = content
        self.first_node = first_node
        self.last_node = last_node

    def __str__(self):
        return f'RoutableMessage: {self.source} -> {self.destination} : {self.content}'




class RipCommunication(Device):

    def __init__(self, index: int, number_of_devices: int, medium: Medium):
        super().__init__(index, number_of_devices, medium)
        
        self.neighbors = [] # generate an appropriate list

        self.routing_table = dict()

    def run(self):
        for neigh in self.neighbors:
            self.routing_table[neigh] = (neigh, 1)
        self.routing_table[self.index()] = (self.index(), 0)
        for neigh in self.neighbors:
            self.medium().send(RipMessage(self.index(), neigh, self.routing_table))

        while True:
            ingoing = self.medium().receive()
            if ingoing is None:
                # this call is only used for synchronous networks
                self.medium().wait_for_next_round()
                continue

            if type(ingoing) is RipMessage:
                print(f"Device {self.index()}: Got new table from {ingoing.source}")
                returned_table = self.merge_tables(ingoing.source, ingoing.table)
                if returned_table is not None:
                    self.routing_table = returned_table
                    for neigh in self.neighbors:
                        self.medium().send(RipMessage(self.index(), neigh, self.routing_table))

            if type(ingoing) is RoutableMessage:
                print(f"Device {self.index()}: Routing from {ingoing.first_node} to {ingoing.last_node} via #{self.index()}: [#{ingoing.content}]")
                if ingoing.last_node is self.index():
                    print(f"\tDevice {self.index()}: delivered message from {ingoing.first_node} to {ingoing.last_node}: {ingoing.content}")
                    continue
                if self.routing_table[ingoing.last_node] is not None:
                    (next_hop, distance) = self.routing_table[ingoing.last_node]
                    self.medium().send(RoutableMessage(self.index(), next_hop, ingoing.first_node, ingoing.last_node, ingoing.content))
                    continue
                print(f"\tDevice {self.index()}:  DROP Unknown route #{ingoing.first_node} to #{ingoing.last_node} via #{self.index}, message #{ingoing.content}")

            # this call is only used for synchronous networks
            self.medium().wait_for_next_round()

    def merge_tables(self, src, table):
        # return None if the table does not change
        pass


    def print_result(self):
        print(f'\tDevice {self.index()} has routing table: {self.routing_table}')