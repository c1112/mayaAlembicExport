import sys,os

# TODO: Make this work with PyQt# PySide#, Qt
from PySide2.QtUiTools import QUiLoader
from PySide2 import QtWidgets 
from PySide2 import QtCore

def getUserDirectory():
    # implement for linux
    return os.environ.get('APPDATA')# windows

class Form(QtCore.QObject):

    def __init__(self, ui_file, parent=None, process_form_callback=None):#, get_selected_callback=None):
        #setup form trying something
        super(Form, self).__init__(parent)
        ui_file = QtCore.QFile(ui_file)
        ui_file.open(QtCore.QFile.ReadOnly)

        loader = QUiLoader()
        self.window = loader.load(ui_file)
        ui_file.close()
        #################################
        # Callbacks
        self.process_form_callback = process_form_callback
        # self.get_selected_callback = get_selected_callback ** Not implemented yet

        # Globals
        self.ftoken     = self.window.line_ftoken
        self.stepsize   = self.window.cbox_stepsize
        self.duration   = self.window.cbox_duration
        self.runloc     = self.window.cbox_runloc
        self.to_export  = self.window.list_toexport
        self.to_attrs   = self.window.list_attrs
        self.attr       = self.window.line_attr

        self.file_export_path   = ''# look this up from settings

        # Buttons
        btn_export      = self.window.btn_export
        btn_export.clicked.connect(self.export_handler)

        btn_cancel      = self.window.btn_cancel
        btn_cancel.clicked.connect(self.close_handler)

        btn_addattr     = self.window.btn_addattr
        btn_addattr.clicked.connect(self.addattr_handler)

        btn_removeattr  = self.window.btn_removeattr
        btn_removeattr.clicked.connect(self.removeattr_handler)

        btn_export_path  = self.window.btn_export_path
        btn_export_path.clicked.connect(self.set_file_export_path)

        # Misc signals
        self.attr.returnPressed.connect(self.addattr_handler)

        #Run defaults
        self.set_defaults()

        #Show window
        self.window.show()

        # get the file_export_path
        self.file_export_path = getUserDirectory()
        if self.file_export_path:
            self.file_export_path = self.file_export_path.replace('\\','/')
        # - set the file_export_path to settings 
        self.update_btn_export_name()


    def set_defaults(self):
        ui = self.window

        #set checkboxes
        checkboxes = [  ui.checkBox_uvWrite_abcopt,
                        ui.checkBox_worldSpace_abcopt,
                        ui.checkBox_writeVisibility_abcopt
                    ]
        for cbox in checkboxes:
            cbox.setChecked(True)

        # set token
        self.ftoken.setText("output")
        # add stepsizes
        self.stepsize.addItems(['1', '1/2', '1/4', '1/8', '1/16'])
        # add duration
        self.duration.addItems(['Time Slider', 'Current Frame'])
        # add run location
        self.runloc.addItems(['Local', 'Farm'])
        # add defualt item to list widget
        item = QtWidgets.QListWidgetItem("Selected Items")
        self.to_export.addItem(item)
        self.to_export.setCurrentItem(item)

    def update_btn_export_name(self):
        self.window.btn_export_path.setText(('%s'%self.file_export_path).replace('\\','/'))

    def set_file_export_path(self,default_directory=None):
        if not default_directory:
            default_directory = self.file_export_path


        default_directory = self.file_export_path.replace('\\','/')
        print('Export file path: %s'%self.file_export_path)
        self.file_export_path = QtWidgets.QFileDialog.getExistingDirectory(None, caption='Set Export Directory', dir=default_directory)
        
        if not self.file_export_path:
            self.file_export_path = getUserDirectory()

        self.file_export_path = self.file_export_path.replace('\\','/')
        self.update_btn_export_name()

    # TODO: make host agnostic
    def build_stepsize(self):
        stepsize = self.stepsize.currentText()
        data = {"1":"1", "1/2":"0.5", "1/4":"0.25", "1/8":"0.125", "1/16":"0.0625"}
        return ["-step", data[stepsize]]

    # TODO: make host agnostic
    def build_attrs(self):
        '''Build out the string required for maya '''
        attr_list = []
        for i in range(self.to_attrs.count()):
            attr_list.append(self.to_attrs.item(i).text())

        attrs = []
        for attr in attr_list:
            attrs += ['-attr',attr]
        return attrs

    # TODO: make host agnostic
    def build_checkboxes(self):
        checkboxes = self.window.findChildren(QtWidgets.QCheckBox, QtCore.QRegExp("_abcopt$"))
        values = []
        for x in checkboxes:
            if x.isChecked():
                tmp = x.objectName().split('_')
                values.append("-%s" % tmp[1])

        return values

    # TODO: make host agnostic
    def build_maya_export(self):
        return ['-root', self.to_export.currentItem().text()]

    # TODO: make host agnostic
    def build_fileout(self):
        token = self.ftoken.text()
        return ['-file', '%s/%s.abc' % (self.file_export_path,token)]

    # TODO: make host agnostic
    def build_framerange(self):
        ret = []
        range = self.duration.currentText()
        if range == 'Time Slider':
            ret = ['-frameRange','1001','1001']
        if range == 'Current Frame':
            ret = ['-frameRange','1002','1002']
        return ret

    # TODO: make host agnostic
    def build_command(self):
        cmd             = ['AbcExport','-j']
        cmd            += self.build_framerange()
        cmd            += ["-dataFormat", "ogawa"]
        cmd            += self.build_fileout()
        cmd            += self.build_maya_export()
        cmd            += self.build_checkboxes()
        cmd            += self.build_attrs()
        cmd            += self.build_stepsize()

        return cmd


    def export_handler(self):
        ''' The handler that is executed when the execute button is pressed '''
        command_list    = self.build_command()
        runloc          = self.runloc.currentText()

        errors = None
        if runloc == 'Local':
            command = '%s %s'%(command_list[0],command_list[1]) + ' "%s"'%(' '.join([str(s) for s in command_list[2:]]))
            print("run local")
            if self.process_form_callback:
                errors = self.process_form_callback(command_list, run_on='local')
        elif runloc == 'Farm':
            print("run farm")
            if self.process_form_callback:
                errors = self.process_form_callback(command_list, run_on='farm')

        if errors:
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.setText('Export errors were found')
            msg.setInformativeText('\n'.join(errors))
            msg.setWindowTitle("%d Errors"%len(errors))
            msg.exec_()

            # return and do not close window
            return len(errors)
        
        self.close_handler()

    def close_handler(self):
        self.window.close()

    def addattr_handler(self):
        text = self.attr.text()
        if text != "":
            self.attr.clear()
            self.to_attrs.addItem(QtWidgets.QListWidgetItem(text))

    def removeattr_handler(self):
        current_item = self.to_attrs.currentRow()
        self.to_attrs.takeItem(current_item)

#######################  CALLBACKS  #########################################
# this is an example of the callback in the host application
# your host method should contain 2 args command_list and run_on
# you will get back a list of command values
# parse it into your host app abc excport format and handle execution
# return 0 for success and list of errors for fail
def example_process_form_callback(command_list, run_on):
    # build for farm ** Not Tested
    if run_on=='farm':
        return ['Test error','second little problem','another thing happened','oh no!']
    command = '%s %s'%(command_list[0],command_list[1]) + ' "%s"'%(' '.join([str(s) for s in command_list[2:]]))
    # build for local ** Not Tested
    print('%s: %s'%(run_on,command))
    return 0

# def example_get_selected_callback(command_list, run_on):
#     return selected items to display in dialog
#######################  END CALLBACKS  #########################################

def main(args):
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(args)
    form = Form('alembicexporter.ui', process_form_callback=example_process_form_callback)
    return app.exec_()

if __name__ == '__main__':
    args = sys.argv[1:]
    args += [
    ]
    sys.exit(main(args))
