from emulators.Device import Device
from emulators.Medium import Medium
from emulators.MessageStub import MessageStub


class GossipMessage(MessageStub):

    def __init__(self, sender: int, destination: int, secrets):
        super().__init__(sender, destination)
        # we use a set to keep the "secrets" here
        self.secrets = secrets

    def __str__(self):
        return f'{self.source} -> {self.destination} : {self.secrets}'


class Gossip(Device):

    def __init__(self, index: int, number_of_devices: int, medium: Medium):
        super().__init__(index, number_of_devices, medium)
        # for this exercise we use the index as the "secret", but it could have been a new routing-table (for instance)
        # or sharing of all the public keys in a cryptographic system
        self._secrets = set([index])
        

    def run(self):
        # the following is your termination condition, but where should it be placed?
        while True:

            # merge my knowledge with received messages
            for ingoing in self.medium().receive_all():
                self._secrets = self._secrets.union(ingoing.secrets)

            # create messages for neighbours
            left_index = self.index() - 1
            if left_index < 0:
                left_index = self.number_of_devices() - 1

            right_index = self.index() + 1 # to avoid the following if; ..= (self.index() + 1) % self.number_of_devices()
            if right_index >= self.number_of_devices():
                right_index = 0
            
            for other in [left_index, right_index]: # to have totally connected, send to self.medium().ids() -- except ofc. self.index()
                message = GossipMessage(self.index(), other, self._secrets)
                self.medium().send(message)

            if len(self._secrets) == self.number_of_devices():
                return
            self.medium().wait_for_next_round()
        return

    def print_result(self):
        print(f'\tDevice {self.index()} got secrets: {self._secrets}')
