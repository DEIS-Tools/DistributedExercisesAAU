from time import sleep
from emulators.MessageStub import MessageStub
from emulators.Medium import Medium
from csv import reader

class UnitTestMedium(Medium):

	def __init__(self, index: int, emulator):
		super().__init__(index, emulator)

	def send(self, message:MessageStub):
		while True:
			try:
				if not self._id == self._emulator.execution_sequence[0][1].source or not self._emulator.execution_sequence[0][0] == 'send':
					sleep(.1)
					self.send(message)
				else:
					break
			except:
				if not self._id == self._emulator.execution_sequence[0][1].source or not self._emulator.execution_sequence[0][0] == 'send':
					sleep(.1)
					self.send(message)
				else:
					break
		self._emulator.execution_sequence.pop(0)
		super().send(message)

	def receive(self):
		print(f'{self._id} reached receive function')
		if self._emulator.execution_sequence[0][1].destination == self._id and self._emulator.execution_sequence[0][0] == 'receive':
			self._emulator.execution_sequence.pop(0)
			return super().receive()
	


def load_execution_sequence(path) -> list[tuple[str, MessageStub]]:
	with open(path) as file:
		csv_reader = reader(file)
		execution_sequence:list[tuple[str, MessageStub]] = list()
		for row in csv_reader:
			if not row[0] == 'send' and not row[0] == 'receive':
				continue
			execution_sequence.append((row[0], MessageStub(int(row[1]), int(row[2]))))
	return execution_sequence
