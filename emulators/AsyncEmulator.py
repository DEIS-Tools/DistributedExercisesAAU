import copy
import random
import threading
import time
from threading import Lock
from typing import Optional

from emulators.EmulatorStub import EmulatorStub
from emulators.MessageStub import MessageStub


class AsyncEmulator(EmulatorStub):

    def __init__(self, number_of_devices: int, kind):
        super().__init__(number_of_devices, kind)
        self._terminated = 0
        self._messages = {}
        self._messages_sent = 0

    def run(self):
        self._progress.acquire()
        self._start_threads()
        self._progress.release()

        # make sure the round_lock is locked initially
        while True:
            time.sleep(0.1)
            self._progress.acquire()
            # check if everyone terminated
            if self.all_terminated():
                break
            self._progress.release()
        for t in self._threads:
            t.join()
        return

    def queue(self, message: MessageStub):
        self._progress.acquire()
        self._messages_sent += 1
        print(f'\tSend {message}')
        if message.destination not in self._messages:
            self._messages[message.destination] = []
        self._messages[message.destination].append(copy.deepcopy(message)) # avoid accidental memory sharing
        random.shuffle(self._messages[message.destination]) # shuffle to emulate changes in order
        time.sleep(random.uniform(0.01, 0.1)) # try to obfuscate delays and emulate network delays
        self._progress.release()

    def dequeue(self, index: int) -> Optional[MessageStub]:
        self._progress.acquire()
        if index not in self._messages:
            self._progress.release()
            return None
        elif len(self._messages[index]) == 0:
            self._progress.release()
            return None
        else:
            m = self._messages[index].pop()
            print(f'\tRecieve {m}')
            self._progress.release()
            return m

    def done(self, index: int):
        time.sleep(random.uniform(0.01, 0.1)) # try to obfuscate delays and emulate network delays
        return


    def print_statistics(self):
        print(f'\tTotal {self._messages_sent} messages')
        print(f'\tAverage {self._messages_sent/len(self._devices)} messages/device')

    def terminated(self, index:int):
        self._progress.acquire()
        self._terminated += 1
        self._progress.release()