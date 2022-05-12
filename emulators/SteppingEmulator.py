import copy
import random
import time
from emulators.AsyncEmulator import AsyncEmulator
from typing import Optional
from emulators.MessageStub import MessageStub
from pynput import keyboard
from getpass import getpass #getpass to hide input, cleaner terminal
from threading import Thread #run getpass in seperate thread


class SteppingEmulator(AsyncEmulator):
    def __init__(self, number_of_devices: int, kind): #default init, add stuff here to run when creating object
        super().__init__(number_of_devices, kind)
        self._stepper = Thread(target=lambda: getpass(""), daemon=True)
        self._stepper.start()
        self._stepping = True
        self._single = False
        self._list_messages_received:list[MessageStub] = list()
        self._list_messages_sent:list[MessageStub] = list()
        self._last_message:tuple[str, MessageStub] = ("init") #type(received or sent), message
        self._keyheld = False
        self.listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.listener.start()
        msg = """
        keyboard input:
            space:  Step a single time through messages
            f:      Fast-forward through messages
            enter:  Kill stepper daemon and run as an async emulator
        """
        print(msg)

    
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
            if self._stepping and self._stepper.is_alive(): #first expression for printing a reasonable amount, second to hide user input
                self._step("step?")
            m = self._messages[index].pop()
            print(f'\tRecieve {m}')
            self._list_messages_received.append(m)
            self._last_message = ("received", m)
            self._progress.release()
            return m
    
    def queue(self, message: MessageStub):
        #return super().queue(message) #uncomment to run as normal queue (debug)
        self._progress.acquire()
        if self._stepping and self._stepper.is_alive():
            self._step("step?")
        self._messages_sent += 1
        print(f'\tSend {message}')
        self._list_messages_sent.append(message)
        self._last_message = ("sent", message)
        if message.destination not in self._messages:
            self._messages[message.destination] = []
        self._messages[message.destination].append(copy.deepcopy(message)) # avoid accidental memory sharing
        random.shuffle(self._messages[message.destination]) # shuffle to emulate changes in order
        time.sleep(random.uniform(0.01, 0.1)) # try to obfuscate delays and emulate network delays
        self._progress.release()

    def _step(self, message:str = ""):
        if not self._single:
            print(f'\t{self._messages_sent}: {message}')
        while self._stepping: #run while waiting for input
            if self._single:  #break while if the desired action is a single message
                self._single = False
                break

    def on_press(self, key:keyboard.KeyCode):
        try:
            #for keycode class
            key = key.char
        except:
            #for key class
            key = key.name
        if key == "f" or key == "enter":
            self._stepping = False
        elif key == "space" and not self._keyheld:
            self._single = True
        self._keyheld = True

    def on_release(self, key:keyboard.KeyCode):
        try:
            #for key class
            key = key.char
        except:
            #for keycode class
            key = key.name
        if key == "f":
            self._stepping = True
        self._keyheld = False