import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QFileDialog, QLabel, QListWidget, QListWidgetItem, 
                             QCheckBox, QMessageBox, QLineEdit)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDragEnterEvent, QDropEvent
from qdarkstyle import load_stylesheet_pyqt5
from fontTools.ttLib import TTFont
from fontTools.varLib.mutator import instantiateVariableFont

class DropArea(QLabel):
    def __init__(self, main_window):
        super().__init__("拖放字体文件到这里或点击选择")
        self.main_window = main_window
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #888;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        self.setMinimumHeight(100)  # 设置最小高度以确保有足够的拖放空间
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            self.main_window.load_font(url.toLocalFile())

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.main_window.select_font()

class VariableFontWeightGenerator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.font_path = None
        self.weights = list(range(100, 901, 100))  # 默认字重 100-900
        self.custom_weights = []  # 自定义字重
        self.initUI()

    def initUI(self):
        self.setWindowTitle('可变体字重生成器')
        self.setFixedSize(400, 550)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 字体选择区域
        self.drop_area = DropArea(self)
        main_layout.addWidget(self.drop_area)

        # 字重选择区域
        self.select_all_checkbox = QCheckBox("全选")
        self.select_all_checkbox.stateChanged.connect(self.toggle_all_weights)
        main_layout.addWidget(self.select_all_checkbox)

        self.weight_list = QListWidget()
        self.update_weight_list()
        main_layout.addWidget(self.weight_list)

        # 自定义字重输入
        custom_weight_layout = QHBoxLayout()
        self.custom_weight_input = QLineEdit()
        self.custom_weight_input.setPlaceholderText("输入自定义字重 (100-900)")
        self.custom_weight_input.setFixedHeight(30)  # 增大转换按钮
        custom_weight_layout.addWidget(self.custom_weight_input)
        add_custom_weight_button = QPushButton('添加')
        add_custom_weight_button.setFixedWidth(50)  # 增大转换按钮
        add_custom_weight_button.setFixedHeight(30)  # 增大转换按钮
        add_custom_weight_button.clicked.connect(self.add_custom_weight)
        custom_weight_layout.addWidget(add_custom_weight_button)
        main_layout.addLayout(custom_weight_layout)

        # 生成按钮
        self.generate_button = QPushButton('生成选中字重')
        self.generate_button.setFixedHeight(50)  # 增大转换按钮
        self.generate_button.clicked.connect(self.generate_ttfs)
        self.generate_button.setEnabled(False)
        main_layout.addWidget(self.generate_button)

        self.about_button = QPushButton("关于", self)
        self.about_button.clicked.connect(self.show_about_dialog)
        main_layout.addWidget(self.about_button)

    def update_weight_list(self):
        self.weight_list.clear()
        all_weights = sorted(set(self.weights + self.custom_weights))
        for weight in all_weights:
            item = QListWidgetItem(self.weight_list)
            checkbox = QCheckBox(str(weight))
            checkbox.stateChanged.connect(self.update_select_all_checkbox)
            item.setSizeHint(checkbox.sizeHint())
            self.weight_list.setItemWidget(item, checkbox)

    def toggle_all_weights(self, state):
        for i in range(self.weight_list.count()):
            item = self.weight_list.item(i)
            checkbox = self.weight_list.itemWidget(item)
            checkbox.setChecked(state == Qt.Checked)

    def update_select_all_checkbox(self):
        all_checked = all(self.weight_list.itemWidget(self.weight_list.item(i)).isChecked()
                          for i in range(self.weight_list.count()))
        self.select_all_checkbox.setChecked(all_checked)

    def add_custom_weight(self):
        weight_text = self.custom_weight_input.text()
        if not weight_text.isdigit():
            QMessageBox.warning(self, "错误", "请输入有效的数字。")
            return
        weight = int(weight_text)
        if weight < 100 or weight > 900:
            QMessageBox.warning(self, "错误", "字重必须在100到900之间。")
            return
        if weight not in self.weights and weight not in self.custom_weights:
            self.custom_weights.append(weight)
            self.update_weight_list()
            self.custom_weight_input.clear()
        else:
            QMessageBox.warning(self, "警告", "该字重已存在。")

    def select_font(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择变量字体文件", "", "字体文件 (*.ttf *.otf)")
        if file_path:
            self.load_font(file_path)

    def load_font(self, file_path):
        try:
            varfont = TTFont(file_path)
            if 'fvar' not in varfont:
                raise ValueError("这不是一个变量字体。")
            
            self.font_path = file_path
            self.generate_button.setEnabled(True)
            self.drop_area.setText(f"已选择: {os.path.basename(file_path)}")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"加载字体失败: {str(e)}")
            self.generate_button.setEnabled(False)
            self.drop_area.setText("拖放字体文件到这里或点击选择")

    def generate_ttfs(self):
        if not self.font_path:
            QMessageBox.warning(self, "错误", "请先选择字体文件。")
            return

        selected_weights = []
        for i in range(self.weight_list.count()):
            item = self.weight_list.item(i)
            checkbox = self.weight_list.itemWidget(item)
            if checkbox.isChecked():
                selected_weights.append(int(checkbox.text()))

        if not selected_weights:
            QMessageBox.warning(self, "错误", "请选择至少一个字重。")
            return

        save_dir = QFileDialog.getExistingDirectory(self, '选择保存目录')
        if not save_dir:
            return

        base_name = os.path.splitext(os.path.basename(self.font_path))[0]

        progress = QMessageBox(QMessageBox.Information, "生成进度", "正在生成字体...", QMessageBox.Cancel)
        progress.setStandardButtons(QMessageBox.Cancel)
        progress.show()

        for i, weight in enumerate(selected_weights):
            if progress.isHidden():
                break
            try:
                varfont = TTFont(self.font_path)
                instance = instantiateVariableFont(varfont, {"wght": weight})
                
                save_path = os.path.join(save_dir, f"{base_name}-{weight}.ttf")
                instance.save(save_path)
                progress.setText(f"正在生成字体... ({i+1}/{len(selected_weights)})")
                QApplication.processEvents()
            except Exception as e:
                QMessageBox.warning(self, "错误", f"生成 {weight} 字重失败: {str(e)}")

        progress.close()
        QMessageBox.information(self, "完成", "所有选中的字重文件已生成。")

    def show_about_dialog(self):
      
        compile_date = "2024/07/28"
          
        QMessageBox.about(self, "关于", f"<b>可变体字重生成器<br>编译日期：{compile_date}<br><br> <a href='https://github.com/LANMIN-X/FontConverter_GUI/'>Github</a><br><a href='https://zfont.cn'>找字体</a>")

if __name__ == '__main__':
    # 在创建 QApplication 之前设置属性
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setStyleSheet(load_stylesheet_pyqt5())

    ex = VariableFontWeightGenerator()
    ex.show()
    sys.exit(app.exec_())
