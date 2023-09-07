class MessageStub:
    """
    Represents a message used in communication within a simulation.

    Attributes:
        _source (int): The identifier of the message sender.
        _destination (int): The identifier of the message receiver.
    """
    _source: int
    _destination: int

    def __init__(self, sender_id: int, destination_id: int):
        """
        Initialize a MessageStub instance.

        Args:
            sender_id (int): The identifier of the message sender.
            destination_id (int): The identifier of the message receiver.
        """
        self._source = sender_id
        self._destination = destination_id

    @property
    def destination(self) -> int:
        """
        Get the identifier of the message's destination.

        Returns:
            int: The identifier of the destination device.
        """
        return self._destination

    @property
    def source(self) -> int:
        """
        Get the identifier of the message's source.

        Returns:
            int: The identifier of the source device.
        """
        return self._source

    @destination.setter
    def destination(self, value):
        """
        Set the identifier of the message's destination.

        Args:
            value (int): The new identifier for the destination device.
        """
        self._destination = value

    @source.setter
    def source(self, value):
        """
        Set the identifier of the message's source.

        Args:
            value (int): The new identifier for the source device.
        """
        self._source = value
