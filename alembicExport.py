import sys,os

# TODO: Make this work with PyQt# PySide#, Qt
from PySide2.QtUiTools import QUiLoader
from PySide2 import QtWidgets 
from PySide2 import QtCore

def getUserDirectory():
    # implement for linux
    return os.environ.get('APPDATA')# windows


UI_FILEPATH = os.path.join(os.path.dirname(__file__),'alembicexporter.ui').replace('\\','/')

class Form(QtCore.QObject):

    def __init__(self, 
                        ui_file, parent=None, 
                        file_export_path=None, 
                        process_form_callback=None, 
                        get_framerange_callback=None, 
                        item_type_callback=None, 
                        # lock_export_path=None,
                        ):#, get_selected_callback=None):
        #setup form trying something
        super(Form, self).__init__(parent)
        ui_file = QtCore.QFile(ui_file)
        ui_file.open(QtCore.QFile.ReadOnly)

        loader = QUiLoader()
        self.window = loader.load(ui_file)
        ui_file.close()
        #################################
        # Callbacks
        self.process_form_callback      = process_form_callback
        self.get_framerange_callback    = get_framerange_callback
        self.item_type_callback         = item_type_callback
        if not self.item_type_callback:
            self.item_type_callback = {'Selected':{'callback':lambda x:['item_%d'%i for i in range(5)]}}

        if not self.get_framerange_callback:
            self.get_framerange_callback = {
                                            'Time Slider':{ 'callback':lambda x: (1001,1100) },
                                            'Current Frame':{ 'callback':lambda x: (1001,1001) },
                                            }
        
        # self.get_selected_callback = get_selected_callback ** Not implemented yet

        # Globals
        self.ftoken     = self.window.line_ftoken
        self.stepsize   = self.window.cbox_stepsize
        self.duration   = self.window.cbox_duration
        self.runloc     = self.window.cbox_runloc
        self.to_export  = self.window.list_toexport
        self.to_attrs   = self.window.list_attrs
        self.attr       = self.window.line_attr

        # self.window.keyPressedEvent = self.keyPressEvent
        # self.file_export_path   = file_export_path or ''# look this up from settings

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

        if file_export_path:
            btn_export_path.setEnabled(0)
            btn_export_path.setToolTip('Value was set by pipeline. Cannot be changed in this instance')
        # item types and filters 
        txt_filter_value  = self.window.txt_filter_value
        txt_filter_value.textChanged[str].connect(self.update_txt_filter_value)

        cmbo_item_types  = self.window.cmbo_item_types
        cmbo_item_types.currentTextChanged.connect(self.update_cmbo_item_types)



        # Misc signals
        self.attr.returnPressed.connect(self.addattr_handler)

        #Run defaults
        self.set_defaults()

        #Show window
        # self.window.show()

        # get the file_export_path
        self.file_export_path = file_export_path or getUserDirectory()
        if self.file_export_path:
            self.file_export_path = self.file_export_path.replace('\\','/')
        # - set the file_export_path to settings 
        self.update_btn_export_name()

    def keyPressEvent(self,evt):
        print('key: %s'%evt.key())

    def set_file_export_path_readonly(self,val):
        val = True if val else False
        self.window.btn_export_path.setEnabled(not val)    

    def update_cmbo_item_types(self,val):
        print('cmbo:val: %s'%val)
        cb = self.item_type_callback.get(val,{}).get('callback')
        if cb:
            self.to_export.clear()
            for item in cb(val):
                try:
                    self.to_export.addItem(item)
                    # print(' -> %s'%item)
                except:
                    pass

    def update_txt_filter_value(self,val):
        print('filter:val: %s'%val)

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
        # self.duration.addItems(['Time Slider', 'Current Frame'])

        if self.get_framerange_callback:
            self.duration.clear()
                
            for key in self.get_framerange_callback:
                self.duration.addItem(key)


        # add run location
        self.runloc.addItems(['Local', 'Farm'])
        # add defualt item to list widget

        # clear the export list
        self.to_export.clear()
        # push types to combo
        for key in self.item_type_callback:
            self.window.cmbo_item_types.addItem(key)
        # item = QtWidgets.QListWidgetItem("Selected Items")
        # self.to_export.addItem(item)
        # self.to_export.setCurrentItem(item)

    def update_btn_export_name(self):
        # self.window.btn_export_path.setText(('%s'%self.file_export_path).replace('\\','/'))
        self.window.lbl_file_export_value.setText(('%s'%self.file_export_path).replace('\\','/'))

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
        ret = []
        for item in self.to_export.selectedItems():
            ret += ['-root',item.text()]
        return ret#['-root', self.to_export.currentItem().text()]

    # TODO: make host agnostic
    def build_fileout(self):
        token = self.ftoken.text()
        return ['-file', '%s/%s.abc' % (self.file_export_path,token)]

    # TODO: make host agnostic
    def build_framerange(self):
        ret = []
        frameValue = self.duration.currentText()
        if self.get_framerange_callback:
            cb = self.get_framerange_callback.get(frameValue,{}).get('callback')
            if cb:
                ret += cb(frameValue)

        # if range == 'Time Slider':
        #     ret = ['-frameRange','1001','1001']
        # if range == 'Current Frame':
        #     ret = ['-frameRange','1002','1002']
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

