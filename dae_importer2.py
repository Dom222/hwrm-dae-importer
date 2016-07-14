# HWRM DAE Importer for Blender
#
# To do:
# - Handle nav names to match better collada exporter (currently truncated)
# - Get image file names & materials from the DAE - currently assumes images are in the same path as the DAE file...
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

################################################################################
############################# PROCESSING FUNCTIONS #############################
################################################################################

def ProcessVertList(vertex_list):
	print("ProcessVertList()")
	processed_verts = []
	coord = 0
	this_vertex_coords = []
	for v in vertex_list:
		coord = coord + 1
		this_vertex_coords.append(float(v))
		if coord == 3:
			processed_verts.append(this_vertex_coords)
			coord = 0
			this_vertex_coords = []
	return processed_verts

def ProcessTriaList(tria_data,max_offset,vert_offset):
	print("ProcessTriaList()")
	processed_triangles = []
	this_offset = 0
	this_vertex = 1
	this_tria_verts = []
	for i in range(0, len(tria_data)): # loop through the triangle data
		if this_offset == vert_offset: # if the current entry is a vertex, process it
			this_tria_verts.append(int(tria_data[i]))
		if this_offset == max_offset: # if this is the last value in the vertex
			if this_vertex == 3:
				# triangle definition complete
				processed_triangles.append(this_tria_verts)
				this_offset = -1 # this will be bumped up to 0 by the last statement in the for loop
				this_vertex = 1 # reset to vertex 1 of the next triangle
				this_tria_verts = [] # reset to a blank list ready for the next triangle
			else:
				this_vertex = this_vertex + 1 # triangle definition not complete, move to next vertex
				this_offset = -1 # this will be bumped up to 0 by the last statement in the for loop
		this_offset = this_offset + 1
	return processed_triangles

def ProcessUVCoords(coords):
	coord_list = coords.split()
	processed_uv_coords = []
	this_coord = 0
	these_coords = []
	for u in coord_list:
		these_coords.append(float(u))
		if this_coord == 1:
			processed_uv_coords.append(these_coords)
			this_coord = 0
			these_coords = []
		else:
			this_coord = this_coord + 1
	return processed_uv_coords
	
################################################################################
########################### BLENDER OBJECT CREATION ############################
################################################################################

def createTextureLayer(name, me, texFaces):
	uvtex = me.uv_textures.new()
	uvtex.name = name
	print(name)
	for n,tf in enumerate(texFaces):
		print(n)
		print(tf)
		datum = uvtex.data[n]
		datum.uv1 = tf[0]
		datum.uv2 = tf[1]
		datum.uv3 = tf[2]
	return uvtex

def CreateJoint(jnt_name,jnt_locn,jnt_rotn,jnt_context):
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
				CheckForChildren(item,context)

