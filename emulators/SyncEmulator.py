import copy
import random
import sys
import threading
import time
from typing import Optional

from emulators.EmulatorStub import EmulatorStub
from emulators.MessageStub import MessageStub


class SyncEmulator(EmulatorStub):

    def __init__(self, number_of_devices: int, kind):
        super().__init__(number_of_devices, kind)
        self._round_lock = threading.Lock()
        self._done = [False for _ in self.ids()]
        self._awaits = [threading.Lock() for _ in self.ids()]
        self._last_round_messages = {}
        self._current_round_messages = {}
        self._messages_sent = 0
        self._rounds = 0
        self._time_started = time.perf_counter_ns()
        self._data_space = 0  # data usage in bytes
        self.s_ns = 1e9  # seconds to nanoseconds

    def reset_done(self):
        self._done = [False for _ in self.ids()]

    def run(self):
        self._progress.acquire()
        for index in self.ids():
            self._awaits[index].acquire()
        self._start_threads()
        self._progress.release()

        # make sure the round_lock is locked initially
        self._round_lock.acquire()
        while True:
            self._round_lock.acquire()
            # check if everyone terminated
            self._progress.acquire()
            print(f'## ROUND {self._rounds} ##')
            if self.all_terminated():
                self._progress.release()
                break
            # send messages
            for index in self.ids():
                # intentionally change the order
                if index in self._current_round_messages:
                    nxt = copy.deepcopy(self._current_round_messages[index])
                    random.shuffle(nxt)
                    if index in self._last_round_messages:
                        self._last_round_messages[index] += nxt
                    else:
                        self._last_round_messages[index] = nxt
            self._current_round_messages = {}
            self.reset_done()
            self._rounds += 1
            ids = [x for x in self.ids()]  # convert to list to make it shuffleable
            random.shuffle(ids)
            for index in ids:
                if self._awaits[index].locked():
                    self._awaits[index].release()
            self._progress.release()
        for t in self._threads:
            t.join()
        return

    def queue(self, message: MessageStub):
        self._progress.acquire()
        self._messages_sent += 1
        print(f'\tSend {message}')
        if message.destination not in self._current_round_messages:
            self._current_round_messages[message.destination] = []
        self._current_round_messages[message.destination].append(
            copy.deepcopy(message))  # avoid accidental memory sharing
        self._progress.release()

    def dequeue(self, index: int) -> Optional[MessageStub]:
        self._progress.acquire()
        if index not in self._last_round_messages:
            self._progress.release()
            return None
        elif len(self._last_round_messages[index]) == 0:
            self._progress.release()
            return None
        else:
            m = self._last_round_messages[index].pop()
            print(f'\tReceive {m}')
            self._progress.release()
            self._data_space += _get_real_size(m)
            return m

    def done(self, index: int):
        self._progress.acquire()
        if self._done[index]:
            # marked as done twice!
            self._progress.release()
            raise RuntimeError(f'Device {index} called wait_for_next_round() twice in the same round!')
        self._done[index] = True

        # check if the thread have marked their round as done OR have ended
        if all([self._done[x] or not self._threads[x].is_alive() for x in self.ids()]):
            self._round_lock.release()
        self._progress.release()
        self._awaits[index].acquire()

    def print_statistics(self):
        print(f'\tTotal {self._messages_sent} messages')
        print(f'\tAverage {self._messages_sent / len(self._devices)} messages/device')
        print(f'\tTotal {self._rounds} rounds')
        print(f'\tFull time elapsed: {round((time.perf_counter_ns() - self._time_started) / self.s_ns, 4)} seconds')
        print(f'\tData transferred: {self._data_space} bytes')

    def terminated(self, index: int):
        self._progress.acquire()
        self._done[index] = True
        if all([self._done[x] or not self._threads[x].is_alive()
                for x in self.ids()]):
            if self._round_lock.locked():
                self._round_lock.release()
        self._progress.release()


def _get_real_size(obj, seen=None):
    """
    python offers no built-in to fully measure the size of an object, this function will achieve that
    """
    size = sys.getsizeof(obj)
    if seen is None:
        seen = set()
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    # Important mark as seen *before* entering recursion to gracefully handle
    # self-referential objects
    seen.add(obj_id)
    if isinstance(obj, dict):
        size += sum([_get_real_size(v, seen) for v in obj.values()])
        size += sum([_get_real_size(k, seen) for k in obj.keys()])
    elif hasattr(obj, '__dict__'):
        size += _get_real_size(obj.__dict__, seen)
    elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
        size += sum([_get_real_size(i, seen) for i in obj])
    return size
