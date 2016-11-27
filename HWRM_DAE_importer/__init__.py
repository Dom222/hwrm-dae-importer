
bl_info = {
	"name": "HWRM DAE importer",
	"author": "Dom2, DKesserich",
	"version": (1, 0, 0),
	"blender": (2, 76, 0),
	"location": "File > Import-Export > Dae",
	"description": "Import HWRM DAE files",
	"category": "Import-Export",
}


if "bpy" in locals():
	print("bpy is in locals()")
	import imp
	if "import_dae" in locals():
		print("import_dae in locals(), attempting to reload...")
		imp.reload(import_dae)
	else:
		print("import_dae not in locals(), attempting to import...")
		from . import import_dae
else:
	print("bpy not in locals(), attempting to import import_dae...")
	from . import import_dae

import os
import bpy
import bpy_extras
"""
if "bpy" in locals():
	try:
		import importlib
		importlib.reload(import_dae)
		print("importlib.reload(import_dae) -- success")
	except:
		print("Tried importlib.reload(import_dae) - it failed")
		try:
			from . import import_dae
			print("from . import import_dae -- success")
		except:
			print("Tried from . import import_dae - it failed")
			import import_dae
			print("import import_dae -- success")
"""

class ImportDAE(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
	"""Import HWRM DAE"""
	bl_idname = "import_scene.dae"
	bl_label = "Import HWRM DAE"
	bl_options = {'UNDO'}

	filename_ext = ".dae"

	filter_glob = bpy.props.StringProperty(
			default="*.dae",
			options={'HIDDEN'},
			)
	files = bpy.props.CollectionProperty(
			name="File Path",
			type=bpy.types.OperatorFileListElement,
			)
	directory = bpy.props.StringProperty(
			subtype='DIR_PATH',
			)

	import_joints = bpy.props.BoolProperty(
			name="Import Joints",
			description="Import joints",
			default=True,
			)

	import_mesh = bpy.props.BoolProperty(
			name="Import Mesh",
			description="Import mesh and materials",
			default=False,
			)

	def execute(self, context):
		print("Executing HWRM DAE import")
		print(self.filepath)
		from . import import_dae # re-import, just in case!
		import_dae.ImportDAE(self.filepath)
		return {'FINISHED'}

def menu_import(self, context):
	self.layout.operator(ImportDAE.bl_idname, text="HWRM DAE (.dae)")

def register():
	bpy.utils.register_module(__name__)
	bpy.types.INFO_MT_file_import.append(menu_import)

def unregister():
	bpy.utils.unregister_module(__name__)
	bpy.types.INFO_MT_file_import.remove(menu_import)

if __name__ == "__main__":
	register()
