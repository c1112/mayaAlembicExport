import sys,os
import time

# TODO: Make this work with PyQt# PySide#, Qt
from PySide2.QtUiTools import QUiLoader
from PySide2 import QtWidgets 
from PySide2 import QtCore

def getUserDirectory():
    # implement for linux
    return os.environ.get('APPDATA')# windows


UI_FILEPATH = os.path.join(os.path.dirname(__file__),'alembicexporter.ui').replace('\\','/')

DEFAULT_STEPSIZES       =  {"1":"1", "1/2":"0.5", "1/4":"0.25", "1/8":"0.125", "1/16":"0.0625"}
DEFAULT_PROC_LOCATION   = ['Farm','Local']


class Form(QtCore.QObject):

    def __init__(self, 
                        ui_file, parent=None, 
                        file_export_path=None, 
                        process_form_callback=None, 
                        get_framerange_callback=None, 
                        item_type_callback=None,
                        process_location_list=None, 
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
        self.process_location_list      = process_location_list or DEFAULT_PROC_LOCATION
        # if not self.item_type_callback:
        #     self.item_type_callback = {'Selected':{'callback':lambda x:['item_%d'%i for i in range(5)]}}

        # if not self.get_framerange_callback:
        #     self.get_framerange_callback = {
        #                                     'Time Slider':{ 'callback':lambda x: (1001,1100) },
        #                                     'Current Frame':{ 'callback':lambda x: (1001,1001) },
        #                                     }
        
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

        self.cmbo_item_types  = self.window.cmbo_item_types
        self.cmbo_item_types.currentTextChanged.connect(self.update_cmbo_item_types)



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
        self.stepsize.addItems(list(DEFAULT_STEPSIZES.keys()))
        # add duration
        # self.duration.addItems(['Time Slider', 'Current Frame'])

        if self.get_framerange_callback:
            self.duration.clear()
                
            for key in self.get_framerange_callback:
                self.duration.addItem(key)


        # add run location
        self.runloc.addItems(self.process_location_list)
        # add defualt item to list widget

        # clear the export list
        self.to_export.clear()
        # push types to combo
        for key in self.item_type_callback:
            self.window.cmbo_item_types.addItem(key)

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
    def get_stepsize(self):
        stepsize = self.stepsize.currentText()
        return DEFAULT_STEPSIZES[stepsize] # can modify this to be a tool variable

    # TODO: make host agnostic
    def get_attributes(self):
        '''Get standardized data for host to convert'''
        attr_list = []
        for i in range(self.to_attrs.count()):
            attr_list.append(self.to_attrs.item(i).text())

        return attr_list

    def get_advanced_flags(self):
        checkboxes = self.window.findChildren(QtWidgets.QCheckBox, QtCore.QRegExp("_abcopt$"))
        values = []
        for x in checkboxes:
            if x.isChecked():
                tmp = x.objectName().split('_')
                values.append("-%s" % tmp[1])

        return values

    def get_export_items(self):
        ret = {'selected_items':[],'key':self.cmbo_item_types.currentText()}#,'items':self.to_export.items()}
        for item in self.to_export.selectedItems():
            ret['selected_items'].append(item.text())
        return ret

    def get_fileout(self):
        return '%s/%s.abc' % (self.file_export_path,self.ftoken.text())

    def get_framerange(self):
        ret = []
        frameValue = self.duration.currentText()
        if self.get_framerange_callback:
            cb = self.get_framerange_callback.get(frameValue,{}).get('callback')
            if cb:
                ret += cb(frameValue)

        return ret

    def get_process_location(self):
        return self.runloc.currentText()

    # TODO: make host agnostic
    def get_command_keyvals(self):
        cmd             = {
        'framerange':self.get_framerange(),
        'export_data':self.get_export_items(),
        'flags':self.get_advanced_flags(),
        'attributes':self.get_attributes(),
        'file_out':self.get_fileout(),
        'stepsize': self.get_stepsize(),
        'process_location':self.get_process_location(),
        }

        return cmd


    def export_handler(self):
        ''' The handler that is executed when the execute button is pressed '''
        command_kvs    = self.get_command_keyvals()
        runloc          = self.runloc.currentText()

        errors = None
        if self.process_form_callback:
            errors = self.process_form_callback(command_kvs)

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

    # load acbExport plugin
    load_plugin_result = cmds.loadPlugin( 'AbcExport.mll' )
    print('LoadPlugin: AbcExport: %s'%load_plugin_result)
    maya_item_type_callback = {'Selected':{'callback':lambda x:['%s'%i for i in cmds.ls(selection=1)]},
                                    'Sets':{'callback':lambda x:['%s'%i for i in cmds.ls(sets=1)]},
                                    # 'All':{'callback':lambda x:['%s'%i for i in cmds.ls()]},
                                    # 'Cameras':{'callback':lambda x:['camera_%d'%i for i in range(4)]},
                                    # 'Geometry':{'callback':lambda x:['geo_%d'%i for i in range(20)]},
                                        }

    # callback for getting frame range options
    start           = cmds.playbackOptions( q=1, min=True )
    end             = cmds.playbackOptions( q=1, max=True )
    frame_range     = [start, end]

    current_frame   = cmds.currentTime(q=1)
    maya_frame_range_callback = {
                            'Time Slider':{ 'callback':lambda x: frame_range },
                            'Current Frame':{ 'callback':lambda x: (current_frame,current_frame) },
    }

    def maya_process_form_callback(command_kvs):

        # dump info to console
        print('='*80)
        for k,v in command_kvs.items():
            print('[%s] = %s'%(k,str(v)))
        print('='*80)

        t0 = time.time()
        export_command = ''

        # lets handle the process_location later (deadline or local)
        for flag in command_kvs.get('flags',[]):
            export_command += ' %s'%(flag)
        for attr in command_kvs.get('attributes',[]):
            export_command += ' -attr "%s"'%attr
        if 'framerange' in command_kvs:
            export_command += ' -framerange %s %s'%(command_kvs['framerange'][0],command_kvs['framerange'][1])
        if 'file_out' in command_kvs:
            export_command += ' -file "%s"'%command_kvs['file_out']
        if 'stepsize' in command_kvs:
            export_command += ' -step "%s"'%command_kvs['stepsize']
        if 'export_data' in command_kvs:
            xport_items = []
            for item in command_kvs['export_data'].get('selected_items'):
                if command_kvs['export_data']['key'] in ('Sets',):
                    for i in cmds.sets( item, query=1):
                        if i not in xport_items:
                            xport_items.append('%s'%i)
                else:
                    xport_items.append('%s'%item)
            for item in xport_items:       
                export_command += ' -root "%s"'%item # may need to get full path here
        export_command = str(export_command).strip()

        # print('command_kvs: ', command_kvs)
        print('export_command: ', export_command)
        # run export
        ret = cmds.AbcExport(j=export_command)
        # check for file
        abc_file = command_kvs.get('file_out')
        # for s in export_command.split():
        #     if s.lower().endswith('.abc'):
        #         abc_file = s
        #         break

        if abc_file:
            print('Size: %.2f (mb)  Date: %s   %s'%(os.path.getsize(abc_file)/100000.0, time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(os.path.getctime(abc_file))) ,abc_file ) )
        else:
            print('Could not parse .abc file from args')

        print('Completed in %.4f (sec)'%(time.time()-t0))


        # build for farm ** Not Tested
        # if run_on=='farm':
        #     return ['Test error','second little problem','another thing happened','oh no!']
        # command = '%s %s'%(command_list[0],command_list[1]) + ' "%s"'%(' '.join([str(s) for s in command_list[2:]]))
        # # build for local ** Not Tested
        # print('%s: %s'%(run_on,command))
        return 0


    # callback for getting selected item type

    # return maya form
    maya_form = Form( UI_FILEPATH,#'alembicexporter.ui', 
                process_form_callback=maya_process_form_callback,
                item_type_callback=maya_item_type_callback,
                get_framerange_callback=maya_frame_range_callback,
                file_export_path='H:/DEV/CBFX',

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
