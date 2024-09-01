import bpy


# Operator to add a mesh object to the collection
class AddMeshOperator(bpy.types.Operator):
    bl_idname = "diffusion.add_mesh"
    bl_label = "Add Mesh"

    def execute(self, context):
        scene = context.scene
        diffusion_props = scene.diffusion_properties

        # Get the list of all available mesh objects in the scene
        available_meshes = [
            (obj.name, obj.name, "") for obj in scene.objects if obj.type == "MESH"
        ]

        # If no meshes are available, show a message and return
        if not available_meshes:
            self.report({"WARNING"}, "No mesh objects available in the scene")
            return {"CANCELLED"}

        # Show a menu to select one of the available mesh objects
        def draw_mesh_menu(self, context):
            layout = self.layout
            for mesh_name, _, _ in available_meshes:
                # Check if the mesh is already in the collection
                if mesh_name not in [
                    mesh_item.name for mesh_item in diffusion_props.mesh_objects
                ]:
                    layout.operator(
                        "diffusion.select_mesh", text=mesh_name
                    ).mesh_name = mesh_name

        context.window_manager.popup_menu(
            draw_mesh_menu, title="Select Mesh", icon="MESH_DATA"
        )
        return {"FINISHED"}


# Operator to select a mesh and add it to the collection
class SelectMeshOperator(bpy.types.Operator):
    bl_idname = "diffusion.select_mesh"
    bl_label = "Select Mesh"

    mesh_name: bpy.props.StringProperty()

    def execute(self, context):
        scene = context.scene
        diffusion_props = scene.diffusion_properties

        # Add the selected mesh to the collection
        new_mesh_item = diffusion_props.mesh_objects.add()
        new_mesh_item.name = self.mesh_name

        return {"FINISHED"}


# Operator to remove a selected mesh from the collection
class RemoveMeshOperator(bpy.types.Operator):
    bl_idname = "diffusion.remove_mesh"
    bl_label = "Remove Mesh"

    index: bpy.props.IntProperty()

    def execute(self, context):
        scene = context.scene
        diffusion_props = scene.diffusion_properties

        # Remove the mesh at the given index
        diffusion_props.mesh_objects.remove(self.index)

        return {"FINISHED"}


def register():
    bpy.utils.register_class(AddMeshOperator)
    bpy.utils.register_class(SelectMeshOperator)
    bpy.utils.register_class(RemoveMeshOperator)


def unregister():
    bpy.utils.unregister_class(AddMeshOperator)
    bpy.utils.unregister_class(SelectMeshOperator)
    bpy.utils.unregister_class(RemoveMeshOperator)
