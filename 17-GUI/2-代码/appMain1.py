# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'FormHello.ui'
#
# Created by: PyQt5 UI code generator 5.15.2
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


import sys
from PyQt5 import QtWidgets, QtCore
from FormHello import Ui_FormHello

app = QtWidgets.QApplication(sys.argv)
baseWidget = QtWidgets.QWidget()  # 创建窗体实例

ui = Ui_FormHello()
ui.setupUi(baseWidget)  # 以baseWidget作为传递参数，创建完整窗体。这句要表的意思就是要用ui.setupUi函数对窗体baseWidget进行设置

baseWidget.show()
# _translate = QtCore.QCoreApplication.translate
# ui.LabHello.setText(_translate("FormHello", "<html><head/><body><p><span style=\" font-size:36pt;\">Hello, 被程序修改</span></p></body></html>"))
sys.exit(app.exec_())