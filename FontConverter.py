import sys
import os
import time
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, 
                             QWidget, QComboBox, QCheckBox, QTextEdit, QFileDialog, QProgressDialog, QGridLayout, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QMouseEvent
from fontTools.ttLib import TTFont
from fontTools.subset import Subsetter
from io import BytesIO

class FontConverter_GUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("字体转换器")
        self.setFixedSize(400, 550)  # 增加窗口高度以适应“关于”按钮

        layout = QGridLayout()
        
        self.label = QLabel("拖放字体文件到这里，或点击选择文件", self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setWordWrap(True)  # 启用自动换行
        self.label.setStyleSheet("""
            QLabel {
                border: 2px dashed #888;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        self.label.setMinimumHeight(100)  # 设置最小高度以确保有足够的拖放空间
        self.label.mousePressEvent = self.label_clicked  # 将鼠标点击事件连接到自定义函数
        layout.addWidget(self.label, 0, 0, 1, 2)

        layout.addWidget(QLabel("选择输出格式："), 1, 0)
        self.format_combo = QComboBox(self)
        self.format_combo.addItems(["TTF", "OTF", "WOFF", "WOFF2"])
        layout.addWidget(self.format_combo, 1, 1)

        self.subset_checkbox = QCheckBox("裁剪子集", self)
        self.subset_checkbox.stateChanged.connect(self.toggle_subset_input)
        layout.addWidget(self.subset_checkbox, 2, 0, 1, 2)

        self.subset_input = QTextEdit(self)
        self.subset_input.setPlaceholderText("输入要保留的字符（每行一个字符）")
        self.subset_input.setVisible(False)
        self.subset_input.setMinimumHeight(150)
        layout.addWidget(self.subset_input, 3, 0, 1, 2)

        self.convert_button = QPushButton("转换", self)
        self.convert_button.setFixedHeight(50)  # 增大转换按钮
        self.convert_button.setStyleSheet("""
            QPushButton {
                padding: 10px;
                font-size: 16px;
            }
        """)
        self.convert_button.clicked.connect(self.convert_font)
        layout.addWidget(self.convert_button, 4, 0, 1, 2)

        self.about_button = QPushButton("关于", self)
        self.about_button.clicked.connect(self.show_about_dialog)
        layout.addWidget(self.about_button, 5, 0, 1, 2)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.setAcceptDrops(True)

    def label_clicked(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            font_file, _ = QFileDialog.getOpenFileName(self, "选择字体文件", "", "字体文件 (*.ttf *.otf *.woff *.woff2)")
            if font_file:
                self.font_file = font_file
                self.label.setText(f"已加载<br><font style='font-size: 12pt; font-weight: bold;'>{os.path.basename(self.font_file)}</font>")

    def toggle_subset_input(self, state):
        self.subset_input.setVisible(state == Qt.Checked)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
            self.label.setStyleSheet("""
                QLabel {
                    border: 2px dashed #888;
                    border-radius: 5px;
                    padding: 10px;
                }
            """)
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.label.setStyleSheet("""
            QLabel {
                border: 2px dashed #888;
                border-radius: 5px;
                padding: 10px;
            }
        """)

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            self.font_file = files[0]
            self.label.setText(f"已加载<br><font style='font-size: 12pt; font-weight: bold;'>{os.path.basename(self.font_file)}</font>")
        self.label.setStyleSheet("""
            QLabel {
                border: 2px dashed #888;
                border-radius: 5px;
                padding: 10px;
            }
        """)

    def convert_font(self):
        if hasattr(self, 'font_file'):
            input_ext = os.path.splitext(self.font_file)[1].lower()
            output_ext = self.format_combo.currentText().lower()
            
            # 生成带有日期时间的文件名
            base_name = os.path.splitext(os.path.basename(self.font_file))[0]
            date_time = datetime.now().strftime("%Y%m%d%H%M")
            default_filename = f"{base_name}_{date_time}.{output_ext}"
            
            # 打开文件对话框让用户选择保存位置
            output_file, _ = QFileDialog.getSaveFileName(self, "保存文件", default_filename, f"{output_ext.upper()} 文件 (*.{output_ext})")
            
            if not output_file:  # 用户取消了保存
                return

            try:
                # 检查是否安装了 brotli（用于 WOFF2）
                if output_ext == 'woff2' or input_ext == '.woff2':
                    try:
                        from fontTools.ttLib import woff2
                    except ImportError:
                        raise ImportError("WOFF2 格式需要 Brotli 库。请使用 'pip install brotli' 安装。")

                # 创建进度对话框
                progress = QProgressDialog("正在转换字体...", "取消", 0, 100, self)
                progress.setWindowModality(Qt.WindowModal)
                progress.setWindowTitle("进度")
                progress.show()

                # 读取字体文件
                if input_ext == '.woff2':
                    with open(self.font_file, 'rb') as woff2_file:
                        decompressed_font = BytesIO()
                        woff2.decompress(woff2_file, decompressed_font)
                        decompressed_font.seek(0)
                        font = TTFont(decompressed_font)
                else:
                    font = TTFont(self.font_file)

                progress.setValue(30)
                QApplication.processEvents()

                # 如果选中了裁剪子集，进行子集化
                if self.subset_checkbox.isChecked():
                    subsetter = Subsetter()
                    subset_text = self.subset_input.toPlainText().replace('\n', '')  # 移除换行符
                    subsetter.populate(text=subset_text)
                    subsetter.subset(font)

                progress.setValue(60)
                QApplication.processEvents()

                # 保存为目标格式
                if output_ext == 'woff2':
                    font.flavor = 'woff2'
                    font.save(output_file)
                elif output_ext == 'woff':
                    font.flavor = 'woff'
                    font.save(output_file)
                else:
                    font.save(output_file)

                # 模拟完成过程
                for i in range(61, 101):
                    progress.setValue(i)
                    QApplication.processEvents()
                    time.sleep(0.02)  # 稍微延迟一下，让进度条动画更平滑

                progress.close()

                self.label.setText(f"转换完成 <br><font style='font-size: 12pt; font-weight: bold;'> {os.path.basename(output_file)}</font>")
            except ImportError as e:
                self.label.setText(f"错误：{str(e)}")
            except Exception as e:
                self.label.setText(f"转换过程中发生错误: {str(e)}")
        else:
            self.label.setText("请先拖放一个字体文件")

    def show_about_dialog(self):
      
        compile_date = "未知"
        try:
            with open(os.path.join(sys._MEIPASS, 'compile_date.txt')) as f:
                compile_date = f.read().strip()
        except Exception:
            pass
          
        QMessageBox.about(
        self,"关于","""字体转换器<br>编译日期：{compile_date}<br><br> <a href="https://github.com/LANMIN-X/FontConverter_GUI/">Github</a><br><a href="https://zfont.cn">找字体</a>""")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FontConverter_GUI()
    window.show()
    sys.exit(app.exec_())

 
