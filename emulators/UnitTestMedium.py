from time import sleep
from emulators.MessageStub import MessageStub
from emulators.Medium import Medium
from csv import reader

class UnitTestMedium(Medium):
	execution_sequence:list[tuple[MessageStub]] = list()
	message_type = MessageStub

	def __init__(self, index: int, emulator, path="tests/demo.csv"):
		super().__init__(index, emulator)
		message_type = emulator.kind

	def send(self, message:MessageStub):
		assert ("send", message) in self.execution_sequence
		while True:
			if message == self.execution_sequence[0]:
				super().send(message)
			else:
				sleep(.1)

	def receive(self):
		message = super().receive()
		assert ("receive", message) in self.execution_sequence
		while True:
			if message == self.execution_sequence[0]:
				return message
			else:
				sleep(.1)
	
	def load_execution_sequence(self, path):
		with open(path) as file:
			csv_reader = reader(file)
			for row in csv_reader:
				self.execution_sequence.append((row[0], self.message_type(int(row[1]), int(row[2]), row[3])))
