import sys

from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QApplication, QPushButton, QLineEdit, QListWidgetItem, QCheckBox
from PySide2.QtCore import QFile, QObject, QCoreApplication, QRegExp

class Form(QObject):

    def __init__(self, ui_file, parent=None):
        #setup form
        super(Form, self).__init__(parent)
        ui_file = QFile(ui_file)
        ui_file.open(QFile.ReadOnly)

        loader = QUiLoader()
        self.window = loader.load(ui_file)
        ui_file.close()
        #################################

        # Globals
        self.ftoken = self.window.line_ftoken
        self.stepsize = self.window.cbox_stepsize
        self.duration = self.window.cbox_duration
        self.runloc = self.window.cbox_runloc
        self.to_export = self.window.list_toexport
        self.to_attrs = self.window.list_attrs
        self.attr = self.window.line_attr

        # Buttons
        btn_export = self.window.btn_export
        btn_export.clicked.connect(self.export_handler)

        btn_cancel = self.window.btn_cancel
        btn_cancel.clicked.connect(self.cancel_handler)

        btn_addattr = self.window.btn_addattr
        btn_addattr.clicked.connect(self.addattr_handler)

        btn_removeattr = self.window.btn_removeattr
        btn_removeattr.clicked.connect(self.removeattr_handler)

        # Misc signals
        self.attr.returnPressed.connect(self.addattr_handler)

        #Run defaults
        self.set_defaults()

        #Show window
        self.window.show()

    def set_defaults(self):
        ui = self.window

        #set checkboxes
        checkboxes = [  ui.checkBox_uvWrite_abcopt,
                        ui.checkBox_worldSpace_abcopt,
                        ui.checkBox_writeVisibility_abcopt
                    ]
        for cbox in checkboxes:
            cbox.setChecked(True)

        #set token
        self.ftoken.setText("output")
        #add stepsizes
        self.stepsize.addItems(['1', '1/2', '1/4', '1/8', '1/16'])
        #add duration
        self.duration.addItems(['Time Slider', 'Current Frame'])
        #add run location
        self.runloc.addItems(['Local', 'Farm'])
        #add defualt item to list widget
        item = QListWidgetItem("Selected Items")
        self.to_export.addItem(item)
        self.to_export.setCurrentItem(item)

    def build_stepsize(self):
        stepsize = self.stepsize.currentText()
        data = {"1":"1", "1/2":"0.5", "1/4":"0.25", "1/8":"0.125", "1/16":"0.0625"}
        return "-step %s" % data[stepsize]

    def build_attrs(self):
        ''' Build out the string required for maya '''
        attr_list = []
        for i in range(self.to_attrs.count()):
            attr_list.append(self.to_attrs.item(i).text())

        attrs = ' '.join(['-attr ' + s for s in attr_list])

        return attrs

    def build_checkboxes(self):
        checkboxes = self.window.findChildren(QCheckBox, QRegExp("_abcopt$"))
        values = []
        for x in checkboxes:
            if x.isChecked():
                tmp = x.objectName().split('_')
                values.append("-%s" % tmp[1])

        out = ' '.join(values)
        return out

    def build_maya_export(self):
        return "-root %s" % self.to_export.currentItem().text()

    def build_fileout(self):
        token = self.ftoken.text()
        return "-file C:/Users/brendan.fitzgerald/Desktop/%s.abc" % token

    def build_framerange(self):
        range = self.duration.currentText()
        if range == 'Time Slider':
            return "-frameRange %s %s" % ("1001", "1001")
        if range == 'Current Frame':
            return "-frameRange %s %s" % ("1002", "1002")

    def build_command(self):
        base_cmd = "AbcExport -j"
        frame_range = self.build_framerange()
        data_format = "-dataFormat ogawa"
        file = self.build_fileout()
        selection = self.build_maya_export()
        checkboxes = self.build_checkboxes()
        attrs = self.build_attrs()
        stepsize = self.build_stepsize()

        compiled_cmd = '%s "%s %s %s %s %s %s %s"' % (base_cmd, frame_range, stepsize, attrs, checkboxes, data_format, selection, file)
        return compiled_cmd


    def export_handler(self):
        ''' The handler that is executed when the execute button is pressed '''
        command = self.build_command()
        runloc = self.runloc.currentText()

        if runloc == 'Local':
            print("run local")
            print(self.build_command())
        elif runloc == 'Farm':
            print("run farm")
            print(self.build_command())

    def cancel_handler(self):
        QCoreApplication.instance().quit()

    def addattr_handler(self):
        text = self.attr.text()
        if text != "":
            self.attr.clear()
            self.to_attrs.addItem(QListWidgetItem(text))

    def removeattr_handler(self):
        current_item = self.to_attrs.currentRow()
        self.to_attrs.takeItem(current_item)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    form = Form('alembicexporter.ui')
    sys.exit(app.exec_())
