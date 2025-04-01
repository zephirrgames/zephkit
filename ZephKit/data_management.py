import bpy
import re

class ZEPHKIT_DATA_WidgetRedundancy(bpy.types.Operator):
	bl_idname = "zephkit.data.widget_redundancy"
	bl_label = "Solve Bone Widget Redundancy"

	def execute(self, context):
		# Specify the name of the target collection containing the desired meshes
		TARGET_COLLECTION_NAME = "WGT"

		# Get the target collection
		target_collection = bpy.data.collections.get(TARGET_COLLECTION_NAME)
		if not target_collection:
			print(f"Collection '{TARGET_COLLECTION_NAME}' not found. Please check the name.")
			return {'CANCELLED'}

		# Store the objects in the target collection in a dictionary for quick lookup
		target_objects = {re.sub(r"\.\d{3}$", "", obj.name): obj for obj in target_collection.objects}

		# Iterate through all armatures in the scene
		for obj in bpy.data.objects:
			if obj.type == 'ARMATURE':
				print(f"Processing rig: {obj.name}")
				
				# Iterate through all bones in the armature
				for bone in obj.pose.bones:
					custom_shape = bone.custom_shape
					if custom_shape:
						# Check if the custom shape's name exists in the target collection
						the_name = re.sub(r"\.\d{3}$", "", bone.custom_shape.name)
						if the_name in target_objects:
							bone.custom_shape = target_objects[the_name]
							print(f"Updated custom shape for bone: {bone.name}")
						else:
							print(f"Custom shape {custom_shape.name} not found in target collection.")

		print("Dependency replacement completed.")

		return {'FINISHED'}

modules = [
	ZEPHKIT_DATA_WidgetRedundancy
]

def register():
	for module in modules:
		bpy.utils.register_class(module)

def unregister():
	for module in reversed(modules):
		bpy.utils.unregister_class(module)