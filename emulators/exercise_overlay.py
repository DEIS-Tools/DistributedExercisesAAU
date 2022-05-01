from math import sin, cos, pi
from random import randint
import tkinter as  TK
import tkinter.ttk as TTK
from os import name

from emulators.SteppingEmulator import SteppingEmulator
from emulators.table import table

def overlay(emulator:SteppingEmulator, run_function):
    # top is planned to be reserved for a little description of controls in stepper
    master = TK.Tk()
    height = 500
    width = 500
    spacing = 10

    
    def show_all_data():
        window = TK.Toplevel(master)
        content:list[list] = []
        messages = emulator._list_messages_sent
        header = TK.Frame(window)
        header.pack(side=TK.TOP)
        TK.Label(header, text="Source | ").pack(side=TK.LEFT)
        TK.Label(header, text="Destination | ").pack(side=TK.LEFT)
        TK.Label(header, text="Message | ").pack(side=TK.LEFT)
        TK.Label(header, text="Sequence number").pack(side=TK.LEFT)

        content = [[messages[i].source, messages[i].destination, messages[i], i] for i in range(len(messages))]
        

        tab = table(window, content, width=15, scrollable="y")
        tab.pack(side=TK.BOTTOM)

    def show_data(device_id):
        def _show_data():
            if len(emulator._list_messages_received) > 0:
                window = TK.Toplevel(master)
                window.title(f'Device {device_id}')
                received_frame = TK.LabelFrame(window, text="Received")
                received_frame.pack(side=TK.LEFT)
                for data in emulator._list_messages_received:
                    if data.destination == device_id:
                        TTK.Label(received_frame, text=data).pack(side=TK.TOP)
                sent_frame = TK.LabelFrame(window, text="Sent")
                sent_frame.pack(side=TK.LEFT)
                for data in emulator._list_messages_sent:
                    if data.source == device_id:
                        TTK.Label(sent_frame, text=data).pack(side=TK.TOP)
            else:
                return
        return _show_data

    def get_coordinates_from_index(center:tuple[int,int], r:int, i:int, n:int) -> tuple[int, int]:
        x = sin((i*2*pi)/n)
        y = cos((i*2*pi)/n)
        if x < pi:
            return int(center[0]-(r*x)), int(center[1]-(r*y))
        else:
            return int(center[0]-(r*-x)), int(center[1]-(r*y))

    def build_device(master:TK.Canvas, device_id, x, y, device_size):
        circle = canvas.create_oval(x, y, x+device_size, y+device_size, outline="black")
        frame = TTK.Frame(master)
        frame.place(x=x+(device_size/5), y=y+(device_size/5))
        button = TTK.Button(frame, command=show_data(device_id), text="Show data")
        button.pack(side=TK.BOTTOM)
        text = TTK.Label(frame, text=f'Device #{device_id}')
        text.pack(side=TK.BOTTOM)
            

    def step():
        #insert stepper function
        emulator._single = True

    def end():
        emulator._stepping = False

    canvas = TK.Canvas(master, height=height, width=width)
    canvas.pack(side=TK.TOP)
    device_size = 100

    for device in range(len(emulator._devices)):
        x,y = get_coordinates_from_index((int((width/2)-(device_size/2)), int((width/2)-(device_size/2))), (int((width/2)-(device_size/2)))-spacing, device, len(emulator._devices))
        build_device(canvas, device, x, y, device_size)
    bottom_frame = TK.LabelFrame(master, text="Inputs")
    bottom_frame.pack(side=TK.TOP)
    TTK.Button(bottom_frame, text="Step", command=step).pack(side=TK.LEFT)
    TTK.Button(bottom_frame, text="End", command=end).pack(side=TK.LEFT)
    TTK.Button(bottom_frame, text="Restart algorithm", command=run_function).pack(side=TK.LEFT)
    TTK.Button(bottom_frame, text="show all data", command=show_all_data).pack(side=TK.LEFT)
    master.resizable(False,False)
    master.title("Stepping algorithm")