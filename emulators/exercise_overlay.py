from copy import copy
from random import randint
import tkinter as  TK
import tkinter.ttk as TTK
from os import name

from emulators.SteppingEmulator import SteppingEmulator


def overlay(emulator:SteppingEmulator, run_function):
    # top is planned to be reserved for a little description of controls in stepper
    # if stepper is not chosen, this will not be displayed
    master = TK.Tk()
    height = 500
    width = 1000

    def show_all_data():
        window = TK.Toplevel(master)
        window.title("All data")
        window.resizable(False, False)
        frames = list()
        for device in emulator._devices:
            dev_frame = TK.LabelFrame(window, text=f'Device {emulator._devices.index(device)}')
            dev_frame.pack(side=TK.LEFT)
            frames.append(dev_frame)
            dev_name = TTK.Label(dev_frame, text=f'Device id: {device._id}')
            dev_name.pack(side=TK.TOP)
        for data in emulator._list_messages_received:
            device_id = data._destination
            data_label = TTK.Label(frames[device_id], text=data)
            data_label.pack(side=TK.BOTTOM)

    def show_data(device_id):
        def _window():
            window = TK.Toplevel(master, width=width/5, height=height/5)
            window.title(f'Device {device_id}')
            received_frame = TK.LabelFrame(window, text="Received")
            received_frame.pack(side=TK.LEFT)
            for data in emulator._list_messages_received:
                if data._destination == device_id:
                    TTK.Label(received_frame, text=data).pack(side=TK.TOP)
            sent_frame = TK.LabelFrame(window, text="Sent")
            sent_frame.pack(side=TK.LEFT)
            for data in emulator._list_messages_sent:
                if data._source == device_id:
                    TTK.Label(sent_frame, text=data).pack(side=TK.TOP)
        return _window

            

    def step():
        #insert stepper function
        emulator._single = True

    def end():
        emulator._stepping = False

    canvas = TK.Canvas(master, height=height, width=width)
    canvas.pack(side=TK.TOP)
    if name == "posix":
        device_size = 150
    else:
        device_size = 100

    for device in range(len(emulator._devices)):
        x = randint(device_size, width-device_size)
        y = randint(device_size, height-device_size)
        canvas.create_oval(x, y, x+device_size, y+device_size, outline="black")
        device_frame = TTK.Frame(canvas)
        device_frame.place(x=x+(device_size/5), y=y+(device_size/5))
        device_button = TTK.Button(device_frame, text="Show data", command=show_data(device))
        device_button.pack(side=TK.BOTTOM)
        device_text = TTK.Label(device_frame, text=f'Device #{device}')
        device_text.pack(side=TK.BOTTOM)
    bottom_frame = TK.LabelFrame(master, text="Inputs")
    bottom_frame.pack(side=TK.TOP)
    step_button = TTK.Button(bottom_frame, text="Step", command=step)
    step_button.pack(side=TK.LEFT)
    end_button = TTK.Button(bottom_frame, text="End", command=end)
    end_button.pack(side=TK.LEFT)
    start_new_button = TK.Button(bottom_frame, text="Restart algorithm", command=run_function)
    start_new_button.pack(side=TK.LEFT)
    show_all_data_button = TK.Button(bottom_frame, text="show all data", command=show_all_data)
    show_all_data_button.pack(side=TK.LEFT)
    master.resizable(False,False)
    master.title("Stepping algorithm")