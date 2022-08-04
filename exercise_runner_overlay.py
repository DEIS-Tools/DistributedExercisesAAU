from exercise_runner import run_exercise
from PyQt6.QtWidgets import QApplication, QWidget, QLineEdit, QVBoxLayout, QPushButton, QHBoxLayout, QLabel, QComboBox
from PyQt6.QtGui import QIcon
from sys import argv
app = QApplication(argv)

windows = list()


window = QWidget()
window.setWindowIcon(QIcon('icon.ico'))
window.setWindowTitle("Distributed Exercises AAU")
main = QVBoxLayout()
window.setFixedSize(600, 100)
button_layout = QHBoxLayout()
start_button = QPushButton("Start")
button_layout.addWidget(start_button)
advanced_button = QPushButton("Advanced")
button_layout.addWidget(advanced_button)
main.addLayout(button_layout)
input_area_labels = QHBoxLayout()
input_area_areas = QHBoxLayout()
actions:dict[str, list[QLineEdit, str]] = {'Algorithm': [QLineEdit, 'PingPong'], 'Type': [QLineEdit, 'stepping'], 'Devices': [QLineEdit, 3]}
input_area_labels.addWidget(QLabel('Lecture'))
combobox = QComboBox()
combobox.addItems([str(i) for i in range(13) if i != 3])
input_area_areas.addWidget(combobox)

for action in actions.items():
    input_area_labels.addWidget(QLabel(action[0]))
    field = QLineEdit()
    input_area_areas.addWidget(field)
    field.setText(str(action[1][1]))
    actions[action[0]][0] = field
main.addLayout(input_area_labels)
main.addLayout(input_area_areas)
actions['Algorithm'][0].setDisabled(True)
is_disabled = True

actions['Lecture'] = [combobox]


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
        11:'ChordClient',
        12:'AodvNode'}
    lecture = int(text)

    actions['Algorithm'][0].setText(exercises[lecture])

combobox.currentTextChanged.connect(text_changed)

def start_exercise():
    windows.append(run_exercise(int(actions['Lecture'][0].currentText()), actions['Algorithm'][0].text(), actions['Type'][0].text(), int(actions['Devices'][0].text())))

def advanced():
    global is_disabled
    if is_disabled:
        actions['Algorithm'][0].setDisabled(False)
        is_disabled = False
    else:
        actions['Algorithm'][0].setDisabled(True)
        is_disabled = True

start_button.clicked.connect(start_exercise)
advanced_button.clicked.connect(advanced)
window.setLayout(main)
window.show()
app.exec()
