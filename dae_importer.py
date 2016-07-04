# HWRM DAE Importer for Blender
#
# To do:
# - Handle nav names to match better collada exporter (currently truncated)
# - Get image file names & materials from the DAE
# - Get UVs from the DAE
# - Get animations from the DAE
# - Make a dialogue box for the file import

import bpy
import xml.etree.ElementTree as ET

context = bpy.context

bpy.ops.object.select_all(action='TOGGLE')
bpy.ops.object.delete(use_global=False)
bpy.ops.object.select_all(action='TOGGLE')
bpy.ops.object.delete(use_global=False)

print("--------------------------------------------------------------------------------")
print("DAE import script")
print("--------------------------------------------------------------------------------")

def MakeJnt(jnt_name,jnt_locn,jnt_rotn,jnt_context):
	print("Creating joint" + jnt_name)
	this_jnt = bpy.data.objects.new(jnt_name, None)
	jnt_context.scene.objects.link(this_jnt)
	pi = 3.14159265359
	this_jnt.rotation_euler.x = joint_rotation[0] * (pi/180.0)
	this_jnt.rotation_euler.y = joint_rotation[1] * (pi/180.0)
	this_jnt.rotation_euler.z = joint_rotation[2] * (pi/180.0)
	this_jnt.location.x = float(jnt_locn[0])
	this_jnt.location.y = float(jnt_locn[1])
	this_jnt.location.z = float(jnt_locn[2])
	return this_jnt

def CheckForChildren(node,context):
	for item in node:
		if "node" in item.tag:
			if bpy.data.objects.get(item.attrib["name"][0:63]) is None:
				print(item.attrib["name"] + " is a child of " + node.attrib["name"])
				print(item.attrib["name"] + " does not exist...")
			else:
				child = context.scene.objects[item.attrib["name"][0:63]]
				parent = context.scene.objects[node.attrib["name"][0:63]]
				child.parent = parent
				CheckForChildren(item,context) # check for next generation?

def CreateMeshFromData(name,origin,verts,faces):
	# Create mesh and object
	me = bpy.data.meshes.new(name)
	ob = bpy.data.objects.new(name, me)
	ob.location = origin
	ob.show_name = True
	
	# Link object to scene and make active
	scn = bpy.context.scene
	scn.objects.link(ob)
	scn.objects.active = ob
	ob.select = True
	
	# Create mesh from given verts, faces.
	me.from_pydata(verts, [], faces)
	# Update mesh with new data
	me.update() 
	return ob

DAEpath = "C:/Program Files (x86)/Steam/steamapps/workshop/content/244160/403557412/Kad_Swarmer/"
DAEfile = "Kad_Swarmer.DAE"

#DAEpath = "C:/Program Files (x86)/Steam/steamapps/workshop/content/244160/403557412/Tur_P1Mothership/"
#DAEfile = "Tur_P1Mothership.DAE"

################################################################################
################################## XML parsing #################################
################################################################################

tree = ET.parse(DAEpath+DAEfile)
root = tree.getroot()

print(" ")
print("CREATING JOINTS")
print(" ")

# Create joints
for joint in root.iter("{http://www.collada.org/2005/11/COLLADASchema}node"): # find all <node> in the file
	# Joint name
	joint_name = joint.attrib["name"]
	print("")
	# Joint location
	joint_location = joint.find("{http://www.collada.org/2005/11/COLLADASchema}translate")
	if joint_location == None:
		joint_location = ['0','0','0'] # If there is no translation specified, default to 0,0,0
	else:
		joint_location = joint_location.text.split()
	# Joint rotation
	joint_rotationX = 0.0
	joint_rotationY = 0.0
	joint_rotationZ = 0.0
	for rot in joint:
		print(rot)
		if "rotate" in rot.tag:
			if "rotateX" in rot.attrib["sid"]:
				joint_rotationX = float(rot.text.split()[3])
			elif "rotateY" in rot.attrib["sid"]:
				joint_rotationY = float(rot.text.split()[3])
			elif "rotateZ" in rot.attrib["sid"]:
				joint_rotationZ = float(rot.text.split()[3])
	joint_rotation = [joint_rotationX,joint_rotationY,joint_rotationZ]
	# Joint or mesh?
	is_joint = True
	for item in joint:
		if "instance_geometry" in item.tag:
			print("this is a mesh:" + item.attrib["url"])
			is_joint = False
	# If this is a joint, make it!
	if is_joint:
		MakeJnt(joint_name, joint_location,joint_rotation,context)

