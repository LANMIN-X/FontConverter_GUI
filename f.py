import sys
import os
import subprocess
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, 
                             QFileDialog, QListWidget, QMessageBox, QLabel, QHBoxLayout)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDropEvent

class DropArea(QLabel):
    filesDropped = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignCenter)
        self.setText("拖放字体文件或文件夹到这里\n或点击选择文件")
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 5px;
                padding: 20px;
                background-color: #f0f0f0;
            }
        """)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        self.filesDropped.emit(files)

    def mousePressEvent(self, event):
        self.filesDropped.emit([])

class FontMergerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("字体合并工具")
        self.setGeometry(100, 100, 400, 500)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.drop_area = DropArea()
        self.drop_area.filesDropped.connect(self.handle_dropped_files)
        self.layout.addWidget(self.drop_area)

        self.font_list = QListWidget()
        self.layout.addWidget(self.font_list)

        button_layout = QHBoxLayout()
        self.merge_button = QPushButton("合并字体")
        self.merge_button.clicked.connect(self.merge_fonts)
        button_layout.addWidget(self.merge_button)

        self.clear_button = QPushButton("清理文件")
        self.clear_button.clicked.connect(self.clear_files)
        button_layout.addWidget(self.clear_button)

        self.layout.addLayout(button_layout)

        self.font_files = []

    def handle_dropped_files(self, files):
        if not files:
            self.add_fonts()
        else:
            for file in files:
                if os.path.isdir(file):
                    self.add_fonts_from_directory(file)
                else:
                    self.add_font(file)

    def add_fonts_from_directory(self, directory):
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith(('.ttf', '.otf')):
                    self.add_font(os.path.join(root, file))

    def add_fonts(self):
        files, _ = QFileDialog.getOpenFileNames(self, "选择字体文件", "", "字体文件 (*.ttf *.otf)")
        for file in files:
            self.add_font(file)

    def add_font(self, path):
        if path.lower().endswith(('.ttf', '.otf')) and path not in self.font_files:
            self.font_files.append(path)
            self.font_list.addItem(os.path.basename(path))

    def clear_files(self):
        self.font_files.clear()
        self.font_list.clear()

    def merge_fonts(self):
        if len(self.font_files) < 2:
            QMessageBox.warning(self, "警告", "请至少添加两个字体文件")
            return

        output_file, _ = QFileDialog.getSaveFileName(self, "保存合并后的字体", "", "字体文件 (*.ttf)")
        if not output_file:
            return

        try:
            command = ["pyftmerge", f"--output-file={output_file}"] + self.font_files
            print(f"执行命令: {' '.join(command)}")
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            
            if result.returncode == 0:
                QMessageBox.information(self, "成功", f"字体已成功合并并保存为 {output_file}")
            else:
                raise Exception(f"pyftmerge 返回非零退出码: {result.returncode}")

        except subprocess.CalledProcessError as e:
            error_msg = f"合并字体时出错：\n{e.stderr}"
            QMessageBox.critical(self, "错误", error_msg)
        except Exception as e:
            error_msg = f"合并字体时出错：\n{str(e)}"
            QMessageBox.critical(self, "错误", error_msg)

if __name__ == "__main__":
    if sys.platform == 'darwin':
        from PyQt5.QtCore import QCoreApplication
        QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
        QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    window = FontMergerApp()
    window.show()
    sys.exit(app.exec_())
