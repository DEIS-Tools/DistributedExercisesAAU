from math import sin, cos, pi
from threading import Thread
import tkinter as  TK
import tkinter.ttk as TTK
from emulators.AsyncEmulator import AsyncEmulator
from emulators.MessageStub import MessageStub

from emulators.SteppingEmulator import SteppingEmulator
from emulators.SyncEmulator import SyncEmulator
from emulators.table import table

def overlay(emulator:SteppingEmulator, run_function):
    #master config
    master = TK.Toplevel()
    master.resizable(False,False)
    master.title("Stepping algorithm")
    pages = TTK.Notebook(master)
    main_page = TTK.Frame(pages)
    controls_page = TTK.Frame(pages)
    pages.add(main_page, text="Emulator")
    pages.add(controls_page, text="Controls")
    pages.pack(expand= 1, fill=TK.BOTH)
    height = 500
    width = 500
    spacing = 10
    #end of master config

    
    def show_all_data():
        window = TK.Toplevel()
        content:list[list] = []
        messages = emulator._list_messages_sent
        message_content = list()
        for message in messages:
            temp = str(message)
            temp = temp.replace(f'{message.source} -> {message.destination} : ', "")
            temp = temp.replace(f'{message.source}->{message.destination} : ', "")
            message_content.append(temp)

        content = [[messages[i].source, messages[i].destination, message_content[i], i] for i in range(len(messages))]
        

        tab = table(window, content, width=15, scrollable="y", title="All messages")
        tab.pack(side=TK.BOTTOM)

        header = TK.Frame(window)
        header.pack(side=TK.TOP, anchor=TK.NW)
        TK.Label(header, text="Source", width=tab.column_width[0]).pack(side=TK.LEFT)
        TK.Label(header, text="Destination", width=tab.column_width[1]).pack(side=TK.LEFT)
        TK.Label(header, text="Message", width=tab.column_width[2]).pack(side=TK.LEFT)
        TK.Label(header, text="Sequence number", width=tab.column_width[3]).pack(side=TK.LEFT)

    def show_data(device_id):
        def _show_data():
            if len(emulator._list_messages_received) > 0:
                window = TK.Toplevel(main_page)
                window.title(f'Device {device_id}')
                received:list[MessageStub] = list()
                sent:list[MessageStub] = list()
                for message in emulator._list_messages_received:
                    if message.destination == device_id:
                        received.append(message)
                    if message.source == device_id:
                        sent.append(message)
                if len(received) > len(sent):
                    for _ in range(len(received)-len(sent)):
                        sent.append("")
                elif len(sent) > len(received):
                    for _ in range(len(sent) - len(received)):
                        received.append("")
                content = list()
                for i in range(len(received)):
                    if received[i] == "":
                        msg = str(sent[i]).replace(f'{sent[i].source} -> {sent[i].destination} : ', "").replace(f'{sent[i].source}->{sent[i].destination} : ', "")
                        content.append(["", received[i], sent[i].destination, msg])
                    elif sent[i] == "":
                        msg = str(received[i]).replace(f'{received[i].source} -> {received[i].destination} : ', "").replace(f'{received[i].source}->{received[i].destination} : ', "")
                        content.append([received[i].source, msg, "", sent[i]])
                    else:
                        sent_msg = str(sent[i]).replace(f'{sent[i].source} -> {sent[i].destination} : ', "").replace(f'{sent[i].source}->{sent[i].destination} : ', "")
                        received_msg = str(received[i]).replace(f'{received[i].source} -> {received[i].destination} : ', "").replace(f'{received[i].source}->{received[i].destination} : ', "")
                        content.append([received[i].source, received_msg, sent[i].destination, sent_msg])

                tab = table(window, content, width=15, scrollable="y", title=f'Device {device_id}')
                tab.pack(side=TK.BOTTOM)

                header = TK.Frame(window)
                header.pack(side=TK.TOP, anchor=TK.NW)
                TK.Label(header, text="Source", width=tab.column_width[0]).pack(side=TK.LEFT)
                TK.Label(header, text="Message", width=tab.column_width[1]).pack(side=TK.LEFT)
                TK.Label(header, text="Destination", width=tab.column_width[2]).pack(side=TK.LEFT)
                TK.Label(header, text="Message", width=tab.column_width[3]).pack(side=TK.LEFT)
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

    def build_device(main_page:TK.Canvas, device_id, x, y, device_size):
        canvas.create_oval(x, y, x+device_size, y+device_size, outline="black", fill="gray")
        frame = TTK.Frame(main_page)
        frame.place(x=x+(device_size/8), y=y+(device_size/4))
        TTK.Label(frame, text=f'Device #{device_id}').pack(side=TK.TOP)
        TTK.Button(frame, command=show_data(device_id), text="Show data").pack(side=TK.TOP)
        data_frame = TTK.Frame(frame)
        data_frame.pack(side=TK.BOTTOM)

            

    def stop_emulator():
        emulator.listener.stop()
        emulator.listener.join()
        bottom_label.config(text="Finished running", fg="green")

    def step():
        #insert stepper function
        emulator._single = True
        if emulator.all_terminated():
            bottom_label.config(text="Finished running, kill keyboard listener?... (press any key)")
            Thread(target=stop_emulator).start()
            
        elif emulator._last_message != tuple():
            message = emulator._last_message[1]
            canvas.delete("line")
            canvas.create_line(coordinates[message.source][0]+(device_size/2), coordinates[message.source][1]+(device_size/2), coordinates[message.destination][0]+(device_size/2), coordinates[message.destination][1]+(device_size/2), tags="line")
            msg = str(message)
            msg = msg.replace(f'{message.source} -> {message.destination} : ', "")
            msg = msg.replace(f'{message.source}->{message.destination} : ', "")
            if emulator._last_message[0] == "sent":
                bottom_label.config(text=f'Device {message.source} sent "{msg}" to {message.destination}')
            elif emulator._last_message[0] == "received":
                bottom_label.config(text=f'Device {message.destination} received {msg} from {message.source}')
    def end():
        emulator._stepping = False
        while not emulator.all_terminated():
            pass
        bottom_label.config(text="Finished running, kill keyboard listener?... (press any key)")
        Thread(target=stop_emulator).start()
    
    #Emulator page stuff
    canvas = TK.Canvas(main_page, height=height, width=width)
    canvas.pack(side=TK.TOP)
    device_size = 100
    canvas.create_line(0,0,0,0, tags="line") #create dummy lines
    coordinates:list[tuple[TTK.Label]] = list()
    for device in range(len(emulator._devices)):
        x, y = get_coordinates_from_index((int((width/2)-(device_size/2)), int((width/2)-(device_size/2))), (int((width/2)-(device_size/2)))-spacing, device, len(emulator._devices))
        build_device(canvas, device, x, y, device_size)
        coordinates.append((x,y))

    def swap_emulator(button:TTK.Button):
        emulator.swap_emulator()
        button.configure(text=emulator.parent.__name__)

    def show_queue():
        window = TK.Toplevel(main_page)
        content = [["Source", "Destination", "Message"]]
        if emulator.parent is AsyncEmulator:
            queue = emulator._messages.values()
        else:
            queue = emulator._last_round_messages.values()
        for messages in queue:
            for message in messages:
                message_stripped = str(message).replace(f'{message.source} -> {message.destination} : ', "").replace(f'{message.source}->{message.destination} : ', "")
                content.append([message.source, message.destination, message_stripped])
        tab = table(window, content, width=15, scrollable="y", title="Message queue")
        tab.pack(side=TK.LEFT)

    def pick_gui():
        def execute():
            device = int(device_entry.get())
            index = int(message_entry.get())
            if emulator.parent is AsyncEmulator:
                emulator._messages[device].append(emulator._messages[device].pop(index))
            elif emulator.parent is SyncEmulator:
                emulator._last_round_messages[device].append(emulator._last_round_messages[device].pop(index))
            window.destroy()

        emulator.print_transit()
        keys = []
        if emulator.parent is AsyncEmulator:
            messages = emulator._messages
        else:
            messages = emulator._last_round_messages
        for item in messages.items():
            keys.append(item[0])
        keys.sort()
        window = TK.Toplevel(main_page)
        header = TTK.Frame(window)
        header.pack(side=TK.TOP)
        TTK.Label(header, text=f'Pick a message to be transmitted next').pack(side=TK.LEFT)
        max_size = 0
        for m in messages.values():
            if len(m) > max_size:
                max_size = len(m)
        content = [[messages[key][i] if len(messages[key]) > i else " " for key in keys] for i in range(max_size)]
        head = [f'Device {key}' for key in keys]
        content.insert(0, head)
        content[0].insert(0, "Message #")
        for i in range(max_size):
            content[i+1].insert(0, i)
        tab = table(window, content, width=15, scrollable="y", title="Pick a message to be transmitted next")
        tab.pack(side=TK.TOP)
        footer = TTK.Frame(window)
        footer.pack(side=TK.BOTTOM)
        device_frame = TTK.Frame(footer)
        device_frame.pack(side=TK.TOP)
        TTK.Button(footer, text="Confirm", command=execute).pack(side=TK.BOTTOM)
        message_frame = TTK.Frame(footer)
        message_frame.pack(side=TK.BOTTOM)
        TTK.Label(device_frame, text="Device: ").pack(side=TK.LEFT)
        device_entry = TTK.Entry(device_frame)
        device_entry.pack(side=TK.RIGHT)
        TTK.Label(message_frame, text="Message: ").pack(side=TK.LEFT)
        message_entry = TTK.Entry(message_frame)
        message_entry.pack(side=TK.RIGHT)

    bottom_frame = TK.LabelFrame(main_page, text="Inputs")
    bottom_frame.pack(side=TK.BOTTOM)
    TTK.Button(bottom_frame, text="Step", command=step).pack(side=TK.LEFT)
    TTK.Button(bottom_frame, text="End", command=end).pack(side=TK.LEFT)
    emulator_button = TTK.Button(bottom_frame, text=emulator.parent.__name__, command=lambda: swap_emulator(emulator_button))
    emulator_button.pack(side=TK.LEFT)
    TTK.Button(bottom_frame, text="Message queue", command=show_queue).pack(side=TK.LEFT)
    TTK.Button(bottom_frame, text="Pick", command=pick_gui).pack(side=TK.LEFT)
    TTK.Button(bottom_frame, text="Restart algorithm", command=run_function).pack(side=TK.LEFT)
    TTK.Button(bottom_frame, text="Delivered messages", command=show_all_data).pack(side=TK.LEFT)
    bottom_label = TK.Label(main_page, text="Status")
    bottom_label.pack(side=TK.BOTTOM)

    #controls page stuff

    TTK.Label(controls_page, text="Controls", font=("Arial", 25)).pack(side=TK.TOP)
    controls_frame = TTK.Frame(controls_page)
    controls_frame.pack(side=TK.TOP)
    name_frame = TTK.Frame(controls_frame)
    name_frame.pack(side=TK.LEFT)
    value_frame = TTK.Frame(controls_frame)
    value_frame.pack(side=TK.RIGHT)
    TTK.Label(name_frame, text="Space", width=15).pack(side=TK.TOP)
    TTK.Label(value_frame, text="Step a single time through messages").pack(side=TK.BOTTOM, anchor=TK.NW)
    TTK.Label(name_frame, text="f", width=15).pack(side=TK.TOP)
    TTK.Label(value_frame, text="Fast-forward through messages").pack(side=TK.BOTTOM, anchor=TK.NW)
    TTK.Label(name_frame, text="Enter", width=15).pack(side=TK.TOP)
    TTK.Label(value_frame, text="Kill stepper daemon and run as an async emulator").pack(side=TK.BOTTOM, anchor=TK.NW)
    TTK.Label(name_frame, text="tab", width=15).pack(side=TK.TOP)
    TTK.Label(value_frame, text="Show all messages currently waiting to be transmitted").pack(side=TK.BOTTOM, anchor=TK.NW)
    TTK.Label(name_frame, text="s", width=15).pack(side=TK.TOP)
    TTK.Label(value_frame, text="Pick the next message waiting to be transmitteed to transmit next").pack(side=TK.BOTTOM, anchor=TK.NW)
    TTK.Label(name_frame, text="e", width=15).pack(side=TK.TOP)
    TTK.Label(value_frame, text="Toggle between sync and async emulation").pack(side=TK.BOTTOM, anchor=TK.NW)