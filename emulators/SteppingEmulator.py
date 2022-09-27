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
from os import name

if name == "posix":
    RESET = "\u001B[0m"
    CYAN = "\u001B[36m"
    GREEN = "\u001B[32m"
else:
    RESET = ""
    CYAN = ""
    GREEN = ""


class SteppingEmulator(SyncEmulator, AsyncEmulator):
    _single = False
    last_action = ""
    messages_received:list[MessageStub] = []
    messages_sent:list[MessageStub] = []
    keyheld = False
    pick_device = -1
    pick_running = False
    next_message = None
    log = None
    parent:EmulatorStub = AsyncEmulator

    def __init__(self, number_of_devices: int, kind): #default init, add stuff here to run when creating object
        super().__init__(number_of_devices, kind)
        #self._stepper = Thread(target=lambda: getpass(""), daemon=True)
        #self._stepper.start()
        self.barrier = Barrier(parties=number_of_devices)
        self.step_barrier = Barrier(parties=2)
        self.is_stepping = True
        self.input_lock = Lock()
        #self.listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
        #self.listener.start()
        self.shell = Thread(target=self.prompt, daemon=True)
        self.messages_received:list[MessageStub] = []
        self.messages_sent:list[MessageStub] = []
        msg = f"""
{CYAN}Shell input:{RESET}:
    {CYAN}step(press return){RESET}: Step a single time through messages
    {CYAN}exit{RESET}:               Finish the execution of the algorithm
    {CYAN}queue{RESET}:              Show all messages currently waiting to be transmitted
    {CYAN}queue <device #>{RESET}:   Show all messages currently waiting to be transmitted to a specific device
    {CYAN}pick{RESET}:               Pick the next message waiting to be transmitted to transmit next
    {CYAN}swap{RESET}:               Toggle between sync and async emulation
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
                print(f'\r\t{GREEN}Receive{RESET} {result}')
                
        else:
            result = self.parent.dequeue(self, index, True)

        self.pick_running = False

        if result != None:
            self.messages_received.append(result)
            self.last_action = "receive"
            if self.is_stepping:
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
            
        if self.is_stepping:
            self.step()
        self._progress.release()

    #the main function to stop execution
    def step(self):
        if self.is_stepping:
            self.step_barrier.wait()

    def pick(self):
        self.print_transit()
        if self.parent is AsyncEmulator:
            messages = self._messages
        else:
            messages = self._last_round_messages
        keys = []
        for key in messages.keys():
            if len(messages[key]) > 0:
                keys.append(key)
        print(f'{GREEN}Available devices:{RESET} {keys}')
        device = int(input(f'Specify device: '))
        self.print_transit_for_device(device)
        index = int(input(f'Specify index of the next message: '))
        self.pick_device = device
        self.next_message = messages[device][index]
        while not self.next_message == None:
            self.pick_running = True
            self.step_barrier.wait()
            while self.pick_running and not self.all_terminated():
                pass
            sleep(.1)

    
    def prompt(self):
        self.prompt_active = True
        line = ""
        while not line == "exit":
            sleep(1)
            line = input(f'\t[{CYAN}{len(self.messages_sent)} {RESET}->{CYAN} {len(self.messages_received)}{RESET}] > ')
            self.input_lock.acquire()
            args = line.split(" ")
            match args[0]:
                case "":
                    if not self.all_terminated():
                        self.step_barrier.wait()
                case "queue":
                    if len(args) == 1:
                        self.print_transit()
                    else:
                        self.print_transit_for_device(int(args[1]))
                case "exit":
                    self.is_stepping = False
                    self.step_barrier.wait()
                case "swap":
                    self.swap_emulator()
                case "pick":
                    try:
                        self.pick()
                    except ValueError:
                        pass
            self.input_lock.release()
        self.prompt_active = False

    def print_prompt(self):
        print(f'\t[{CYAN}{len(self.messages_sent)} {RESET}->{CYAN} {len(self.messages_received)}{RESET}] > ', end="", flush=True)


    #print all messages in transit
    def print_transit(self):
        print(f"{CYAN}Messages in transit:{RESET}")
        if self.parent is AsyncEmulator:
            for messages in self._messages.values():
                for message in messages:
                    print(f'\t{message}')
        elif self.parent is SyncEmulator:
            for messages in self._last_round_messages.values():
                for message in messages:
                    print(f'\t{message}')
    
    #print all messages in transit to specified device
    def print_transit_for_device(self, device):
        print(f'{CYAN}Messages in transit to device #{device}{RESET}')
        print(f'\t{CYAN}index{RESET}:     <message>')
        index = 0
        if self.parent is AsyncEmulator:
            if not device in self._messages.keys():
                return
            messages:list[MessageStub] = self._messages.get(device)
        elif self.parent is SyncEmulator:
            if not device in self._last_round_messages.keys():
                return
            messages:list[MessageStub] = self._last_round_messages.get(device)
        for message in messages:
            print(f'\t{CYAN}{index}{RESET}:         {message}')
            index+=1
    
    #swap between which parent class the program will run in between deliveries
    def swap_emulator(self):
        if self.parent is AsyncEmulator:
            self.parent = SyncEmulator
        elif self.parent is SyncEmulator:
            self.parent = AsyncEmulator
        print(f'Changed emulator to {GREEN}{self.parent.__name__}{RESET}')

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
                print(f'\r\t## {GREEN}ROUND {self._rounds}{RESET} ##')
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

    def print_statistics(self):
        return self.parent.print_statistics(self)

    def collectThread(self):
        #print("collecting a thread")
        self.pick_running = False
        self._progress.release()
        try:
            self.barrier.wait()
        except:
            pass
        