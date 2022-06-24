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
        self.parent = AsyncEmulator
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
        result = self.parent.dequeue(self, index)
        self._progress.acquire()
        if result != None and self._stepping and self._stepper.is_alive():
            self._step()
        self._progress.release()
        return result
    
    def queue(self, message: MessageStub):
        self._progress.acquire()
        if self._stepping and self._stepper.is_alive():
            self._step()
        self._progress.release()
        
        return self.parent.queue(self, message)

    def _step(self, message:str = "Step?"):
        if not self._single:
            print(f'\t{self._messages_sent}: {message}')
        while self._stepping: #run while waiting for input
            if self._single:  #break while if the desired action is a single message
                self._single = False
                break
            elif self._pick:
                self._pick = False
                try:
                    print("Press return to proceed")
                    while self._stepper.is_alive():
                        pass
                    self._print_transit()
                    keys = []
                    if self.parent is AsyncEmulator:
                        for key in self._messages.keys():
                            keys.append(key)
                    elif self.parent is SyncEmulator:
                        for key in self._last_round_messages.keys():
                            keys.append(key)
                    print(f'Available devices: {keys}')
                    device = int(input(f'Specify device to send to: '))
                    self._print_transit_for_device(device)
                    index = int(input(f'Specify index of the next element to send: '))
                    if self.parent is AsyncEmulator:
                        item = self._messages[device].pop(index)
                        self._messages[device].append(item)
                        
                        pass
                    elif self.parent is SyncEmulator:
                        pass
                except Exception as e:
                    print(e)
                if not self._stepper.is_alive():
                    self._stepper = Thread(target=lambda: getpass(""), daemon=True)
                    self._stepper.start()
                self._stepping = True
                print(message)


    def _on_press(self, key:keyboard.KeyCode | keyboard.Key):
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
            self._print_transit()
        elif key == "s":
            self._pick = True
        elif key == "e":
            self.swap_emulator()
        self._keyheld = True

    def _on_release(self, key:keyboard.KeyCode | keyboard.Key):
        try:
            #for key class
            key = key.char
        except:
            #for keycode class
            key = key.name
        if key == "f":
            self._stepping = True
        self._keyheld = False

    def _print_transit(self):
        print("Messages in transit:")
        if self.parent is AsyncEmulator:
            for messages in self._messages.values():
                for message in messages:
                    print(f'{message}')
        elif self.parent is SyncEmulator:
            for messages in self._last_round_messages.values():
                for message in messages:
                    print(f'{message}')
    
    def _print_transit_for_device(self, device):
        print(f'Messages in transit to device #{device}')
        index = 0
        if self.parent is AsyncEmulator:
            messages:list[MessageStub] = self._messages.get(device)
        elif self.parent is SyncEmulator:
            messages:list[MessageStub] = self._last_round_messages.get(device)
        for message in messages:
            print(f'{index}: {message}')
            index+=1
    
    def swap_emulator(self):
        if self.parent is AsyncEmulator:
            self.parent = SyncEmulator
        elif self.parent is SyncEmulator:
            self.parent = AsyncEmulator
        print(f'Changed emulator to {self.parent.__name__}')
    