def CreateMesh(name,origin,verts,trias,mats,uvs,uv_coords):
	# Process trias
	faces = []
	tria_mats = []
	for i in range(0, len(trias)):
		for j in trias[i]:
			faces.append(j)
			tria_mats.append(mats[i][0])
	
	################################################################################
	################################## Create mesh #################################
	################################################################################
	me = bpy.data.meshes.new(name)
	ob = bpy.data.objects.new(name, me)
	ob.location = origin
	ob.show_name = True
	
	# Link object to scene and make active
	scn = bpy.context.scene
	scn.objects.link(ob)
	scn.objects.active = ob
	ob.select = True # needs to be selected for materials bit
	
	# Create mesh from given verts, faces
	me.from_pydata(verts, [], faces)
	# Update mesh with new data
	me.update()
	
	################################################################################
	############################### Create materials ###############################
	################################################################################
	
	#this_mat_data = [this_mat,this_GLOW_filename,this_GLOW_name,this_DIFF_filename,this_DIFF_name,this_SPEC_filename,this_SPEC_name]
	#			   m[0,	   1,				 2,			 3,				 4,			 5,				 6			 ]
	
	this_mat_index = 0
	mat_index_lib = {}
	for m in mats:
		if m[0] != "no material":
			#this_mat_data = [this_mat,this_GLOW_filename,this_DIFF_filename,this_SPEC_filename]
			print("Creating material " + m[0])
			mat_path = "C:/Program Files (x86)/Steam/steamapps/workshop/content/244160/403557412/Kad_Swarmer/"
			glow_filename = None
			diff_filename = None
			spec_filename = None
			if m[1]:
				glow_filename = mat_path + m[1]
			if m[3]:
				diff_filename = mat_path + m[3]
			if m[5]:
				spec_filename = mat_path + m[5]
			CreateMaterial(glow_filename,m[2],diff_filename,m[4],spec_filename,m[6],m[0],ob)
			mat_index_lib[m[0]] = this_mat_index
			this_mat_index = this_mat_index + 1
	
	################################################################################
	########################### Assign materials to faces ##########################
	################################################################################
	
	obj = bpy.context.active_object
	#bpy.ops.object.editmode_toggle()
	faceloop = True
	f = 0
	while faceloop:
		try:
			obj.data.polygons[f].material_index = mat_index_lib[tria_mats[f]]
		except:
			faceloop = False
		f = f + 1
	
	# Add UV maps
	
	uv_trias = []
	
	for u in range(0,len(uvs)):
		print("++++++++++++++++++++++++")
		print("UV map for material " + str(m[u]))
		uv_trias.append([])
		if uvs[u]:
			for tria in uvs[u]:
				this_tria_uvs = []
				for vert in tria:
					this_tria_uvs.append(uv_coords[u][vert])
				uv_trias[u].append(this_tria_uvs)
		#print(uv_trias[u])
	
	# Select the object - necessary?
	bpy.data.objects[name].select = True
	bpy.context.scene.objects.active = bpy.data.objects[name]
	# Select the faces for each material
	bpy.ops.object.editmode_toggle()
	for i in range(0,this_mat_index):
		print("UV mapping for material index " + str(i))
		bpy.context.object.active_material_index = i
		bpy.ops.mesh.select_all(action="DESELECT")
		bpy.ops.object.material_slot_select()
		# Apply a UV map
		bpy.ops.uv.smart_project()
		#print(me)
		#print(uv_trias[i])
		#uvmap = createTextureLayer("UVMap1", me, uv_trias[i])
		#bpy.ops.uv.project_from_view(camera_bounds=False, correct_aspect=True, scale_to_bounds=False)
		me.uv_textures["UVMap"].active = True
		me.uv_textures["UVMap"].active_render = True
	
	bpy.ops.object.editmode_toggle()
	
	return ob

def CreateMaterial(glow_file,glow_name,diff_file,diff_name,spec_file,spec_name,mat_name,this_mesh):
	# Create material
	MAT = bpy.data.materials.new(mat_name)
	# Process DIFF
	if diff_file:
		try:
			DIFF_img = bpy.data.images.load(diff_file)
		except:
			raise NameError("Cannot DIFF load image: " + diff_file)
		# Create DIFF texture
		DIFF = bpy.data.textures.new(mat_name,type='IMAGE')
		DIFF.image = DIFF_img
		# Add texture slot for DIFF
		MAT_DIFF = MAT.texture_slots.add()
		MAT_DIFF.texture = DIFF
		MAT_DIFF.texture.name = diff_name
		MAT_DIFF.texture_coords = 'UV'
		MAT_DIFF.use_map_color_diffuse = True
		#MAT_DIFF.use_map_color_emission = True
		#MAT_DIFF.emission_color_factor = 0.5
		MAT_DIFF.use_map_density = True
		MAT_DIFF.mapping = 'FLAT'
	# Process SPEC
	if spec_file:
		try:
			SPEC_img = bpy.data.images.load(spec_file)
		except:
			raise NameError("Cannot SPEC load image: " + spec_file)
		# Create SPEC texture
		SPEC = bpy.data.textures.new(mat_name,type='IMAGE')
		SPEC.image = SPEC_img
		# Add texture slot for SPEC
		MAT_SPEC = MAT.texture_slots.add()
		MAT_SPEC.texture = SPEC
		MAT_SPEC.texture.name = spec_name
		MAT_SPEC.use_map_specular = True
	if glow_file:
		try:
			GLOW_img = bpy.data.images.load(glow_file)
		except:
			raise NameError("Cannot GLOW load image: " + glow_file)
		# Create GLOW texture
		GLOW = bpy.data.textures.new(mat_name,type='IMAGE')
		GLOW.image = GLOW_img
		# Add texture slot for GLOW
		MAT_GLOW = MAT.texture_slots.add()
		MAT_GLOW.texture = GLOW
		MAT_GLOW.texture.name = glow_name
		MAT_GLOW.use_map_emit = True
	
	# add this material to the currently selected object...
	this_mesh.data.materials.append(MAT)

