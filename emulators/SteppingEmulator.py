import copy
import random
import time
from emulators.AsyncEmulator import AsyncEmulator
from typing import Optional
from emulators.MessageStub import MessageStub


class SteppingEmulator(AsyncEmulator):
    def __init__(self, number_of_devices: int, kind): #default init, add stuff here to run when creating object
        super().__init__(number_of_devices, kind)
        self._stepping = True
    
    def dequeue(self, index: int) -> Optional[MessageStub]:
        #return super().dequeue(index) #uncomment to run as a normal async emulator (debug)
        self._progress.acquire()
        if index not in self._messages:
            self._progress.release()
            return None
        elif len(self._messages[index]) == 0:
            self._progress.release()
            return None
        else:
            # giving the user the ability to end stepping at any time
            if self._stepping:
                _input = input(f'Receive step?')
                if len(_input) > 0:
                    self._stepping = False
            m = self._messages[index].pop()
            print(f'\tRecieve {m}')
            self._progress.release()
            return m
    
    def queue(self, message: MessageStub):
        #return super().queue(message) #uncomment to run as normal queue (debug)
        self._progress.acquire()
        if self._stepping:
            _input = input("Send step?")
            if len(_input) > 0:
                self._stepping = False
        self._messages_sent += 1
        print(f'\tSend {message}')
        if message.destination not in self._messages:
            self._messages[message.destination] = []
        self._messages[message.destination].append(copy.deepcopy(message)) # avoid accidental memory sharing
        random.shuffle(self._messages[message.destination]) # shuffle to emulate changes in order
        time.sleep(random.uniform(0.01, 0.1)) # try to obfuscate delays and emulate network delays
        self._progress.release()
