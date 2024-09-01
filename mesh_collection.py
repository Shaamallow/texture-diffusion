import json
import random
from io import BytesIO
from urllib import parse, request

import bpy
import numpy as np
import requests
from PIL import Image

# pyright: reportInvalidTypeForm=false
# Refer to this issue as to why this is disabled : https://github.com/microsoft/pylance-release/issues/5457


# Define a class to store individual mesh selection with a Boolean property
class MeshItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Mesh Name")


# Define the property group class
class DiffusionProperties(bpy.types.PropertyGroup):

    # Store a collection of mesh items
    mesh_objects: bpy.props.CollectionProperty(type=MeshItem)

    # The existing models available property
    models_available: bpy.props.EnumProperty(
        name="Models",
        description="Pick a model from the available models you have downloaded",
        items=[("sdxl", "SDXL", "Base SDXL model available on huggingface")],
        default=None,
    )

    prompt: bpy.props.StringProperty(
        name="Prompt", description="Text prompt for the diffusion effect"
    )
    n_steps: bpy.props.IntProperty(
        name="N_Steps",
        description="Number of steps for the diffusion effect",
        default=30,
        min=1,
    )
    seed: bpy.props.IntProperty(
        name="seed",
        description="Seed for the generation. 0 is random seed",
        default=1000000,
        min=0,
    )
    cfg_scale: bpy.props.FloatProperty(
        name="CFG Scale",
        description="CFG scale for the diffusion effect",
        default=7.5,
        min=1.0,
    )
    show_advanced: bpy.props.BoolProperty(
        name="Show Advanced Parameters",
        description="Toggle advanced parameters",
        default=False,
    )
    negative_prompt: bpy.props.StringProperty(
        name="Negative Prompt",
        description="Negative text prompt for the diffusion effect",
    )
    scheduler: bpy.props.EnumProperty(
        name="Scheduler",
        description="Scheduler for the diffusion process",
        items=[("DDIM", "DDIM", ""), ("DDPM", "DDPM", ""), ("LCM", "LCM", "")],
        default="DDIM",
    )


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


# Define the main diffusion panel class
class DiffusionPanel(bpy.types.Panel):
    bl_label = "Diffusion Panel"
    bl_idname = "OBJECT_PT_DiffusionPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Diffusion"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        diffusion_properties = scene.diffusion_properties

        # Add the models_available property to the panel
        layout.prop(diffusion_properties, "models_available")

        layout.prop(diffusion_properties, "prompt")
        row = layout.row()
        row.prop(diffusion_properties, "n_steps")
        row.prop(diffusion_properties, "cfg_scale")

        layout.prop(diffusion_properties, "seed")

        layout.prop(diffusion_properties, "show_advanced")

        if diffusion_properties.show_advanced:
            layout.prop(diffusion_properties, "negative_prompt")
            layout.prop(diffusion_properties, "scheduler")

        # Add a visual separator and different background for the mesh collection
        layout.separator()
        box = layout.box()
        box.label(text="Select Meshes", icon="MESH_DATA")

        # Button to add a mesh object to the collection
        box.operator("diffusion.add_mesh", text="Add Mesh")

        # Display the mesh_objects collection with remove buttons
        for i, mesh_item in enumerate(diffusion_properties.mesh_objects):
            row = box.row(align=True)
            row.label(text=mesh_item.name)
            row.operator("diffusion.remove_mesh", text="", icon="REMOVE").index = i

        # Add a big "Generate" button at the bottom of the panel
        layout.separator()
        layout.operator("diffusion.generate", text="Generate", icon="RENDER_STILL")


