from exercise_runner import run_exercise
from PyQt6.QtWidgets import QApplication, QWidget, QLineEdit, QVBoxLayout, QPushButton, QHBoxLayout, QLabel
from PyQt6.QtGui import QIcon
from sys import argv
app = QApplication(argv)

windows = list()


window = QWidget()
window.setWindowIcon(QIcon('icon.ico'))
window.setWindowTitle("Distributed Exercises AAU")
main = QVBoxLayout()
window.setFixedSize(600, 100)
start_button = QPushButton("start")
main.addWidget(start_button)
input_area_labels = QHBoxLayout()
input_area_areas = QHBoxLayout()
actions = {'Lecture':[print, 0], 'Algorithm': [print, 'PingPong'], 'Type': [print, 'stepping'], 'Devices': [print, 3]}

for action in actions.items():
    input_area_labels.addWidget(QLabel(action[0]))
    field = QLineEdit()
    input_area_areas.addWidget(field)
    field.setText(str(action[1][1]))
    actions[action[0]][0] = field.text
main.addLayout(input_area_labels)
main.addLayout(input_area_areas)


def start_exercise():
    windows.append(run_exercise(int(actions['Lecture'][0]()), actions['Algorithm'][0](), actions['Type'][0](), int(actions['Devices'][0]())))

start_button.clicked.connect(start_exercise)
window.setLayout(main)
window.show()
app.exec()
