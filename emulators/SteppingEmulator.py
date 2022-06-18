from typing import Optional
from emulators.AsyncEmulator import AsyncEmulator
from emulators.SyncEmulator import SyncEmulator
from emulators.MessageStub import MessageStub
from pynput import keyboard
from getpass import getpass #getpass to hide input, cleaner terminal
from threading import Thread #run getpass in seperate thread



class SteppingEmulator(SyncEmulator, AsyncEmulator):
    def __init__(self, number_of_devices: int, kind): #default init, add stuff here to run when creating object
        super().__init__(number_of_devices, kind)
        self._stepper = Thread(target=lambda: getpass(""), daemon=True)
        self._stepper.start()
        self._stepping = True
        self._single = False
        self._keyheld = False
        self._pick = False
        self.current_parent = SyncEmulator
        self.next_index = -1
        self.listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
        self.listener.start()
        msg = """
        keyboard input:
            space:              Step a single time through messages
            f:                  Fast-forward through messages
            enter:              Kill stepper daemon finish algorithm
            tab:                Show all messages currently waiting to be transmitted
            s:                  Pick the next message waiting to be transmitted to transmit next
            e:                  Toggle between sync and async emulation
        """
        print(msg)
    
    def dequeue(self, index: int) -> Optional[MessageStub]:
        result = self.current_parent.dequeue(self, index)
        self._progress.acquire()
        if result != None and self._stepping and self._stepper.is_alive():
            index = self._step(index=index)
        self._progress.release()
        return result
    
    def queue(self, message: MessageStub):
        self._progress.acquire()
        if self._stepping and self._stepper.is_alive():
            self._step()
        self._progress.release()
        
        return self.current_parent.queue(self, message)

    def _step(self, message:str = "Step?", index=-1):
        if not self._single:
            print(f'\t{self._messages_sent}: {message}')
        while self._stepping: #run while waiting for input
            if self._single:  #break while if the desired action is a single message
                self._single = False
                break
            elif self._pick:
                if index != -1:
                    self._pick = False
                    try:
                        print("Press return to proceed")
                        while self._stepper.is_alive():
                            pass
                        index = int(input("Specify index of the next element to send: "))
                    except:
                        print("Invalid element!")
                    if not self._stepper.is_alive():
                        self._stepper = Thread(target=lambda: getpass(""), daemon=True)
                        self._stepper.start()
                    self._stepping = True
                    print(message)
                self.next_index = index


    def _on_press(self, key:keyboard.KeyCode):
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
                    print(f'{index}: {message}')
                    index+=1
        elif key == "s":
            self._pick = True
        elif key == "e":
            if self.current_parent is AsyncEmulator:
                self.current_parent = SyncEmulator
            elif self.current_parent is SyncEmulator:
                self.current_parent = AsyncEmulator
            print(f'Changed emulator to {self.current_parent.__name__}')
        self._keyheld = True

    def _on_release(self, key:keyboard.KeyCode):
        try:
            #for key class
            key = key.char
        except:
            #for keycode class
            key = key.name
        if key == "f":
            self._stepping = True
        self._keyheld = False

    