class GenerateDiffusionOperator(bpy.types.Operator):
    bl_idname = "diffusion.generate"
    bl_label = "Generate"

    # Utils functions
    def normalize_array(self, array: np.ndarray):
        return (array - np.min(array)) / np.max(array - np.min(array))

    def linear_to_srgb_array(self, color_array: np.ndarray):
        # Create an empty array to hold the sRGB values
        srgb_array = np.empty_like(color_array)

        # Apply the conversion for values <= 0.0031308
        mask = color_array <= 0.0031308
        srgb_array[mask] = 12.92 * color_array[mask] * 255.99

        # Apply the conversion for values > 0.0031308
        srgb_array[~mask] = (
            1.055 * np.power(color_array[~mask], 1 / 2.4) - 0.055
        ) * 255.99

        # Convert the result to integers (sRGB values)
        return srgb_array.astype(np.uint8)

    def reverse_color(self, color_array: np.ndarray):
        return 255 - color_array

    # Open the depth.json file

    def send_request(self, scene, depth_image):
        diffusion_props = scene.diffusion_properties

        # UPLOAD IMAGE TO COMFY
        image = depth_image

        # Convert the PIL image to bytes
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)

        # Prepare the multipart/form-data payload
        files = {"image": ("blender_depth.png", buffer, "image/png")}

        # Additional data can be added to the request if needed
        data = {
            "type": "input",  # Adjust the type according to your needs ('input', 'temp', 'output')
            "overwrite": "true",  # Optionally set to 'true' if you want to overwrite an existing image
        }

        response = requests.post(
            "http://127.0.0.1:8188/upload/image", files=files, data=data
        )
        print(response.status_code)

        if response.status_code != 200:
            print("Error occured")
            return

        # Now send request to generate with correct parameters

        # Load basic scheme
        json_path = "./Code/test/controlnet_depth.json"
        with open(json_path) as f:
            prompt_text = f.read()

        prompt_request = json.loads(prompt_text)

        positive_prompt = diffusion_props.prompt
        seed = diffusion_props.seed

        if seed == 0:
            seed = random.randint(1, 1000000)
        prompt_request["6"]["inputs"]["text"] = positive_prompt

        # input parameters
        prompt_request["3"]["inputs"]["seed"] = seed
        prompt_request["3"]["inputs"]["steps"] = diffusion_props.n_steps

        p = {"prompt": prompt_request}
        data = json.dumps(p).encode("utf-8")
        req = request.Request("http://127.0.0.1:8188/prompt", data=data)
        request.urlopen(req)

        print("Request Sent!")

        return

    # Main function
    def execute(self, context):
        scene = context.scene
        diffusion_props = scene.diffusion_properties

        # Check if any objects have been selected in the diffusion_props.mesh_objects collection
        if not diffusion_props.mesh_objects:
            self.report({"WARNING"}, "No objects selected in the Mesh Collection")
            return {"CANCELLED"}

        # Step 1 & 2: Loop over all available objects in the scene and store their current visibility state
        original_visibility = {}
        for obj in scene.objects:
            original_visibility[obj.name] = obj.hide_render

        # Step 3: Set all objects not in the diffusion_props.mesh_objects collection as hidden for rendering
        for obj in scene.objects:
            if obj.name not in [
                mesh_item.name for mesh_item in diffusion_props.mesh_objects
            ]:
                obj.hide_render = True
            else:
                obj.hide_render = False

        bpy.ops.object.camera_add()
        camera = context.active_object
        scene.camera = camera
        bpy.ops.view3d.camera_to_view()

        print("Generating Depth map")

        # switch on nodes
        scene.use_nodes = True
        tree = scene.node_tree
        bpy.context.scene.view_layers["ViewLayer"].use_pass_z = True
        links = tree.links

        # create input render layer node
        rl = tree.nodes.new("CompositorNodeRLayers")
        rl.location = 185, 285

        # create output viewer node
        v = tree.nodes.new("CompositorNodeViewer")
        v.location = 750, 210
        v.use_alpha = False

        # Set viewer node resolution to 1024x512 pixels
        bpy.data.scenes["Scene"].render.resolution_x = 512
        bpy.data.scenes["Scene"].render.resolution_y = 512

        # Links: link the Depth output to the Viewer node
        links.new(rl.outputs["Depth"], v.inputs[0])

        # render
        bpy.ops.render.render()

        # get viewer pixels
        viewer_image = bpy.data.images["Viewer Node"]

        # Check if the image has data
        if viewer_image.size[0] > 0 and viewer_image.size[1] > 0:
            # Get the dimensions
            width, height = viewer_image.size
            print(f"Image size: {width} x {height}")

            # Get pixel data
            pixels = np.array(viewer_image.pixels[:])

            print(f"Lenght: {len(pixels)}")

            # Reshape the pixel data to a proper matrix with shape (height, width, channels)
            # In this case, we know that the number of channels is 4 (RGBA), so we reshape accordingly
            arr = pixels.reshape((height, width, 4))

            print(f"Array shape: {arr.shape}")
        else:
            print("The Viewer Node does not have any image data.")

        m, n, _ = arr.shape
        arr = arr[::-1, :, :-1]

        positions = np.unique(arr)
        print(positions)
        threshold_distance = positions[-2] * 1.05

        arr = np.minimum(arr, threshold_distance)
        arr = self.normalize_array(arr)
        image_array = self.linear_to_srgb_array(arr)
        reverse = self.reverse_color(image_array)

        image = Image.fromarray(reverse)
        image.save("test.png")

        # Cleaning Up

        bpy.data.objects.remove(camera)

        for obj in scene.objects:
            obj.hide_render = original_visibility[obj.name]

        tree.nodes.remove(rl)
        tree.nodes.remove(v)

        self.send_request(scene, image)

        return {"FINISHED"}


# Register the panel and properties
def register():
    bpy.utils.register_class(MeshItem)
    bpy.utils.register_class(DiffusionProperties)
    bpy.utils.register_class(DiffusionPanel)
    bpy.utils.register_class(AddMeshOperator)
    bpy.utils.register_class(SelectMeshOperator)
    bpy.utils.register_class(RemoveMeshOperator)
    bpy.utils.register_class(GenerateDiffusionOperator)
    bpy.types.Scene.diffusion_properties = bpy.props.PointerProperty(
        type=DiffusionProperties
    )


def unregister():
    bpy.utils.unregister_class(MeshItem)
    bpy.utils.unregister_class(DiffusionProperties)
    bpy.utils.unregister_class(DiffusionPanel)
    bpy.utils.unregister_class(AddMeshOperator)
    bpy.utils.unregister_class(SelectMeshOperator)
    bpy.utils.unregister_class(RemoveMeshOperator)
    bpy.utils.unregister_class(GenerateDiffusionOperator)
    del bpy.types.Scene.diffusion_properties


if __name__ == "__main__":
    register()
