import math
import random
import sys
import os
from enum import Enum

from emulators.Device import Device
from emulators.Medium import Medium
from emulators.MessageStub import MessageStub


class Role(Enum):
    # is the Worker a Mapper, a Reducer, or in Idle state?
    IDLE = 1
    MAPPER = 2
    REDUCER = 3


class MapReduceMaster(Device):
    def __init__(self, index: int, number_of_devices: int, medium: Medium):
        super().__init__(index, number_of_devices, medium)
        self.number_partitions: int = -1
        self.result_files: list[str] = []
        self.number_finished_reducers = 0

    def run(self):
        # since this is a server, its job is to answer for requests (messages), then do something
        while True:
            for ingoing in self.medium().receive_all():
                if not self.handle_ingoing(ingoing):
                    return
            self.medium().wait_for_next_round()

    def handle_ingoing(self, ingoing: MessageStub):
        if isinstance(ingoing, ClientJobStartMessage):
            # I assign ingoing.number_partitions workers as reducers, the rest as mappers
            # and I assign some files to each mapper
            self.number_partitions = ingoing.number_partitions
            number_of_mappers = self.number_of_devices() - self.number_partitions - 2
            for i in range(2, self.number_partitions + 2):
                message = ReduceTaskMessage(self.index(), i, i - 2, self.number_partitions, number_of_mappers) # the reducer needs to know how many mappers they are, to know when its task is completed
                self.medium().send(message)
            for i in range(0, number_of_mappers):
                length = len(ingoing.filenames)
                length = 5  # TODO: comment out this line to process all files, once you think your code is ready
                first = int(length * i / number_of_mappers)
                last = int(length * (i+1) / number_of_mappers)
                message = MapTaskMessage(self.index(), self.number_partitions + 2 + i, ingoing.filenames[first:last], self.number_partitions)
                self.medium().send(message)
        elif isinstance(ingoing, QuitMessage):
            # if the client is satisfied with the work done, I can tell all workers to quit, then I can quit
            for w in MapReduceNetwork.workers:
                self.medium().send(QuitMessage(self.index(), w))
            return False
        elif isinstance(ingoing, MappingDoneMessage):
            # TODO: contact all reducers, telling them that a mapper has completed its job
            #  hint: you need to define a new message type, for example ReducerVisitMapperMessage (see MapReduceWorker)
            pass
        elif isinstance(ingoing, ReducingDoneMessage):
            self.number_finished_reducers += 1
            self.result_files.append(ingoing.result_filename)
            if self.number_finished_reducers == self.number_partitions:
                # I can tell the client that the job is done
                message = ClientJobCompletedMessage(1, MapReduceNetwork.client_index, self.result_files)
                self.medium().send(message)
        return True

    def print_result(self):
        print(f"Master {self.index()} quits")


