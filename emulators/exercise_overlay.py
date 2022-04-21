from random import randint
import tkinter as  TK

from platformdirs import os

from emulators.EmulatorStub import EmulatorStub

def overlay(emulator:EmulatorStub):
    # top is planned to be reserved for a little description of controls in stepper
    # if stepper is not chosen, this will not be displayed
    master = TK.Tk()
    height = 500
    width = 1000

    def show_info():
        window = TK.Toplevel(master)
        window.resizable(False, False)
        data = TK.Label(window, text="___placeholder___")
        data.pack(side=TK.TOP)
        for device in emulator._devices:
            pass

    def step():
        #insert stepper function
        emulator._single = True

    def end():
        emulator._stepping = False

    canvas = TK.Canvas(master, height=height, width=width)
    canvas.pack(side=TK.TOP)
    for device in range(len(emulator._devices)):
        if os.name == 'posix':
            device_size=150
        else:
            device_size = 100
        x = randint(device_size, width-device_size)
        y = randint(device_size, height-device_size)
        canvas.create_oval(x, y, x+device_size, y+device_size, outline="black")
        device_frame = TK.Frame(canvas)
        device_frame.place(x=x+(device_size/5), y=y+(device_size/5))
        device_button = TK.Button(device_frame, text="Show data", command=show_info)
        device_button.pack(side=TK.BOTTOM)
        device_text = TK.Label(device_frame, text=f'Device #{device}')
        device_text.pack(side=TK.BOTTOM)
    bottom_frame = TK.LabelFrame(master, text="Inputs")
    bottom_frame.pack(side=TK.TOP)
    step_button = TK.Button(bottom_frame, text="Step", command=step)
    step_button.pack(side=TK.LEFT)
    end_button = TK.Button(bottom_frame, text="End", command=end)
    end_button.pack(side=TK.LEFT)
    master.resizable(False,False)
    master.mainloop()
