from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import QTimer, QTime, Qt

class ClockWidget(QLabel):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("font-size: 48px; color: white;")
        
        timer = QTimer(self)
        timer.timeout.connect(self.update_time)
        timer.start(1000)
        
        self.update_time()

    def update_time(self):
        current_time = QTime.currentTime()
        time_text = current_time.toString('hh:mm:ss')
        self.setText(time_text)