class MapReduceWorker(Device):
    def __init__(self, index: int, number_of_devices: int, medium: Medium):
        super().__init__(index, number_of_devices, medium)
        MapReduceNetwork.workers.append(index)
        self.role = Role.IDLE
        # number of partitions (equals to number of reducers)
        self.number_partitions = 0
        # variables if it is a mapper
        self.M_files_to_process: list[str] = []  # list of files to process
        self.M_cached_results: dict[str, int] = {}  # in-memory cache
        self.M_stored_results: dict[int, dict[str, int]] = {}  # "R" files containing results. partition -> word -> count
        # variables if it is a reducer
        self.R_my_partition = 0  # the partition I am managing
        self.R_number_mappers = 0  # how many mappers there are. I need to know it to decide when I can tell the master I am done with the reduce task

    def mapper_process_file(self, filename: str) -> dict[str, int]:
        # goal: return the occurrences of words in the file
        words = []
        with open("ex9data/books/"+filename) as file:
            for line in file:
                words += line.split()
        result = {}
        for word in words:
            result[word.lower()] = 1 + result.get(word.lower(), 0)
        return result

    def mapper_partition_function(self, key: str) -> int:
        # Compute the partition based on the key (see the lecture material)
        # This function should be supplied by the client, but we stick to a fixed function for sake of clarity
        char = ord(key[0])
        if char < ord('a'):
            char = ord('a')
        if char > ord('z'):
            char = ord('z')
        partition = (char - ord('a')) * self.number_partitions / (1+ord('z')-ord('a'))
        return int(partition)

    def mapper_shuffle(self):
        # goal: merge all the data I have in the cache to the stored results WITH SHUFFLE, then flush the cache
        for word in self.M_cached_results:
            p = self.mapper_partition_function(word)
            old_value = self.M_stored_results[p].get(word, 0)
            self.M_stored_results[p][word] = self.M_cached_results[word] + old_value
        self.M_cached_results = []  # flushing the cache

    def do_some_work(self):
        if self.role == Role.IDLE:
            return
        if self.role == Role.MAPPER:
            # if I am a mapper:
            #   I pop one filename from the list of files I have to process
            #   I process the file
            #   if I have no more files, I "store" it locally into partitions and tell the master that I am done
            if self.M_files_to_process != []:
                filename = self.M_files_to_process.pop()
                map_result = self.mapper_process_file(filename)
                for word in map_result:
                    self.M_cached_results[word] = self.M_cached_results.get(word, 0) + map_result[word]
                print(f"Mapper {self.index()}: file '{filename}' processed")
                if self.M_files_to_process == []:
                    self.mapper_shuffle()
                    message = MappingDoneMessage(self.index(), MapReduceNetwork.master_index)
                    self.medium().send(message)
        if self.role == Role.REDUCER:
            # not much to do: everything is done when the master tells us about a mapper that completed its task
            pass

    def run(self):
        # since this is a worker, it looks for incoming requests (messages), then it works a little
        while True:
            for ingoing in self.medium().receive_all():
                if not self.handle_ingoing(ingoing):
                    return
            self.do_some_work()
            self.medium().wait_for_next_round()

    def handle_ingoing(self, ingoing: MessageStub):
        if isinstance(ingoing, QuitMessage):
            print(f"I am Worker {self.index()} and I am quitting")
            return False
        elif isinstance(ingoing, MapTaskMessage):
            # I was assigned to be a mapper, thus I:
            #   save the files I have to visit
            #   I initialize the dict of dict for the "stored" results
            self.role = Role.MAPPER
            self.number_partitions = ingoing.number_partitions
            for i in range(self.number_partitions):
                self.M_stored_results[i] = {}
            self.M_files_to_process = ingoing.filenames
        elif isinstance(ingoing, ReduceTaskMessage):
            # I was assigned to be a reducer, thus I:
            #   save the partition number I will have to download from each mapper
            self.role = Role.REDUCER
            self.number_partitions = ingoing.number_partitions
            self.R_my_partition = ingoing.my_partition
            self.R_number_mappers = ingoing.number_mappers
            # nothing to do until the Master tells us to contact Mappers
        elif isinstance(ingoing, ReducerVisitMapperMessage):  # 'ReducerVisitMapperMessage' does not exist by default
            # the master is saying that a mapper is done
            # thus this reducer will:
            #   get the "stored" results from the mapper, for the correct partition (new message type)
            # if it is the last mapper I have to contact, I will:
            #   merge the data
            #   store resulting data in "ex9data/results/{my_partition_file_name}"
            #   tell the master I am done
            # TODO: write the code
            pass
        return True

    def print_result(self):
        print(f"Worker {self.index()} quits. It was a {self.role}")


