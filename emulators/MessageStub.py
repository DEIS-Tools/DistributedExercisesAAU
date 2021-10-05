class MessageStub:
    _source: int
    _destination: int

    def __init__(self, sender_id: int, destination_id: int):
        self._source = sender_id
        self._destination = destination_id

    @property
    def destination(self) -> int:
        return self._destination

    @property
    def source(self) -> int:
        return self._source

    @destination.setter
    def destination(self, value):
        self._destination = value

    @source.setter
    def source(self, value):
        self._source = value
