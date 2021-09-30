import threading

from emulators.MessageStub import MessageStub


class Medium:
    _id: int

    def __init__(self, index: int, emulator):
        self._id = index
        self._emulator = emulator

    def send(self, message: MessageStub):
        self._emulator.queue(message)

    def receive(self) -> MessageStub:
        return self._emulator.dequeue(self._id)

    def wait_for_next_round(self):
        self._emulator.done(self._id)

    def ids(self):
        return self._emulator.ids()
