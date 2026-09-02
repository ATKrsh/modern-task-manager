import sys
import psutil
import time
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QLabel
)
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor
import pyqtgraph as pg

# Windows 11 Dark Mode Stylesheet
STYLE_SHEET = """
QMainWindow {
    background-color: #202020;
}
QTabWidget::pane {
    border: none;
    background-color: #202020;
}
QTabBar::tab {
    background: transparent;
    color: #FFFFFF;
    padding: 10px 20px;
    font-size: 14px;
    border-bottom: 3px solid transparent;
}
QTabBar::tab:selected {
    color: #60CDFF;
    border-bottom: 3px solid #60CDFF;
}
QTabBar::tab:hover {
    background: rgba(255, 255, 255, 0.05);
}
QTableWidget {
    background-color: #2C2C2C;
    color: #FFFFFF;
    border: 1px solid #333333;
    border-radius: 8px;
    gridline-color: #333333;
}
QHeaderView::section {
    background-color: #202020;
    color: #A0A0A0;
    padding: 5px;
    border: none;
    border-bottom: 1px solid #333333;
    font-weight: bold;
}
QTableWidget::item:selected {
    background-color: #3A3A3A;
}
QLabel {
    color: #FFFFFF;
}
"""

class WorkerThread(QThread):
    metrics_updated = pyqtSignal(dict)
    processes_updated = pyqtSignal(list)

    def run(self):
        while True:
            # Metrics
            cpu_percent = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            metrics = {
                'cpu': cpu_percent,
                'memory': mem.percent,
                'disk': disk.percent
            }
            self.metrics_updated.emit(metrics)

            # Processes
            procs = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
                try:
                    info = proc.info
                    mem_mb = info['memory_info'].rss / (1024 * 1024) if info['memory_info'] else 0
                    procs.append({
                        "pid": info['pid'],
                        "name": info['name'],
                        "cpu": info['cpu_percent'] or 0.0,
                        "memory": mem_mb
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            procs.sort(key=lambda x: x['memory'], reverse=True)
            self.processes_updated.emit(procs[:100]) # Top 100
            
            time.sleep(1)


class TaskManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Task Manager")
        self.resize(1000, 700)
        self.setStyleSheet(STYLE_SHEET)

        # Main Widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # Tabs
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)

        self.setup_processes_tab()
        self.setup_performance_tab()

        # Threading for real-time updates
        self.worker = WorkerThread()
        self.worker.metrics_updated.connect(self.update_performance)
        self.worker.processes_updated.connect(self.update_processes)
        self.worker.start()

    def setup_processes_tab(self):
        self.proc_tab = QWidget()
        layout = QVBoxLayout(self.proc_tab)
        
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["PID", "Name", "CPU (%)", "Memory (MB)"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        
        layout.addWidget(self.table)
        self.tabs.addTab(self.proc_tab, "Processes")

    def setup_performance_tab(self):
        self.perf_tab = QWidget()
        layout = QVBoxLayout(self.perf_tab)
        
        # PyQtGraph Global Settings for modern look
        pg.setConfigOption('background', '#202020')
        pg.setConfigOption('foreground', '#FFFFFF')

        # CPU Chart
        self.cpu_label = QLabel("CPU Usage: 0%")
        self.cpu_label.setFont(QFont("Segoe UI Variable", 12, QFont.Bold))
        layout.addWidget(self.cpu_label)
        
        self.cpu_plot = pg.PlotWidget()
        self.cpu_plot.setYRange(0, 100)
        self.cpu_plot.showGrid(x=True, y=True, alpha=0.3)
        self.cpu_data = [0] * 60
        self.cpu_curve = self.cpu_plot.plot(self.cpu_data, pen=pg.mkPen(color='#60CDFF', width=2), fillLevel=0, brush=(96, 205, 255, 50))
        layout.addWidget(self.cpu_plot)

        # Memory Chart
        self.mem_label = QLabel("Memory Usage: 0%")
        self.mem_label.setFont(QFont("Segoe UI Variable", 12, QFont.Bold))
        layout.addWidget(self.mem_label)
        
        self.mem_plot = pg.PlotWidget()
        self.mem_plot.setYRange(0, 100)
        self.mem_plot.showGrid(x=True, y=True, alpha=0.3)
        self.mem_data = [0] * 60
        self.mem_curve = self.mem_plot.plot(self.mem_data, pen=pg.mkPen(color='#8A2BE2', width=2), fillLevel=0, brush=(138, 43, 226, 50))
        layout.addWidget(self.mem_plot)

        self.tabs.addTab(self.perf_tab, "Performance")

    def update_processes(self, procs):
        self.table.setRowCount(len(procs))
        for row, p in enumerate(procs):
            pid_item = QTableWidgetItem(str(p['pid']))
            name_item = QTableWidgetItem(p['name'])
            cpu_item = QTableWidgetItem(f"{p['cpu']:.1f}%")
            mem_item = QTableWidgetItem(f"{p['memory']:.1f} MB")
            
            # Align center/right for numbers
            pid_item.setTextAlignment(Qt.AlignCenter)
            cpu_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            mem_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            self.table.setItem(row, 0, pid_item)
            self.table.setItem(row, 1, name_item)
            self.table.setItem(row, 2, cpu_item)
            self.table.setItem(row, 3, mem_item)

    def update_performance(self, metrics):
        # Update CPU
        self.cpu_label.setText(f"CPU Usage: {metrics['cpu']:.1f}%")
        self.cpu_data = self.cpu_data[1:] + [metrics['cpu']]
        self.cpu_curve.setData(self.cpu_data)

        # Update Memory
        self.mem_label.setText(f"Memory Usage: {metrics['memory']:.1f}%")
        self.mem_data = self.mem_data[1:] + [metrics['memory']]
        self.mem_curve.setData(self.mem_data)


if __name__ == '__main__':
    # Fix for high DPI displays on Windows
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    
    # Modern font
    font = QFont("Segoe UI Variable Display", 10)
    app.setFont(font)

    window = TaskManager()
    window.show()
    sys.exit(app.exec_())
