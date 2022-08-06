from typing import Any
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QScrollArea, QPushButton
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt

class Table(QScrollArea):
	def __init__(self, content:list[list[str | QWidget]], title="table"):
		super().__init__()
		widget = QWidget()
		self.setWindowIcon(QIcon('icon.ico'))
		self.setWindowTitle(title)
		columns = QVBoxLayout()
		columns.setAlignment(Qt.AlignmentFlag.AlignTop)
		for row in content:
			column = QHBoxLayout()
			for element in row:
				if type(element) is str:
					label = QLabel(element)
					label.setAlignment(Qt.AlignmentFlag.AlignCenter)
				else:
					label = element
				column.addWidget(label)
			columns.addLayout(column)
		widget.setLayout(columns)
		self.setWidgetResizable(True)
		self.setWidget(widget)



if __name__ == "__main__":
	from PyQt6.QtWidgets import QApplication
	from sys import argv
	app = QApplication(argv)
	table = Table([[str(i+j) for i in range(5)] for j in range(5)])
	table.show()
	app.exec()
	