import copy
import random
from time import sleep
from typing import Optional
from emulators.AsyncEmulator import AsyncEmulator
from .EmulatorStub import EmulatorStub
from emulators.SyncEmulator import SyncEmulator
from emulators.MessageStub import MessageStub
from pynput import keyboard
from getpass import getpass #getpass to hide input, cleaner terminal
from threading import Barrier, Lock, Thread #run getpass in seperate thread

RESET = "\u001B[0m"
CYAN = "\u001B[36m"
GREEN = "\u001B[32m"


class SteppingEmulator(SyncEmulator, AsyncEmulator):
    _stepping = True
    _single = False
    last_action = ""
    messages_received:list[MessageStub] = []
    messages_sent:list[MessageStub] = []
    keyheld = False
    pick = False
    pick_device = -1
    pick_running = False
    next_message = None
    parent:EmulatorStub = AsyncEmulator

    def __init__(self, number_of_devices: int, kind): #default init, add stuff here to run when creating object
        super().__init__(number_of_devices, kind)
        self._stepper = Thread(target=lambda: getpass(""), daemon=True)
        self._stepper.start()
        self.barrier = Barrier(parties=number_of_devices)
        self.wait_lock = Lock()
        self.listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
        self.listener.start()
        msg = f"""
{CYAN}keyboard input{RESET}:
    {CYAN}shift{RESET}:              Step a single time through messages
    {CYAN}f{RESET}:                  Fast-forward through messages
    {CYAN}enter{RESET}:              Kill stepper daemon finish algorithm
    {CYAN}tab{RESET}:                Show all messages currently waiting to be transmitted
    {CYAN}s{RESET}:                  Pick the next message waiting to be transmitted to transmit next
    {CYAN}e{RESET}:                  Toggle between sync and async emulation
        """
        print(msg)
    
    def dequeue(self, index: int) -> Optional[MessageStub]:
        self._progress.acquire()
        #print(f'thread {index} is in dequeue')
        if not self.next_message == None:
            if not index == self.pick_device:
                self.collectThread()
                return self.dequeue(index)
            else:
                if self.parent == AsyncEmulator:
                    messages = self._messages
                else:
                    messages = self._last_round_messages
                result = messages[index].pop(messages[index].index(self.next_message))
                self.next_message = None
                self.pick_device = -1
                self.barrier.reset()
                print(f'\t{GREEN}Receive{RESET} {result}')
                
        else:
            result = self.parent.dequeue(self, index, True)

        self.pick_running = False

        if result != None:
            self.messages_received.append(result)
            self.last_action = "receive"
            if self._stepping and self._stepper.is_alive():
                self.step()

        self._progress.release()
        return result
    
    def queue(self, message: MessageStub):
        self._progress.acquire()
        #print(f'thread {message.source} is in queue')
        if not self.next_message == None and not message.source == self.pick_device:
            self.collectThread()
            return self.queue(message)

        self.parent.queue(self, message, True)
        self.last_action = "send"
        self.messages_sent.append(message)

        self.pick_running = False
            
        if self._stepping and self._stepper.is_alive():
            self.step()
        self._progress.release()

    #the main function to stop execution
    def step(self):
        if not self._single:
            print(f'\t{self._messages_sent}: Step?')
        while self._stepping: #run while waiting for input
            sleep(.1)
            if self._single:  #break while if the desired action is a single message
                self._single = False
                break
            elif self.pick:
                self.pick = False
                self.pick_function()

    #listen for pressed keys
    def _on_press(self, key:keyboard.KeyCode | keyboard.Key):
        try:
            #for keycode class
            key = key.char
        except:
            #for key class
            key = key.name
        if key == "f" or key == "enter":
            self._stepping = False
        elif key == "shift" and not self.keyheld:
            self._single = True
        elif key == "tab":
            self.print_transit()
        elif key == "s":
            self.pick = True
        elif key == "e":
            self.swap_emulator()
        self.keyheld = True

    #listen for released keys
    def _on_release(self, key:keyboard.KeyCode | keyboard.Key):
        try:
            #for key class
            key = key.char
        except:
            #for keycode class
            key = key.name
        if key == "f":
            self._stepping = True
        self.keyheld = False 

    #print all messages in transit
    def print_transit(self):
        print("Messages in transit:")
        if self.parent is AsyncEmulator:
            for messages in self._messages.values():
                for message in messages:
                    print(f'{message}')
        elif self.parent is SyncEmulator:
            for messages in self._last_round_messages.values():
                for message in messages:
                    print(f'{message}')
    
    #print all messages in transit to specified device
    def print_transit_for_device(self, device):
        print(f'Messages in transit to device #{device}')
        index = 0
        if self.parent is AsyncEmulator:
            messages:list[MessageStub] = self._messages.get(device)
        elif self.parent is SyncEmulator:
            messages:list[MessageStub] = self._last_round_messages.get(device)
        for message in messages:
            print(f'{index}: {message}')
            index+=1
    
    #swap between which parent class the program will run in between deliveries
    def swap_emulator(self):
        if self.parent is AsyncEmulator:
            self.parent = SyncEmulator
        elif self.parent is SyncEmulator:
            self.parent = AsyncEmulator
        print(f'Changed emulator to {self.parent.__name__}')
    
    #Pick command function, this lets the user alter the queue for a specific device
    def pick_function(self):
        try:
            print("Press return to proceed")                                                            #prompt the user to kill the stepper daemon
            while self._stepper.is_alive():                                                             #wait for the stepper to be killed
                pass
            self.print_transit()
            keys = []
            if self.parent is AsyncEmulator:
                for key in self._messages.keys():
                    keys.append(key)
            elif self.parent is SyncEmulator:
                for key in self._last_round_messages.keys():
                    keys.append(key)
            print(f'Available devices: {keys}')
            device = int(input(f'Specify device to send to: '))                                         #ask for user input to specify which device queue to alter
            self.print_transit_for_device(device)
            index = int(input(f'Specify index of the next element to send: '))                          #ask for user input to specify a message to send
            if self.parent is AsyncEmulator:
                self._messages[device].append(self._messages[device].pop(index))                        #pop index from input and append to the end of the list
            elif self.parent is SyncEmulator:
                self._last_round_messages[device].append(self._last_round_messages[device].pop(index))  #pop index from input and append to the end of the list
        except Exception as e:
            print(e)
        if not self._stepper.is_alive():
            self._stepper = Thread(target=lambda: getpass(""), daemon=True)                             #restart stepper daemon
            self._stepper.start()
        self._stepping = True
        print(f'\t{self._messages_sent}: Step?')

    def run(self):
        self._progress.acquire()
        for index in self.ids():
            self._awaits[index].acquire()
        self._start_threads()
        self._progress.release()

        self._round_lock.acquire()
        while True:
            if self.parent is AsyncEmulator:
                sleep(.1)
                self._progress.acquire()
                # check if everyone terminated
                if self.all_terminated():
                    break
                self._progress.release()
            else:
                self._round_lock.acquire()
                # check if everyone terminated
                self._progress.acquire()
                print(f'## {GREEN}ROUND {self._rounds}{RESET} ##')
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
                ids = [x for x in self.ids()] # convert to list to make it shuffleable
                random.shuffle(ids)
                for index in ids:
                    if self._awaits[index].locked():
                        self._awaits[index].release()
                self._progress.release()
                
        for t in self._threads:
            t.join()

    def done(self, id):
        return self.parent.done(self, id)

    def _run_thread(self, index: int):
        super()._run_thread(index)
        self._devices[index]._finished = True



    def collectThread(self):
        #print("collecting a thread")
        self.pick_running = False
        self._progress.release()
        try:
            self.barrier.wait()
        except:
            pass
        