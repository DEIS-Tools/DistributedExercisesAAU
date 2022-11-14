from exercise_runner import run_exercise
from PyQt6.QtWidgets import QApplication, QWidget, QLineEdit, QVBoxLayout, QPushButton, QHBoxLayout, QLabel, QComboBox
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt
from sys import argv
app = QApplication(argv)

windows = list()

#new
window = QWidget()
window.setWindowIcon(QIcon('icon.ico'))
window.setWindowTitle("Distributed Exercises AAU")
main = QVBoxLayout()
window.setFixedSize(600, 100)
start_button = QPushButton("Start")
main.addWidget(start_button)
input_area = QHBoxLayout()
lecture_layout = QVBoxLayout()
lecture_layout.addWidget(QLabel("Lecture"), alignment=Qt.AlignmentFlag.AlignCenter)
lecture_combobox = QComboBox()
lecture_combobox.addItems([str(i) for i in range(13) if i != 3])
lecture_layout.addWidget(lecture_combobox)
input_area.addLayout(lecture_layout)
type_layout = QVBoxLayout()
type_layout.addWidget(QLabel("Type"), alignment=Qt.AlignmentFlag.AlignCenter)
type_combobox = QComboBox()
type_combobox.addItems(["stepping", "async", "sync"])
type_layout.addWidget(type_combobox)
input_area.addLayout(type_layout)
algorithm_layout = QVBoxLayout()
algorithm_layout.addWidget(QLabel("Algorithm"), alignment=Qt.AlignmentFlag.AlignCenter)
algorithm_input = QLineEdit()
algorithm_input.setText("PingPong")
algorithm_layout.addWidget(algorithm_input)
input_area.addLayout(algorithm_layout)
devices_layout = QVBoxLayout()
devices_layout.addWidget(QLabel("Devices"), alignment=Qt.AlignmentFlag.AlignCenter)
devices_input = QLineEdit()
devices_input.setText("3")
devices_layout.addWidget(devices_input)
input_area.addLayout(devices_layout)
main.addLayout(input_area)
starting_exercise = False
actions:dict[str, QLineEdit | QComboBox] = {"Lecture":lecture_combobox, "Type":type_combobox, "Algorithm":algorithm_input, "Devices":devices_input}

def text_changed(text):
    exercises = {
        0:'PingPong', 
        1:'Gossip', 
        2:'RipCommunication', 
        4:'TokenRing', 
        5:'TOSEQMulticast', 
        6:'PAXOS', 
        7:'Bully',
        8:'GfsNetwork',
        9:'MapReduceNetwork',
        10:'BlockchainNetwork',
        11:'ChordNetwork',
        12:'AodvNode'}
    lecture = int(text)

    actions['Algorithm'].setText(exercises[lecture])

lecture_combobox.currentTextChanged.connect(text_changed)

def start_exercise():
    global starting_exercise
    if not starting_exercise:
        starting_exercise = True
        windows.append(run_exercise(int(actions['Lecture'].currentText()), actions['Algorithm'].text(), actions['Type'].currentText(), int(actions['Devices'].text()), True))
        starting_exercise = False


start_button.clicked.connect(start_exercise)
window.setLayout(main)
window.show()
app.exec()
