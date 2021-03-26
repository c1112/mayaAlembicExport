'''
	Example built from:
		arg1(file) 		'c:/users/username/documents/maya/projects/default/scenes/test_scene_01.mb'
		arg2(command) 	'-dataFormat ogawa -file c:/users/username/documents/maya/projects/default/scenes/output.abc -root pSphere1 -worldSpace -uvWrite -writeVisibility -step 1'

	Example Usage:
		mayapy <path_to_this_script.py> <scene_file.mb|ma> <abcexport_command_string>

'''


import os,sys
import time

t0 = time.time()
# setup maya standalone
import maya.standalone
maya.standalone.initialize()

# load maya api
import maya.cmds as cmds

# pull data from cli args
scene_path = sys.argv[1]
export_command = sys.argv[2]

# print('Scene: %s'%scene_path)
# print('Command: %s'%export_command)

# load the scene
ret = cmds.file(scene_path,o=True)
print('OpenFile: %s'%ret)

# load abcexport plugin
ret = cmds.loadPlugin( 'AbcExport.mll' )
print('LoadPlugin: %s'%ret)

# run export
ret = cmds.AbcExport(j=export_command)

# check for file
abc_file = None
for s in export_command.split():
	if s.lower().endswith('.abc'):
		abc_file = s
		break

if abc_file:
	print('Size: %.2f (mb)  Date: %s   %s'%(os.path.getsize(abc_file)/100000.0, time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(os.path.getctime(abc_file))) ,abc_file ) )
else:
	print('Could not parse .abc file from args')

print('Completed in %.4f (sec)'%(time.time()-t0))