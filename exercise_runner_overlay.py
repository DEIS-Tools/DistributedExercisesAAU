import tkinter as TK
from exercise_runner import run_exercise

def input_builder(master, title:str, entry_content:str):
    frame = TK.Frame(master)
    text = TK.Label(frame, text=title)
    entry = TK.Entry(frame)
    entry.insert(TK.END, entry_content)
    frame.pack(side=TK.LEFT)
    text.pack(side=TK.TOP)
    entry.pack(side=TK.BOTTOM)
    return frame, entry

def run():
    lecture = int(lecture_entry.get())
    algorithm = algorithm_entry.get()
    type = type_entry.get()
    devices = int(devices_entry.get())
    print("running exercise")
    print(f'with data: {lecture, algorithm, type, devices}')
    run_exercise(lecture, algorithm, type, devices)


master = TK.Tk()


input_area = TK.LabelFrame(text="Input")
input_area.pack(side=TK.BOTTOM)

lecture_frame,   lecture_entry   = input_builder(input_area, "Lecture",   0)
algorithm_frame, algorithm_entry = input_builder(input_area, "Algorithm", "PingPong")
type_frame,      type_entry      = input_builder(input_area, "Type",      "async")
devices_frame,   devices_entry   = input_builder(input_area, "Devices",   3)

start_button = TK.Button(master, text="Start", command=run)
start_button.pack(side=TK.TOP)

master.resizable(False,False)

master.mainloop()