################################################################################
################################## File input ##################################
################################################################################

DAEpath = "C:/Program Files (x86)/Steam/steamapps/workshop/content/244160/403557412/Kad_Swarmer/"
DAEfile = "Kad_Swarmer.DAE"

# This one has a <rotate> without a "sid"!!!
#DAEpath ="C:/Users/Dom/Documents/06 Games/HW2/taiidan_republic/ship/trp_transport/"
#DAEfile = "trp_emptytransport.dae"

#DAEpath = "C:/Program Files (x86)/Steam/steamapps/workshop/content/244160/403557412/Tur_P1Mothership/"
#DAEfile = "Tur_P1Mothership.DAE"

# Max DAE
#DAEpath = "C:/Users/Dom/Documents/3dsMax/export/"
#DAEfile = "trp_attackbomber.DAE"

# Blender DAE
#DAEpath = "C:/Users/Dom/Documents/06 Games/HW2/taiidan_republic/ship/trp_ioncannonfrigate/"
#DAEfile = "trp_ioncannonfrigate4.DAE"

# RODOH DAE
#DAEpath = "C:/Users/Dom/Dropbox/file-transfer/hgn-frig/"
#DAEfile = "hgn_torpedofrigate.dae"

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
			#print("this is a mesh:" + item.attrib["url"])
			is_joint = False
	# If this is a joint, make it!
	if is_joint:
		CreateJoint(joint_name, joint_location,joint_rotation,context)

print(" ")
print("CREATING MESHES")
print(" ")

lib_mat = root.find("{http://www.collada.org/2005/11/COLLADASchema}library_materials")
lib_fx  = root.find("{http://www.collada.org/2005/11/COLLADASchema}library_effects")
lib_img = root.find("{http://www.collada.org/2005/11/COLLADASchema}library_images")


