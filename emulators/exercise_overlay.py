from random import randint
import tkinter as  TK

def overlay(devices:int = 3):
    # top is planned to be reserved for a little description of controls in stepper
    # if stepper is not chosen, this will not be displayed
    master = TK.Tk()
    canvas = TK.Canvas(master, height=1000, width=1000)
    canvas.pack(side=TK.TOP)
    for device in range(devices):
        x = randint(100, 900)
        y = randint(100, 900)
        device_size = 100
        canvas.create_oval(x, y, x+device_size, y+device_size, outline="black")
        device_frame = TK.Frame(canvas)
        device_frame.place(x=x+(device_size/4), y=y+(device_size/4))
        device_button = TK.Button(device_frame, text="Show data")
        device_button.pack(side=TK.BOTTOM)
        device_text = TK.Label(device_frame, text=f'Device #{device}')
        device_text.pack(side=TK.BOTTOM)
    bottom_text = TK.Label(master, text="last message")
    bottom_text.pack(side=TK.TOP)
    master.resizable(False,False)
    master.mainloop()

overlay()