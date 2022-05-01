import random

from emulators.Device import Device
from emulators.Medium import Medium
from emulators.MessageStub import MessageStub


# We extend the MessageStub here for the message-types we wish to communicate
class PingMessage(MessageStub):

    # the constructor-function takes the source and destination as arguments. These are used for "routing" but also
    # for pretty-printing. Here we also take the specific flag of "is_ping"
    def __init__(self, sender: int, destination: int, is_ping: bool):
        # first thing to do (mandatory), is to send the arguments to the "MessageStub" constructor
        super().__init__(sender, destination)
        # finally we set the field
        self.is_ping = is_ping

    # remember to implement the __str__ method such that the debug of the framework works!
    def __str__(self):
        if self.is_ping:
            return f'{self.source} -> {self.destination} : Ping'
        else:
            return f'{self.source} -> {self.destination} : Pong'


# This class extends on the basic Device class. We will implement the protocol in the run method
class PingPong(Device):

    # The constructor must have exactly this form.
    def __init__(self, index: int, number_of_devices: int, medium: Medium):
        # forward the constructor arguments to the super-constructor
        super().__init__(index, number_of_devices, medium)
        # for this small example, all UNEVEN indexed devices will start with a ping
        self._is_ping = (index % 2) == 0
        self._rec_ping = 0
        self._rec_pong = 0

    # this method implements the actual algorithm
    def run(self):
        # for this algorithm, we will repeat the protocol 10 times and then stop
        for repetetions in range(0, 10):
            # in each repetition, let us send the ping to one random other device
            message = PingMessage(self.index(), random.randrange(0, self.number_of_devices()), self._is_ping)
            # we send the message via a "medium"
            self.medium().send(message)
            # in this instance, we also try to receive some messages, there can be multiple, but
            # eventually the medium will return "None"
            while True:
                ingoing = self.medium().receive()
                if ingoing is None:
                    break

                # let's keep some statistics
                if ingoing.is_ping:
                    self._rec_ping += 1
                else:
                    self._rec_pong += 1

                # in this protocol, we ignore the message if it is the same state as us
                if self._is_ping == ingoing.is_ping:
                    continue
                else:
                    # we were ping and got pong, or were pong and got ping
                    self._is_ping = ingoing.is_ping

            # this call is only used for synchronous networks
            self.medium().wait_for_next_round()

    # for pretty-printing and debugging, implement this function
    def print_result(self):
        print(f'\tDevice {self.index()} got pings: {self._rec_ping} and pongs: {self._rec_pong}')
