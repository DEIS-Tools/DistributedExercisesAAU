if True:
    from emulators.AsyncEmulator import AsyncEmulator as Emulator
else:
    from emulators.SyncEmulator import SyncEmulator as Emulator
from typing import Optional
from emulators.MessageStub import MessageStub
from pynput import keyboard
from getpass import getpass #getpass to hide input, cleaner terminal
from threading import Thread #run getpass in seperate thread


class SteppingEmulator(Emulator):
    def __init__(self, number_of_devices: int, kind): #default init, add stuff here to run when creating object
        super().__init__(number_of_devices, kind)
        self._stepper = Thread(target=lambda: getpass(""), daemon=True)
        self._stepper.start()
        self._stepping = True
        self._single = False
        self._keyheld = False
        self.listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.listener.start()
        msg = """
        keyboard input:
            space:              Step a single time through messages
            f:                  Fast-forward through messages
            enter:              Kill stepper daemon and run as an async emulator
            tab:                Show all messages currently waiting to be transmitted
            s:                  Pick the next message waiting to be transmitted to transmit next
            e:                  Toggle between sync and async emulation
        """
        print(msg)
    
    def dequeue(self, index: int) -> Optional[MessageStub]:
        self._progress.acquire()
        if index in self._messages and not len(self._messages[index]) == 0 and self._stepping and self._stepper.is_alive():
            self._step("step?")
        self._progress.release()
        return super().dequeue(index)
    
    def queue(self, message: MessageStub):
        self._progress.acquire()
        if self._stepping and self._stepper.is_alive():
            self._step("step?")
        self._progress.release()
        return super().queue(message)

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
        elif key == "tab":
            print("Message queue:")
            index = 0
            for messages in self._messages.values():
                for message in messages:
                    index+=1
                    print(f'{index}: {message}')
        elif key == "s":
            try:
                print("press return to proceed")
                while self._stepper.is_alive():
                    pass
                _in = int(input("Specify index of which element to transmit next element to send next: "))
                index = 0
                for messages in self._messages.values():
                    for message in messages:
                        index+=1
                        if _in == index:
                            self.dequeue(message.destination)
            except:
                print("Invalid element")
            if not self._stepper.is_alive():
                self._stepper = Thread(target=lambda: getpass(""), daemon=True)
                self._stepper.start()
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
