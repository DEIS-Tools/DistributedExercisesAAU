import threading

from emulators.MessageStub import MessageStub


class Medium:
    """
    Represents a communication medium in a simulation.

    Args:
        index (int): The unique identifier for the medium.
        emulator: The emulator object responsible for managing message queues.

    Attributes:
        _id (int): The unique identifier for the medium.
        _emulator: The emulator object associated with the medium.
    """
    _id: int

    def __init__(self, index: int, emulator):
        self._id = index
        self._emulator = emulator

    def send(self, message: MessageStub):
        """
        Send a message through the medium.

        Args:
            message (MessageStub): The message to be sent.
        """
        self._emulator.queue(message)

    def receive(self) -> MessageStub:
        """
        Receive a message from the medium.

        Returns:
            MessageStub: The received message.
        """
        return self._emulator.dequeue(self._id)

    def receive_all(self) -> list[MessageStub]:
        """
        Receive all available messages from the medium.

        Returns:
            list[MessageStub]: A list of received messages.
        """
        messages = []
        while True:
            message = self._emulator.dequeue(self._id)
            if message is None:
                return messages
            messages.append(message)

    def wait_for_next_round(self):
        """
        Wait for the next communication round.

        This method signals that the device is waiting for the next communication round to begin.
        """
        self._emulator.done(self._id)

    def ids(self):
        """
        Get the unique identifier of the medium.

        Returns:
            int: The unique identifier of the medium.
        """
        return self._emulator.ids()
