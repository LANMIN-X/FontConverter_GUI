import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QMessageBox
from fontTools.merge import Merger
from fontTools.ttLib import TTFont

class FontMerger(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.font_files = []

    def initUI(self):
        self.layout = QVBoxLayout()

        self.select_button = QPushButton('选择字体文件', self)
        self.select_button.clicked.connect(self.openFileDialog)
        self.layout.addWidget(self.select_button)

        self.merge_button = QPushButton('合并字体文件', self)
        self.merge_button.clicked.connect(self.mergeFonts)
        self.layout.addWidget(self.merge_button)

        self.setLayout(self.layout)
        self.setWindowTitle('字体文件合并器')
        self.show()

    def openFileDialog(self):
        options = QFileDialog.Options()
        files, _ = QFileDialog.getOpenFileNames(self, '选择字体文件', '', 'Font Files (*.ttf *.otf);;All Files (*)', options=options)
        if files:
            self.font_files = files
            QMessageBox.information(self, '已选择的文件', '\n'.join(files), QMessageBox.Ok)

    def mergeFonts(self):
        if not self.font_files:
            QMessageBox.warning(self, '错误', '请先选择字体文件', QMessageBox.Ok)
            return

        try:
            merger = Merger()
            merged_font = merger.merge(self.font_files)

            save_path, _ = QFileDialog.getSaveFileName(self, '保存合并后的字体文件', '', 'Font Files (*.ttf *.otf);;All Files (*)')
            if save_path:
                merged_font.save(save_path)
                QMessageBox.information(self, '成功', f'字体文件已合并并保存到 {save_path}', QMessageBox.Ok)
        except Exception as e:
            QMessageBox.critical(self, '错误', f'合并字体文件时出错: {str(e)}', QMessageBox.Ok)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = FontMerger()
    sys.exit(app.exec_())
