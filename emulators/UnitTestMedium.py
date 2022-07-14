from emulators.MessageStub import MessageStub
from emulators.Medium import Medium
from csv import reader

class UnitTestMedium(Medium):

	def __init__(self, index: int, emulator):
		super().__init__(index, emulator)

	def send(self, message:MessageStub):
		while not self._id == self._emulator.sending_execution_sequence[0]:
			pass
		super().send(message)
		self._emulator.sending_execution_sequence.pop(0)

	def receive(self):
		if not self._id == self._emulator.receiving_execution_sequence[0]:
			return None
		recv =  super().receive()
		if not recv == None:
			self._emulator.receiving_execution_sequence.pop(0)
		return recv
	


def load_execution_sequence(path) -> list[int]:
	with open(path) as file:
		csv_reader = reader(file)
		execution_sequence:list[int] = list()
		for row in csv_reader:
			if row[0] == 'source' or row[0] == 'destination':
				continue
			execution_sequence.append(int(row[0]))
	return execution_sequence