class MapReduceClient(Device):
    def __init__(self, index: int, number_of_devices: int, medium: Medium):
        super().__init__(index, number_of_devices, medium)
        self.result_files: list[str] = []

    def scan_for_books(self):
        with os.scandir('ex9data/books/') as entries:
            return [entry.name for entry in entries
                    if entry.is_file() and entry.name.endswith(".txt")]

    def run(self):
        # being a client, it listens to incoming messages, but it also does something to put the ball rolling
        print(f"I am client {self.index()}")
        books = self.scan_for_books()

        message = ClientJobStartMessage(self.index(), MapReduceNetwork.master_index, books, 3)  # TODO: experiment with different number of reducers
        self.medium().send(message)

        while True:
            for ingoing in self.medium().receive_all():
                if not self.handle_ingoing(ingoing):
                    return
            self.medium().wait_for_next_round()

    def handle_ingoing(self, ingoing: MessageStub):
        if isinstance(ingoing, ClientJobCompletedMessage):
            # I can tell the master to quit
            # I will print the result later, with the print_result function
            self.medium().send(QuitMessage(self.index(), MapReduceNetwork.master_index))
            self.result_files = ingoing.result_files
            return False
        return True

    def print_result(self):
        for filename in self.result_files:
            print(f"Results from file: {filename}")
            with open(f"ex9data/results/{filename}") as file:
                for line in file:
                    print("\t" + line.rstrip())


class MapReduceNetwork:
    def __new__(cls, index: int, number_of_devices: int, medium: Medium):
        # client has index 0
        # master has index 1
        # workers have index 2+
        if index == MapReduceNetwork.client_index:
            return MapReduceClient(index, number_of_devices, medium)
        elif index == MapReduceNetwork.master_index:
            return MapReduceMaster(index, number_of_devices, medium)
        else:
            return MapReduceWorker(index, number_of_devices, medium)
    client_index = 0
    master_index = 1
    workers: list[int] = []


class QuitMessage(MessageStub):
    def __init__(self, sender: int, destination: int):
        super().__init__(sender, destination)

    def __str__(self):
        return f'QUIT REQUEST {self.source} -> {self.destination}'


class ClientJobStartMessage(MessageStub):
    def __init__(self, sender: int, destination: int, filenames: list, number_partitions: int):
        super().__init__(sender, destination)
        self.filenames = filenames
        self.number_partitions = number_partitions

    def __str__(self):
        return f'CLIENT START JOB REQUEST {self.source} -> {self.destination}: ({len(self.filenames)} files, {self.number_partitions} partitions)'


class ClientJobCompletedMessage(MessageStub):
    def __init__(self, sender: int, destination: int, result_files: list):
        super().__init__(sender, destination)
        self.result_files = result_files

    def __str__(self):
        return f'CLIENT JOB COMPLETED {self.source} -> {self.destination} ({self.result_files})'


class MapTaskMessage(MessageStub):
    def __init__(self, sender: int, destination: int, filenames: list, number_partitions: int):
        super().__init__(sender, destination)
        self.filenames = filenames
        self.number_partitions = number_partitions

    def __str__(self):
        return f'MAP TASK ASSIGNMENT {self.source} -> {self.destination}: ({len(self.filenames)} files, {self.number_partitions} partitions)'


class MappingDoneMessage(MessageStub):
    def __init__(self, sender: int, destination: int):
        super().__init__(sender, destination)

    def __str__(self):
        return f'MAP TASK COMPLETED {self.source} -> {self.destination}'


class ReduceTaskMessage(MessageStub):
    def __init__(self, sender: int, destination: int, my_partition: int, number_partitions: int, number_mappers: int):
        super().__init__(sender, destination)
        self.my_partition = my_partition
        self.number_partitions = number_partitions
        self.number_mappers = number_mappers

    def __str__(self):
        return f'REDUCE TASK ASSIGNMENT {self.source} -> {self.destination}: (partition is {self.my_partition}, {self.number_partitions} partitions, {self.number_mappers} mappers)'


class ReducingDoneMessage(MessageStub):
    def __init__(self, sender: int, destination: int, result_filename: str):
        super().__init__(sender, destination)
        self.result_filename = result_filename

    def __str__(self):
        return f'REDUCE TASK COMPLETED {self.source} -> {self.destination}: result_filename = {self.result_filename}'
