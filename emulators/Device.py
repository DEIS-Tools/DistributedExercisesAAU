from emulators.Medium import Medium


class Device:
    def __init__(self, index: int, number_of_devices: int, medium: Medium):
        self._id = index
        self._medium = medium
        self._number_of_devices = number_of_devices

    def run(self):
        raise NotImplementedError("You have to implement a run-method!")

    def print_result(self):
        raise NotImplementedError("You have to implement a result printer!")

    def index(self):
        return self._id

    def number_of_devices(self):
        return self._number_of_devices

    def medium(self):
        return self._medium
