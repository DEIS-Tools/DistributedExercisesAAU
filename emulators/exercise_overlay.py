from random import randint
from threading import Thread
from PyQt6.QtWidgets import QWidget, QApplication, QHBoxLayout, QVBoxLayout, QPushButton, QTabWidget, QLabel
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt
from sys import argv
from math import cos, sin, pi
from emulators.MessageStub import MessageStub

from emulators.table import Table
from emulators.SteppingEmulator import SteppingEmulator

def circle_button_style(size):
	return f'''
	QPushButton {{
		background-color: transparent; 
		border-style: solid; 
		border-width: 2px; 
		border-radius: {int(size/2)}px; 
		border-color: black; 
		max-width: {size}px; 
		max-height: {size}px; 
		min-width: {size}px; 
		min-height: {size}px;
	}}
	QPushButton:hover {{
		background-color: gray;
		border-width: 2px; 
	}}
	QPushButton:pressed {{
		background-color: transparent; 
		border-width: 1px
	}}
	'''

class Window(QWidget):
	h = 600
	w = 600
	device_size = 80
	windows = list()

	def __init__(self, elements, restart_function, emulator:SteppingEmulator):
		super().__init__()
		self.emulator = emulator
		self.setFixedSize(self.w, self.h)
		layout = QVBoxLayout()
		tabs = QTabWidget()
		tabs.addTab(self.main(elements, restart_function), 'Main')
		tabs.addTab(self.controls(), 'controls')
		layout.addWidget(tabs)
		self.setLayout(layout)
		self.setWindowTitle("Test")
		self.setWindowIcon(QIcon("icon.ico"))

	def coordinates(self, center, r, i, n):
		x = sin((i*2*pi)/n)
		y = cos((i*2*pi)/n)
		if x < pi:
			return int(center[0] - (r*x)), int(center[1] - (r*y))
		else:
			return int(center[0] - (r*-x)), int(center[1] - (r*y))

	def show_device_data(self, device_id):
		def show():
			received:list[MessageStub] = list()
			sent:list[MessageStub] = list()
			for message in self.emulator._list_messages_received:
				if message.destination == device_id:
					received.append(message)
				if message.source == device_id:
					sent.append(message)
			if len(received) > len(sent):
				for _ in range(len(received)-len(sent)):
					sent.append("")
			elif len(sent) > len(received):
				for _ in range(len(sent)-len(received)):
					received.append("")
			content = list()
			for i in range(len(received)):
				if received[i] == "":
					msg = str(sent[i]).replace(f'{sent[i].source} -> {sent[i].destination} : ', "").replace(f'{sent[i].source}->{sent[i].destination} : ', "")
					content.append(["", received[i], str(sent[i].destination), msg])
				elif sent[i] == "":
					msg = str(received[i]).replace(f'{received[i].source} -> {received[i].destination} : ', "").replace(f'{received[i].source}->{received[i].destination} : ', "")
					content.append([str(received[i].source), msg, "", sent[i]])
				else:
					sent_msg = str(sent[i]).replace(f'{sent[i].source} -> {sent[i].destination} : ', "").replace(f'{sent[i].source}->{sent[i].destination} : ', "")
					received_msg = str(received[i]).replace(f'{received[i].source} -> {received[i].destination} : ', "").replace(f'{received[i].source}->{received[i].destination} : ', "")
					content.append([str(received[i].source), received_msg, str(sent[i].destination), sent_msg])
			content.insert(0, ['Source', 'Message', 'Destination', 'Message'])
			table = Table(content, title=f'Device #{device_id}')
			self.windows.append(table)
			table.setFixedSize(300, 500)
			table.show()
			return table
		return show
	
	def show_all_data(self):
		content = []
		messages = self.emulator._list_messages_sent
		message_content = []
		for message in messages:
			temp = str(message)
			temp = temp.replace(f'{message.source} -> {message.destination} : ', "")
			temp = temp.replace(f'{message.source}->{message.destination} : ', "")
			message_content.append(temp)

		content = [[str(messages[i].source), str(messages[i].destination), message_content[i], str(i)] for i in range(len(messages))]
		content.insert(0, ['Source', 'Destination', 'Message', 'Sequence number'])
		table = Table(content, title=f'All data')
		self.windows.append(table)
		table.setFixedSize(500, 500)
		table.show()
		return table

	def stop_stepper(self):
		self.emulator.listener.stop()
		self.emulator.listener.join()

	def end(self):
		self.emulator._stepping = False
		while not self.emulator.all_terminated():
			pass
		Thread(target=self.stop_stepper, daemon=True).start()
	
	def step(self):
		self.emulator._single = True
		if self.emulator.all_terminated():
			Thread(target=self.stop_stepper, daemon=True).start()

	def main(self, num_devices, restart_function):
		main_tab = QWidget()
		layout = QVBoxLayout()
		device_area = QWidget()
		device_area.setFixedSize(500, 500)
		layout.addWidget(device_area)
		main_tab.setLayout(layout)
		for i in range(num_devices):
			x, y = self.coordinates((device_area.width()/2, device_area.height()/2), (device_area.height()/2) - (self.device_size/2), i, num_devices)
			button = QPushButton(f'Device #{i}', main_tab)
			button.resize(self.device_size, self.device_size)
			button.setStyleSheet(circle_button_style(self.device_size))
			button.move(x, int(y - (self.device_size/2)))
			button.clicked.connect(self.show_device_data(i))
		
		button_actions = {'Step': self.step, 'End': self.end, 'Restart algorithm': restart_function, 'Show all messages': self.show_all_data}
		inner_layout = QHBoxLayout()
		for action in button_actions.items():
			button = QPushButton(action[0])
			button.clicked.connect(action[1])
			inner_layout.addWidget(button)
		layout.addLayout(inner_layout)

		return main_tab

	def controls(self):
		controls_tab = QWidget()
		content = {'Space': 'Step a single time through messages', 'f': 'Fast forward through messages', 'Enter': 'Kill stepper daemon and run as an async emulator'}
		main = QVBoxLayout()
		main.setAlignment(Qt.AlignmentFlag.AlignTop)
		controls = QLabel("Controls")
		controls.setAlignment(Qt.AlignmentFlag.AlignCenter)
		main.addWidget(controls)
		for item in content.items():
			inner = QHBoxLayout()
			inner.addWidget(QLabel(item[0]))
			inner.addWidget(QLabel(item[1]))
			main.addLayout(inner)
		controls_tab.setLayout(main)
		return controls_tab

if __name__ == "__main__":
	app = QApplication(argv)
	window = Window(argv[1] if len(argv) > 1 else 10, lambda: print("Restart function"))

	app.exec()