# def example_item_type_callback(key):
# def example_get_selected_callback(command_list, run_on):
#     return selected items to display in dialog

def get_sample_form(args=None):
    sample_form = Form( UI_FILEPATH,#'alembicexporter.ui', 
                process_form_callback=example_process_form_callback,
                item_type_callback={'Selected':{'callback':lambda x:['item_%d'%i for i in range(7)]},
                                    'Sets':{'callback':lambda x:['set_%d'%i for i in range(4)]},
                                    # 'Cameras':{'callback':lambda x:['camera_%d'%i for i in range(4)]},
                                    # 'Geometry':{'callback':lambda x:['geo_%d'%i for i in range(20)]},
                                        },
                file_export_path='d:/dev/data',

                )
    return sample_form

def get_maya_form(args=None):
    # setup maya standalone
    # import maya.standalone
    # maya.standalone.initialize()

    # load maya api
    from maya import cmds

    # callback for getting frame range options
    start           = cmds.playbackOptions( q=1, min=True )
    end             = cmds.playbackOptions( q=1, max=True )
    frame_range     = [start, end]

    current_frame   = cmds.currentTime(q=1)
    frame_range_callback = {
                            'Time Slider':{ 'callback':lambda x: frame_range },
                            'Current Frame':{ 'callback':lambda x: (current_frame,current_frame) },
    }
    # callback for getting selected item type

    # return maya form
    maya_form = Form( UI_FILEPATH,#'alembicexporter.ui', 
                process_form_callback=example_process_form_callback,
                item_type_callback={'Selected':{'callback':lambda x:['item_%d'%i for i in range(7)]},
                                    'Sets':{'callback':lambda x:['set_%d'%i for i in range(4)]},
                                    # 'Cameras':{'callback':lambda x:['camera_%d'%i for i in range(4)]},
                                    # 'Geometry':{'callback':lambda x:['geo_%d'%i for i in range(20)]},
                                        },
                get_framerange_callback=frame_range_callback,
                file_export_path='d:/dev/data',

                )
    return maya_form

#######################  END CALLBACKS  #########################################

def main(args):
    # grab app instance or create one
    ret = 0

    inst = QtWidgets.QApplication.instance()
    app  = inst or QtWidgets.QApplication(args)


    form = None

    # not best practice in memory/dev 
    if 'maya' in args:
        form = get_maya_form(args)
    if 'sample' in args:
        form = get_sample_form(args)

    if form:
        form.window.show()#exec_()

    # trouble sho0ting window not staying open in maya
    if not inst:
        ret = app.exec_()

    return ret

if __name__ == '__main__':
    args = sys.argv[1:]
    args += [ 
        #'maya',
        'sample',
    ]
    sys.exit(main(args))
