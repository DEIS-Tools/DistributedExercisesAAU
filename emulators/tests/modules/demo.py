from emulators.Device import Device

class test:
	# example test class, for course holder to implement the remaining tests for exercises
	def run(self, devices:list[Device]):
		# testing whether all messages have been received
		pingpongs = sum([device._rec_ping + device._rec_pong for device in devices])
		max_pingpongs = 10*len(devices)
		assert pingpongs == max_pingpongs
		print("Unit test successfull")