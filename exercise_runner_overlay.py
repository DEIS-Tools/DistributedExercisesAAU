import typing
from PyQt6 import QtCore
from exercise_runner import run_exercise
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QIcon, QRegularExpressionValidator
from PyQt6.QtCore import Qt, QThread, QObject, pyqtSignal, QRegularExpression
from sys import argv

class Worker(QObject):
    finished: pyqtSignal = pyqtSignal()
    window: pyqtSignal = pyqtSignal(QObject)
    def __init__(self) -> None:
        super().__init__()

    def run(self,
        lecture_no: int,
        algorithm: str,
        network_type: str,
        number_of_devices: int,
        ):
        self.window.emit(run_exercise(lecture_no, algorithm, network_type, number_of_devices, True))
        self.finished.emit()


class InputArea(QFormLayout):
    def __init__(self) -> None:
        super().__init__()
        self.__algs = [
            "PingPong",
            "Gossip",
            "RipCommunication",
            "TokenRing",
            "TOSEQMulticast",
            "PAXOS",
            "Bully",
            "GfsNetwork",
            "MapReduceNetwork",
            "BlockchainNetwork",
            "ChordNetwork",
            "AodvNode",
        ]
        self.lecture = QComboBox()
        self.lecture.addItems([str(i) for i in range(13) if i != 3])

        self.type = QComboBox()
        self.type.addItems(["stepping", "async", "sync"])

        self.alg = QComboBox()
        self.alg.addItems(self.__algs)

        self.device = QLineEdit(text="3")

        self.device.setValidator(
            QRegularExpressionValidator(
                QRegularExpression(r"[0-9]*")
                ))

        self.addRow("Lecture", self.lecture)
        self.addRow("Type", self.type)
        self.addRow("Algorithm", self.alg)
        self.addRow("Devices", self.device)

        self.lecture.currentTextChanged.connect(self.__lecture_handler)
        self.__lecture_handler("0")

    def __lecture_handler(self, text: str):
        self.alg.setCurrentText(self.__algs[int(text)])

    def data(self):
        return (
            int(self.lecture.currentText()), 
            self.alg.currentText(),
            self.type.currentText(),
            int(self.device.text())
            )

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__(
            windowTitle="Distributed Exercises AAU",
            windowIcon=QIcon("icon.ico")
            )
        self.__thread = None
        self.__worker = None
        self.__windows = []
        layout = QVBoxLayout()
        self.__start_btn = QPushButton("Start")

        group = QGroupBox(title="Inputs")
        self.__input_area = InputArea()
        group.setLayout(self.__input_area)

        layout.addWidget(group)
        layout.addWidget(self.__start_btn)
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self.__start_btn.clicked.connect(self.__start)

    def __start(self):
        if self.__worker is not None:
            return

        self.__thread = QThread()
        self.__worker = Worker()
        self.__thread.started.connect(lambda: self.__worker.run(*self.__input_area.data()))
        self.__worker.finished.connect(self.__thread.quit)
        self.__worker.window.connect(self.__window_handler)
        self.__worker.finished.connect(self.__worker.deleteLater)
        self.__thread.finished.connect(self.__thread.deleteLater)
        self.__thread.start()

    def __window_handler(self, window: QObject):
        self.__windows.append(window)

    def show(self) -> None:
        self.resize(600, 100)
        return super().show()
    

app = QApplication(argv)
window = MainWindow()
window.show()
app.exec()
