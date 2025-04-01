import bpy
import re

def PROP_updateEraseMode(self, context):
	brush = bpy.data.brushes.get("Draw")
	if brush:
		if brush.blend == "SUB" or brush.blend == "ADD":
			brush.blend = "SUB" if self.zk_erase else "ADD"

bpy.types.Scene.zk_erase = bpy.props.BoolProperty(
    name= "Erase Mode",
    description= "Erase colors instead of add?",
    default = False,
	update = PROP_updateEraseMode
)

bpy.types.Scene.delete_counter = bpy.props.IntProperty(
    name= "Delete Counter",
    description= "Internal use",
    default = 0,
)

class ZephKit_ColorMenu(bpy.types.Menu):
	bl_label = "Custom Lighting"
	bl_idname = "zephkit.shade"

	def draw(self, context):
		layout = self.layout
		mesh = context.active_object.data if context.active_object and context.active_object.type == 'MESH' else None
		if mesh:
			# Adding operators to the menu
			erase = layout.prop(context.scene, "zk_erase")

			layout.separator()

			black = layout.operator("zephkit.apply_shade_paint", text="Black", icon="RECORD_OFF")
			black.color = (0, 0, 0)
			black.blend = "MIX"

			white = layout.operator("zephkit.apply_shade_paint", text="White", icon="RECORD_ON")
			white.color = (1, 1, 1)
			white.blend = "MIX"

			layout.separator()

			prefix = "(Erase) " if context.scene.zk_erase else ""

			light = layout.operator("zephkit.apply_shade_paint", text=prefix+"Shading", icon="NODE_MATERIAL")
			light.color = (1, 0, 0)
			light.blend = "ADD"

			specular = layout.operator("zephkit.apply_shade_paint", text=prefix+"Specular", icon="OUTLINER_OB_LIGHT")
			specular.color = (0, 1, 0)
			specular.blend = "ADD"

			detail = layout.operator("zephkit.apply_shade_paint", text=prefix+"Auto", icon="SOLO_ON")
			detail.color = (0, 0, 1)
			detail.blend = "MIX"

			layout.separator()
			# add the valid frames.
			valid_frames = []
			active_frame = -1

			for i,x in enumerate(mesh.color_attributes):
				layer_name = x.name
				if layer_name.startswith("frame"):
					num = layer_name.replace("frame","").replace(" ","") # replace spaces and the frame part with empty.
					valid_frames.append(int(num))
					if mesh.attributes.active_color_index == i:
						active_frame = int(num)

			for valid_frame in sorted(valid_frames):
				frame_selector = layout.operator("zephkit.select_color_layer", text=f"Frame {valid_frame}", icon="DOT" if active_frame == valid_frame else "NONE")
				frame_selector.frame = valid_frame
			layout.operator("zephkit.add_vertex_color_layer",text="Create Frame",icon="ADD")

class ZephKit_AddVertexColorLayer(bpy.types.Operator):
	bl_label = "Add Vertex Color Layer"
	bl_idname = "zephkit.add_vertex_color_layer"

	def execute(self, context):
		# Get existing vertex color layers
		mesh = context.active_object.data if context.active_object and context.active_object.type == 'MESH' else None
		if mesh:
			# Extract current vertex color layer names
			existing_layers = [layer.name for layer in mesh.color_attributes]
			# Use regex to find the highest number
			next_layer = 1
			while f"frame{next_layer}" in existing_layers: # Search for a number we can use.
				next_layer += 1
			
			# Determine the next available frame number
			new_layer_name = f"frame{next_layer}"

			# Create new vertex color layer
			mesh.color_attributes.new(name=new_layer_name,type='FLOAT_COLOR', domain='POINT')

			# Set the new layer as active
			set_act = mesh.color_attributes.get(new_layer_name)
			mesh.attributes.active_color = set_act
			
			self.report({'INFO'}, f"Added vertex color layer: {new_layer_name}")
		else:
			self.report({'ERROR'}, "No active mesh object found")
		
		return {'FINISHED'}

