import math
import random
import sys

from emulators.Device import Device
from emulators.Medium import Medium
from emulators.MessageStub import MessageStub

NUMBER_OF_MASTERS = 1
NUMBER_OF_CHUNKSERVERS = 4
NUMBER_OF_REPLICAS = 3
# if you need repetition:
# random.seed(100)

class GfsMaster(Device):
    def __init__(self, index: int, number_of_devices: int, medium: Medium):
        super().__init__(index, number_of_devices, medium)
        self._metadata = {}
        self.chunks_being_allocated = []
        GfsNetwork.gfsmaster.append(index)

    def run(self):
        # since this is a server, its job is to answer for requests (messages), then do something
        while True:
            for ingoing in self.medium().receive_all():
                if not self.handle_ingoing(ingoing):
                    return
            self.medium().wait_for_next_round()

    def handle_ingoing(self, ingoing: MessageStub):
        if isinstance(ingoing, File2ChunkReqMessage):
            key = (ingoing.filename, ingoing.chunkindex)
            chunk = self._metadata.get(key)
            if chunk is not None:

                for c in self.chunks_being_allocated:
                    if c[0] == chunk[0]:
                        self.chunks_being_allocated.append((chunk[0], ingoing.source))
                        return True
                        

                anwser = File2ChunkRspMessage(
                    self.index(),
                    ingoing.source,
                    chunk[0],
                    chunk[1]
                    )
                self.medium().send(anwser)
            else:
                if ingoing.createIfNotExists:
                    self.do_allocate_request(ingoing.filename, ingoing.chunkindex, ingoing.source)
                else:
                    anwser = File2ChunkRspMessage(
                        self.index(),
                        ingoing.source,
                        0,
                        []
                        )
                    self.medium().send(anwser)
        elif isinstance(ingoing, QuitMessage):
            print("I am Master " + str(self.index()) + " and I am quitting")
            return False
        elif isinstance(ingoing, AllocateChunkRspMessage):
            if not ingoing.result == "ok":
                print("allocation failed! I am quitting!!")
                return False
            for chunk in self._metadata.values():
                if chunk[0] == ingoing.chunkhandle:
                    self.add_chunk_to_metadata(chunk, ingoing.source)
        return True

    def add_chunk_to_metadata(self, chunk, chunkserver):
        chunk[1].append(chunkserver)
        if len(chunk[1]) == NUMBER_OF_REPLICAS:
            for request in self.chunks_being_allocated:
                if request[0] == chunk[0]:
                    anwser = File2ChunkRspMessage(
                        self.index(),
                        request[1],
                        chunk[0],
                        chunk[1]
                        )
                    self.medium().send(anwser)
    

    def do_allocate_request(self, filename, chunkindex, requester):
        chunkhandle = random.randint(0, 999999)
        self.chunks_being_allocated.append((chunkhandle, requester))
        self._metadata[(filename, chunkindex)] = (chunkhandle, [])

        chunkservers = []
        startnumber = random.randint(0, 9999)
        for i in range(NUMBER_OF_REPLICAS):
            numChunkServer = len(GfsNetwork.gfschunkserver)
            chosen = GfsNetwork.gfschunkserver[(startnumber + i ) % numChunkServer]
            chunkservers.append(chosen)

        for i in chunkservers:
            message = AllocateChunkReqMessage(self.index(), i, chunkhandle, chunkservers)
            self.medium().send(message)

    def print_result(self):
        pass


class GfsChunkserver(Device):
    def __init__(self, index: int, number_of_devices: int, medium: Medium):
        super().__init__(index, number_of_devices, medium)
        GfsNetwork.gfschunkserver.append(index)
        self.localchunks = {}
        # the first server in chunkservers is the primary
        self.chunkservers = {}

    def run(self):
        # since this is a server, its job is to answer for requests (messages), then do something
        while True:
            for ingoing in self.medium().receive_all():
                if not self.handle_ingoing(ingoing):
                    return
            self.medium().wait_for_next_round()

    def handle_ingoing(self, ingoing: MessageStub):
        if isinstance(ingoing, QuitMessage):
            print("I am Chunk Server " + str(self.index()) + " and I am quitting")
            return False
        elif isinstance(ingoing, AllocateChunkReqMessage):
            self.do_allocate_chunk(ingoing.chunkhandle, ingoing.chunkservers)
            message = AllocateChunkRspMessage(self.index(), ingoing.source, ingoing.chunkhandle, "ok")
            self.medium().send(message)
        elif isinstance(ingoing, RecordAppendReqMessage):
            #
            # TODO: need to implement the storate operation
            # do not forget the passive replication discipline
            #
            pass
        return True

    def do_allocate_chunk(self, chunkhandle, servers):
        self.localchunks[chunkhandle] = ""
        self.chunkservers[chunkhandle] = servers

    def print_result(self):
        print("chunk server quit. Currently, my saved chunks are as follows:")
        for c in self.localchunks:
            print("chunk " + str(c) + " : " + str(self.localchunks[c]))