for geometry in root.iter("{http://www.collada.org/2005/11/COLLADASchema}geometry"): # find all <geometry> in the file
	this_mesh_name = geometry.attrib["name"].rstrip("Mesh")
	print("-----------------------------")
	print("Found <geometry> " + this_mesh_name)
	# This assumes that there is only one <mesh> per <geometry>
	this_mesh = geometry.find("{http://www.collada.org/2005/11/COLLADASchema}mesh")
	###################################################################
	########################### GET VERTICES ##########################
	###################################################################
	# This assumes that there is only one <vertices> per <mesh>
	this_vert_data_raw = None
	for temp_verts in this_mesh.iter("{http://www.collada.org/2005/11/COLLADASchema}vertices"): # find all <vertices> in the <mesh>
		verts_input = temp_verts.find("{http://www.collada.org/2005/11/COLLADASchema}input").attrib["source"].lstrip("#")
		# Get the <float_array> where the vertices are actually listed...
		for source in this_mesh.iter("{http://www.collada.org/2005/11/COLLADASchema}source"): # find all <source> in the <mesh>
			if source.attrib["id"] == verts_input:
				this_vert_data_raw = source.find("{http://www.collada.org/2005/11/COLLADASchema}float_array").text
				this_vert_data = ProcessVertList(this_vert_data_raw.split())
	# Loop through <triangles>
	all_triangles = []
	all_uvs = []
	all_uv_coords = []
	all_mats = []
	for this_triangles in this_mesh.iter("{http://www.collada.org/2005/11/COLLADASchema}triangles"): # find all <triangles> in the <mesh>
		this_mat_data = None
		this_uv_data = None
		this_uv_coords = None
		###################################################################
		########################## GET MATERIALS ##########################
		###################################################################
		this_GLOW_filename = None
		this_GLOW_name = None
		this_DIFF_filename = None
		this_DIFF_name = None
		this_SPEC_filename = None
		this_SPEC_name = None
		if "material" in this_triangles.attrib:
			this_mat = this_triangles.attrib["material"]
			print(this_mat)
			# Get FX name
			for fx in lib_mat.iter("{http://www.collada.org/2005/11/COLLADASchema}material"): # find all <material> in <library_materials>
				if fx.attrib["id"] == this_mat:
					this_mat_fx = fx.find("{http://www.collada.org/2005/11/COLLADASchema}instance_effect").attrib["url"].lstrip("#") # find the <instance_effect> in the <material>
					print(this_mat_fx)
			# Get IMG names
			for effect in lib_fx.iter("{http://www.collada.org/2005/11/COLLADASchema}effect"): # find all <effect> in <library_effects>
				if effect.attrib["id"] == this_mat_fx:
					this_profile = effect.find("{http://www.collada.org/2005/11/COLLADASchema}profile_COMMON")
					this_technique = this_profile.find("{http://www.collada.org/2005/11/COLLADASchema}technique")
					this_phong = this_technique.find("{http://www.collada.org/2005/11/COLLADASchema}phong")
					if this_phong.find("{http://www.collada.org/2005/11/COLLADASchema}emission/{http://www.collada.org/2005/11/COLLADASchema}texture"):
						this_GLOW_img = this_phong.find("{http://www.collada.org/2005/11/COLLADASchema}emission/{http://www.collada.org/2005/11/COLLADASchema}texture").attrib["texture"]
					else:
						print("No GLOW for " + this_mat)
						this_GLOW_img = None
					if this_phong.find("{http://www.collada.org/2005/11/COLLADASchema}diffuse/{http://www.collada.org/2005/11/COLLADASchema}texture"):
						this_DIFF_img = this_phong.find("{http://www.collada.org/2005/11/COLLADASchema}diffuse/{http://www.collada.org/2005/11/COLLADASchema}texture").attrib["texture"]
					else:
						print("No DIFF for " + this_mat)
						this_DIFF_img = None
					if this_phong.find("{http://www.collada.org/2005/11/COLLADASchema}specular/{http://www.collada.org/2005/11/COLLADASchema}texture"):
						this_SPEC_img = this_phong.find("{http://www.collada.org/2005/11/COLLADASchema}specular/{http://www.collada.org/2005/11/COLLADASchema}texture").attrib["texture"]
					else:
						print("No SPEC for " + this_mat)
						this_SPEC_img = None
			# Get file names
			for image in lib_img: # all <image> in <library_images>
				if image.attrib["id"] == this_GLOW_img:
					this_GLOW_filename = image.find("{http://www.collada.org/2005/11/COLLADASchema}init_from").text.lstrip("file://")
					this_GLOW_name = image.attrib["name"]
				elif image.attrib["id"] == this_DIFF_img:
					this_DIFF_filename = image.find("{http://www.collada.org/2005/11/COLLADASchema}init_from").text.lstrip("file://")
					this_DIFF_name = image.attrib["name"]
				elif image.attrib["id"] == this_SPEC_img:
					this_SPEC_filename = image.find("{http://www.collada.org/2005/11/COLLADASchema}init_from").text.lstrip("file://")
					this_SPEC_name = image.attrib["name"]
		else:
			this_mat = "no material"
		this_mat_data = [this_mat,this_GLOW_filename,this_GLOW_name,this_DIFF_filename,this_DIFF_name,this_SPEC_filename,this_SPEC_name]
		print("Found <triangles> with mat " + this_mat)
		# Loop through the <input>s
		offset_per_vertex = 0
		tria_uv_offset = None
		for this_input in this_triangles.iter("{http://www.collada.org/2005/11/COLLADASchema}input"): # find all <input> in the <triangles>
			print("<input> for " + this_input.attrib["semantic"])
			# Track the offsets
			if this_input.attrib["semantic"] == "VERTEX":
				tria_vertex_offset = int(this_input.attrib["offset"])
			if int(this_input.attrib["offset"]) > offset_per_vertex: # ¬
				offset_per_vertex = int(this_input.attrib["offset"]) # |- we need the maximum offset (early Blender HW DAE exports can have all offsets = 0)
			###################################################################
			############################# GET UVS #############################
			###################################################################
			if this_input.attrib["semantic"] == "TEXCOORD":
				tria_uv_offset = int(this_input.attrib["offset"])
				print("Found <input> TEXCOORD")
				for source in this_mesh.iter("{http://www.collada.org/2005/11/COLLADASchema}source"): # find all <source> in the <mesh>
					if source.attrib["id"] == this_input.attrib["source"].lstrip("#"):
						this_uv_coords_raw = source.find("{http://www.collada.org/2005/11/COLLADASchema}float_array").text
						this_uv_coords = ProcessUVCoords(this_uv_coords_raw)
		###################################################################
		########################## GET TRIANGLES ##########################
		###################################################################
		this_tria_data_raw = this_triangles.find("{http://www.collada.org/2005/11/COLLADASchema}p").text
		this_tria_data = ProcessTriaList(this_tria_data_raw.split(),offset_per_vertex,tria_vertex_offset)
		if tria_uv_offset:
			this_uv_data = ProcessTriaList(this_tria_data_raw.split(),offset_per_vertex,tria_uv_offset)
		#
		all_triangles.append(this_tria_data)
		all_uvs.append(this_uv_data)
		all_uv_coords.append(this_uv_coords)
		all_mats.append(this_mat_data)
	###################################################################
	########################## MAKE THE MESH ##########################
	###################################################################
	origin = (0.0,0.0,0.0)
	CreateMesh(this_mesh_name,origin,this_vert_data,all_triangles,all_mats,all_uvs,all_uv_coords)