class ZephKit_SelectColorLayer(bpy.types.Operator):
	bl_label = "Select Color Frame"
	bl_idname = "zephkit.select_color_layer"

	frame: bpy.props.IntProperty(
		name="Frame"
	)

	def execute(self, context):
		mesh = context.active_object.data if context.active_object and context.active_object.type == 'MESH' else None
		if mesh:
			frame_name = f"frame{self.frame}"
			# Set the new layer as active
			if frame_name in mesh.color_attributes:
				set_act = mesh.color_attributes.get(frame_name)
				mesh.attributes.active_color = set_act
				return {'FINISHED'}
		return {'CANCELLED'}		

class ZephKit_ApplyColor(bpy.types.Operator):
	bl_label = "Apply Shading Paint"
	bl_idname = "zephkit.apply_shade_paint"

	blend: bpy.props.StringProperty(
		name="Blend Mode",
		description="Blend mode for the paint",
	)

	color: bpy.props.FloatVectorProperty(
		name="Color",
		description="Color for paint",
		default=(1.0, 1.0, 1.0),  # RGB default to white
		subtype='COLOR'
	)

	def execute(self, context):
		# Check and apply settings to the active brush
		brush = bpy.data.brushes.get("Draw")
		if brush:
			if self.blend == "ADD":
				if context.scene.zk_erase:
					brush.blend = "SUB"
				else:
					brush.blend = "ADD"
			else:
				brush.blend = self.blend
			brush.color = self.color
			self.report({'INFO'}, f"Applied {self.blend} with color {self.color}")
		else:
			self.report({'ERROR'}, "No active brush found")
		return {'FINISHED'}
	
class ZephKit_DeleteAllLayers(bpy.types.Operator):
	bl_label = "Delete all Layers"
	bl_idname = "zephkit.delete_all_color_layers"

	def execute(self, context):
		
		# Get existing vertex color layers
		mesh = context.active_object.data if context.active_object and context.active_object.type == 'MESH' else None
		if mesh:
			# Has a warning if you really wanna delete it.
			context.scene.delete_counter += 1
			if context.scene.delete_counter > 1:
				context.scene.delete_counter = 0 
				# Actually Delete all
				for x in range(len(mesh.color_attributes)):
					mesh.color_attributes.remove(mesh.color_attributes[x])
		else:
			self.report({'ERROR'}, "No active mesh object found")
		
		return {'FINISHED'}


def draw_item(self, context):
	layout = self.layout
	layout.menu(ZephKit_ColorMenu.bl_idname)


def register_keymap():
	wm = bpy.context.window_manager
	kc = wm.keyconfigs.addon
	if kc:
		# Create a new keymap for calling the menu
		km = kc.keymaps.new(name='Vertex Paint', space_type='EMPTY')
		kmi = km.keymap_items.new('wm.call_menu', 'W', 'PRESS')
		kmi.properties.name = ZephKit_ColorMenu.bl_idname


def unregister_keymap():
	wm = bpy.context.window_manager
	kc = wm.keyconfigs.addon
	if kc:
		km = kc.keymaps.get('Vertex Paint')
		if km:
			for kmi in km.keymap_items:
				if kmi.idname == 'wm.call_menu' and kmi.properties.name == ZephKit_ColorMenu.bl_idname:
					km.keymap_items.remove(kmi)

modules = [
	ZephKit_SelectColorLayer,
	ZephKit_ColorMenu,
	ZephKit_ApplyColor,
	ZephKit_AddVertexColorLayer,
]


# Register and unregister functions
def register():
	for module in modules:
		bpy.utils.register_class(module)
	bpy.types.TOPBAR_MT_editor_menus.append(draw_item)
	register_keymap()


def unregister():
	unregister_keymap()
	bpy.types.TOPBAR_MT_editor_menus.remove(draw_item)
	for module in reversed(modules):
		bpy.utils.unregister_class(module)



# Enable the script to run as an addon
if __name__ == "__main__":
	register()