print(" ")
print("CREATING MESHES")
print(" ")

# Create meshes:
for geom in root.iter("{http://www.collada.org/2005/11/COLLADASchema}geometry"): # find all <geometry> in the file
	print("Found <geometry> " + geom.attrib["name"])
	for mesh in geom.iter("{http://www.collada.org/2005/11/COLLADASchema}mesh"): # find all <mesh> in the <geometry>
		print("Found <mesh> " + mesh.tag)
		# Mesh vertices
		for array in mesh.iter("{http://www.collada.org/2005/11/COLLADASchema}float_array"): # find all <float_array> in the <mesh>
			if "POSITION" in array.attrib["id"]:
				print("Found position array")
				#print(array.text)
				vertex_data = array.text.split()
				verts = []
				coord = 0
				this_vertex_coords = []
				for v in vertex_data:
					coord = coord + 1
					this_vertex_coords.append(float(v))
					if coord == 3:
						verts.append(this_vertex_coords)
						coord = 0
						this_vertex_coords = []
			elif "Normal0" in array.attrib["id"]:
				print("Found normal array")
		# Mesh triangles
		trias = []
		for tria in mesh.iter("{http://www.collada.org/2005/11/COLLADASchema}triangles"): # find all <triangles> in the <mesh>
			offset_per_vertex = -1
			for inp in tria.iter("{http://www.collada.org/2005/11/COLLADASchema}input"): # find all <input> in the <triangles>
				#print("input: " + inp.attrib["semantic"] + " = " + inp.attrib["offset"])
				if "VERTEX" in inp.attrib["semantic"]:
					tria_vertex_offset = int(inp.attrib["offset"])
				offset_per_vertex = offset_per_vertex + 1
			#print("offset_per_vertex = " + str(offset_per_vertex))
			for p in tria.iter("{http://www.collada.org/2005/11/COLLADASchema}p"): # find all <p> in the <triangles>
				print("Found triangles")
				if p.text:
					tria_data = p.text.split()
					this_offset = 0
					this_vertex = 1
					this_tria_verts = []
					for i in range(0, len(tria_data)):
						if this_offset == tria_vertex_offset:
							this_tria_verts.append(int(tria_data[i]))
						elif this_offset == offset_per_vertex: # if this is the last value in the vertex
							if this_vertex == 3:
								# triangle definition complete
								trias.append(this_tria_verts)
								this_offset = -1 # this will be bumped up to 0 by the last statement in the for loop
								this_vertex = 1
								this_tria_verts = []
							else:
								# triangle definition not complete, move to next vertex
								this_vertex = this_vertex + 1
								this_offset = -1
						this_offset = this_offset + 1
		# Make a mesh!
		origin = (0.0,0.0,0.0)
		CreateMeshFromData(geom.attrib["name"].rstrip("Mesh"),origin,verts,trias)

print(" ")
print("SORTING HIERARCHY")
print(" ")

# Sort out hierarchy
for child in root:
	if "library_visual_scenes" in child.tag:
		for grandchild in child:
			if "visual_scene" in grandchild.tag:
				for node in grandchild:
					if "node" in node.tag:
						CheckForChildren(node,context)

print(" ")
print("CREATING MATERIALS")
print(" ")

image_library = {} # dict of images, each refers to a file

for image in root.iter("{http://www.collada.org/2005/11/COLLADASchema}image"): # find all <image> in the file
	print("Found image: " + image.attrib["name"])
	print("Found image: " + image.attrib["id"])
	for f in image:
		print(f.text)
		IMGfile = f.text.lstrip("file://")
		image_library[image.attrib["id"]] = IMGfile

effects_library = {} # dict of "effects", each refers to one or more images

for effect in root.iter("{http://www.collada.org/2005/11/COLLADASchema}effect"): # find all <effect> in the file
	print("-------------------------")
	print("Found effect: " + effect.attrib["id"])
	effects_library[effect.attrib["id"]] = {}
	for emission in effect.iter("{http://www.collada.org/2005/11/COLLADASchema}emission"): # find all <emission> in the <effect>
		try:
			glow_img = emission.find("{http://www.collada.org/2005/11/COLLADASchema}texture").attrib["texture"]
		except:
			print("No GLOW found")
			glow_img = None
		else:
			print("has emission: " + str(glow_img))
		effects_library[effect.attrib["id"]]["GLOW"] = glow_img
	for diffuse in effect.iter("{http://www.collada.org/2005/11/COLLADASchema}diffuse"): # find all <diffuse> in the <effect>
		try:
			diff_img = diffuse.find("{http://www.collada.org/2005/11/COLLADASchema}texture").attrib["texture"]
		except:
			print("No DIFF found")
			diff_img = None
		else:
			print("has diffuse: " + str(diff_img))
		effects_library[effect.attrib["id"]]["DIFF"] = diff_img
	for specular in effect.iter("{http://www.collada.org/2005/11/COLLADASchema}specular"): # find all <specular> in the <effect>
		try:
			spec_img = specular.find("{http://www.collada.org/2005/11/COLLADASchema}texture").attrib["texture"]
		except:
			print("No SPEC found")
			spec_img = None
		else:
			print("has specular: " + str(spec_img))
		effects_library[effect.attrib["id"]]["SPEC"] = spec_img