"""
<triangles count="1492" material="MAT[Kad_Swarmer]_SHD[ship]">
	<input semantic="VERTEX" offset="0" source="#MULT[P2Swarmer]_LOD[0]_TAGS[DoScar]-VERTEX"/>
	<input semantic="NORMAL" offset="1" source="#MULT[P2Swarmer]_LOD[0]_TAGS[DoScar]-Normal0"/>
	<input semantic="TEXCOORD" offset="2" set="0" source="#MULT[P2Swarmer]_LOD[0]_TAGS[DoScar]-UV0"/>
	<input semantic="COLOR" offset="3" set="0" source="#MULT[P2Swarmer]_LOD[0]_TAGS[DoScar]-VERTEX_COLOR0"/>
	<p> 0 0 0 0 3 1 1 3 2 2 2 2 2 3 2 2 1 4 3 1 0 5 0 0 4 6 4 4 6 7 5 6 2 8 2 2 2 9 2 2 5 10 6 5 4 11 4 4 2 12 ...</p>
</triangles>
<triangles count="322" material="MAT[Kad_SwarmerThruster]_SHD[thruster]">
	<input semantic="VERTEX" offset="0" source="#MULT[P2Swarmer]_LOD[0]_TAGS[DoScar]-VERTEX"/>
	<input semantic="NORMAL" offset="1" source="#MULT[P2Swarmer]_LOD[0]_TAGS[DoScar]-Normal0"/>
	<input semantic="TEXCOORD" offset="2" set="0" source="#MULT[P2Swarmer]_LOD[0]_TAGS[DoScar]-UV0"/>
	<input semantic="COLOR" offset="3" set="0" source="#MULT[P2Swarmer]_LOD[0]_TAGS[DoScar]-VERTEX_COLOR0"/>
	<p> 806 4476 1078 806 804 4477 1079 804 805 4478 1080 805 794 4479 1081 794 505 4480 1133 505 483 4481 1129 ...</p>
</triangles>
"""


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

# Make textures visible
for area in bpy.context.screen.areas: # iterate through areas in current screen
	if area.type == 'VIEW_3D':
		for space in area.spaces: # iterate through spaces in current VIEW_3D area
			if space.type == 'VIEW_3D': # check if space is a 3D view
				space.viewport_shade = 'TEXTURED' # set the viewport shading to textured

# Clear selection
bpy.ops.object.select_all(action='DESELECT')

"""
#bpy.ops.object.select_pattern(pattern="MULT[P2Swarmer]_LOD[0]_TAGS[DoScar]")
bpy.data.objects["MULT[P2Swarmer]_LOD[0]_TAGS[DoScar]"].select = True
bpy.context.scene.objects.active = bpy.data.objects["MULT[P2Swarmer]_LOD[0]_TAGS[DoScar]"]
bpy.ops.object.editmode_toggle()
bpy.context.object.active_material_index = 1
bpy.ops.mesh.select_all(action="DESELECT")
bpy.ops.object.material_slot_select()

#bpy.ops.object.editmode_toggle()
"""
print("--------------------------------------------------------------------------------")
print("DONE")
print("--------------------------------------------------------------------------------")
