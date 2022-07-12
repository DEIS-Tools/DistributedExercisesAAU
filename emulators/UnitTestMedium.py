from time import sleep
from emulators.MessageStub import MessageStub
from emulators.Medium import Medium
from csv import reader

class UnitTestMedium(Medium):

	def __init__(self, index: int, emulator):
		super().__init__(index, emulator)

	def send(self, message:MessageStub):
		while True:
			if message is self._emulator.execution_sequence[0][1]:
				self._emulator.execution_sequence.pop(0)
				super().send(message)

	def receive(self):
		message = super().receive()
		while True:
			if message is self._emulator.execution_sequence[0][1]:
				self._emulator.execution_sequence.pop(0)
				return message
	


def load_execution_sequence(path, message_type) -> list[tuple[str, MessageStub]]:
	with open(path) as file:
		csv_reader = reader(file)
		execution_sequence:list[tuple[str, MessageStub]] = list()
		for row in csv_reader:
			if not row[0] == 'send' and not row[0] == 'receive':
				continue
			execution_sequence.append((row[0], message_type(int(row[1]), int(row[2]), row[3])))
	return execution_sequence
