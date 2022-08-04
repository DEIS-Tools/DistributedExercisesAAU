from importlib import import_module
from typing import Any
from emulators.MessageStub import MessageStub
from emulators.Medium import Medium
from csv import reader

class UnitTestMedium(Medium):

	def __init__(self, index: int, emulator, lecture):
		super().__init__(index, emulator)
		self.lecture = lecture
		self.testing_module = import_module(f'emulators.tests.modules.exercise{self.lecture}') if not self.lecture == 0 else import_module("emulators.tests.modules.demo")

	def send(self, message:MessageStub):
		while not self._id == self._emulator.sending_execution_sequence[0][0] and not self.testing_module.test().message_test(message, self._emulator.sending_execution_sequence[0][1]):
			pass
		super().send(message)
		self._emulator.sending_execution_sequence.pop(0)

	def receive(self):
		if not self._id == self._emulator.receiving_execution_sequence[0][0]:
			return None
		recv =  super().receive()
		if self.testing_module.test().message_test(recv, self._emulator.receiving_execution_sequence[0][1]):
			
			if not recv == None:
				self._emulator.receiving_execution_sequence.pop(0)
			return recv
		else:
			self.send(recv)
			return None
	


def load_execution_sequence(path) -> list[tuple[int, Any]]:
	with open(path) as file:
		csv_reader = reader(file)
		execution_sequence:list[int] = list()
		for row in csv_reader:
			execution_sequence.append((int(row[0]), row[1]))
	return execution_sequence