class GfsClient(Device):
    def __init__(self, index: int, number_of_devices: int, medium: Medium):
        super().__init__(index, number_of_devices, medium)
        if index == 0:
            for i in range(5):
                pass

    def run(self):
        # being a client, it listens to incoming messags, but it also does something to put the ball rolling
        print("i am client " + str(self.index()))
        master = GfsNetwork.gfsmaster[0]
        message = File2ChunkReqMessage(self.index(), master, "myfile.txt", 0, True)
        self.medium().send(message)

        while True:
            for ingoing in self.medium().receive_all():
                if not self.handle_ingoing(ingoing):
                    return
            self.medium().wait_for_next_round()

    def handle_ingoing(self, ingoing: MessageStub):
        if isinstance(ingoing, File2ChunkRspMessage):
            print("I found out where my chunk is: " + str(ingoing.chunkhandle) + " locations: " + str(ingoing.locations))

            # I select a random chunk server, and I send the append request
            # I do not necessarily select the primary

            randomserver = ingoing.locations[random.randint(0,999)%len(ingoing.locations)]
            data = "hello from client number " + str(self.index()) + "\n"
            self.medium().send(RecordAppendReqMessage(self.index(), randomserver, ingoing.chunkhandle, data))
        elif isinstance(ingoing, RecordAppendRspMessage):
            # project completed, time to quit
            for i in GfsNetwork.gfsmaster:
                self.medium().send(QuitMessage(self.index(), i))
            for i in GfsNetwork.gfschunkserver:
                self.medium().send(QuitMessage(self.index(), i))

            return False
        return True

    def print_result(self):
        pass



class GfsNetwork:
    def __new__(cls, index: int, number_of_devices: int, medium: Medium):
        if index < NUMBER_OF_MASTERS:
            return GfsMaster(index, number_of_devices, medium)
        elif index < (NUMBER_OF_CHUNKSERVERS + NUMBER_OF_MASTERS):
            return GfsChunkserver(index, number_of_devices, medium)
        else:
            return GfsClient(index, number_of_devices, medium)
    gfsmaster = []
    gfschunkserver = []




class QuitMessage(MessageStub):
    def __init__(self, sender: int, destination: int):
        super().__init__(sender, destination)

    def __str__(self):
        return f'QUIT REQUEST {self.source} -> {self.destination}'



class File2ChunkReqMessage(MessageStub):
    def __init__(self, sender: int, destination: int, filename: str, chunkindex: int, createIfNotExists = False):
        super().__init__(sender, destination)
        self.filename = filename
        self.chunkindex = chunkindex
        self.createIfNotExists = createIfNotExists

    def __str__(self):
        return f'FILE2CHUNK REQUEST {self.source} -> {self.destination}: ({self.filename}, {self.chunkindex}, createIfNotExists = {self.createIfNotExists})'

class File2ChunkRspMessage(MessageStub):
    def __init__(self, sender: int, destination: int, chunkhandle: int, locations: list):
        super().__init__(sender, destination)
        self.chunkhandle = chunkhandle
        self.locations = locations

    def __str__(self):
        return f'FILE2CHUNK RESPONSE {self.source} -> {self.destination}: ({self.chunkhandle}, {self.locations})'


class AllocateChunkReqMessage(MessageStub):
    def __init__(self, sender: int, destination: int, chunkhandle: int, chunkservers: list):
        super().__init__(sender, destination)
        self.chunkhandle = chunkhandle
        self.chunkservers = chunkservers

    def __str__(self):
        return f'ALLOCATE REQUEST {self.source} -> {self.destination}: ({self.chunkhandle})'

class AllocateChunkRspMessage(MessageStub):
    def __init__(self, sender: int, destination: int, chunkhandle: int, result: str):
        super().__init__(sender, destination)
        self.chunkhandle = chunkhandle
        self.result = result

    def __str__(self):
        return f'ALLOCATE RESPONSE {self.source} -> {self.destination}: ({self.chunkhandle, self.result})'

class RecordAppendReqMessage(MessageStub):
    def __init__(self, sender: int, destination: int, chunkhandle: int, data: str):
        super().__init__(sender, destination)
        self.chunkhandle = chunkhandle
        self.data = data

    def __str__(self):
        return f'RECORD APPEND REQUEST {self.source} -> {self.destination}: ({self.chunkhandle}, {self.data})'

class RecordAppendRspMessage(MessageStub):
    def __init__(self, sender: int, destination: int, result: str):
        super().__init__(sender, destination)
        self.result = result
        # TODO: possibly, complete this message with the fields you need

    def __str__(self):
        return f'RECORD APPEND REQUEST {self.source} -> {self.destination}: ({self.result})'