material_library = {} # dict of materials, each refers to an effect

for material in root.iter("{http://www.collada.org/2005/11/COLLADASchema}material"): # find all <material> in the file
	this_fx = material.find("{http://www.collada.org/2005/11/COLLADASchema}instance_effect").attrib["url"]
	mat = material.attrib["id"]
	print("Found material: " + str(mat) + ", refers to effect: " + str(this_fx))
	material_library[mat] = this_fx

# for each instance geometry, sort out the materials:

print("----------------------------------------")
print("Checking meshes for materials")
print("----------------------------------------")

for node in root.iter("{http://www.collada.org/2005/11/COLLADASchema}node"): # find all <node> in the file
	if node.find("{http://www.collada.org/2005/11/COLLADASchema}instance_geometry"): # if this node has an <instance_geometry>
		print("")
		print(node.attrib["name"] + " is a mesh...")
		ig = node.find("{http://www.collada.org/2005/11/COLLADASchema}instance_geometry")
		for im in ig.iter("{http://www.collada.org/2005/11/COLLADASchema}instance_material"): # find all <instance_material> within the <instance_geometry>
			print("--" + im.attrib["symbol"])
			# need to use this to actually create some materials:
			this_material = im.attrib["symbol"]
			this_effect = material_library[this_material].lstrip("#")
			print("----" + this_effect)
			this_DIFF = effects_library[this_effect]["DIFF"]
			this_GLOW = effects_library[this_effect]["GLOW"]
			this_SPEC = effects_library[this_effect]["SPEC"]
			print("------" + str(this_DIFF))
			if this_DIFF != None:
				print("-------" + str(image_library[this_DIFF]))
				IMGfile = image_library[this_DIFF]
				try:
					img = bpy.data.images.load(DAEpath + IMGfile)
				except:
					raise NameError("Cannot load image: " + DAEpath + IMGfile)
				# Create image texture from image
				cTex = bpy.data.textures.new(im.attrib["symbol"], type = 'IMAGE')
				cTex.image = img
				# Create material
				mat = bpy.data.materials.new(im.attrib["symbol"])
				# Add texture slot for color texture
				mtex = mat.texture_slots.add()
				mtex.texture = cTex
				mtex.texture_coords = 'UV'
				mtex.use_map_color_diffuse = True
				mtex.use_map_color_emission = True
				mtex.emission_color_factor = 0.5
				mtex.use_map_density = True
				mtex.mapping = 'FLAT'
				#
				this_mesh = context.scene.objects[node.attrib["name"]]
				bpy.data.objects[node.attrib["name"]]
				bpy.ops.object.select_all(action='DESELECT')
				bpy.ops.object.select_pattern(pattern=node.attrib["name"])
				bpy.ops.object.editmode_toggle()
				bpy.ops.uv.smart_project()
				bpy.ops.object.editmode_toggle()
				# add this material to the currently selected object...
				this_mesh.data.materials.append(mat)
				print("+++++++++++++++++++++++++++adding material to mesh " + str(this_mesh))
			print("------" + str(this_GLOW))
			if this_GLOW != None:
				print("-------" + str(image_library[this_GLOW]))
			print("------" + str(this_SPEC))
			if this_SPEC != None:
				print("-------" + str(image_library[this_SPEC]))

# Make textures visible
for area in bpy.context.screen.areas: # iterate through areas in current screen
	if area.type == 'VIEW_3D':
		for space in area.spaces: # iterate through spaces in current VIEW_3D area
			if space.type == 'VIEW_3D': # check if space is a 3D view
				space.viewport_shade = 'TEXTURED' # set the viewport shading to textured

# Clear selection
bpy.ops.object.select_all(action='DESELECT')


print(" ")
print("DONE")
print(" ")
