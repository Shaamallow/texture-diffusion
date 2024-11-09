import os
from typing import Optional, Set

import bmesh
import bpy
import numpy as np
from PIL import Image

from ..functions.utils import (
    linear_to_srgb_array,
    normalize_array,
    reverse_color,
    send_image_function,
)

# pyright: reportAttributeAccessIssue=false


class DepthRenderOperator(bpy.types.Operator):
    """Render the depth map of the current object from the active camera view,
    process it to normalize depth values,and apply color grading to improve visual representation.
    The operator is called automatically after the camera_setup operator
    """

    bl_idname = "diffusion.render_depth"
    bl_label = "Render Depth Map"
    bl_description = "Render the depth map of the current object from the view, process the depth map to be normalized with proper color grading"

    uuid: bpy.props.StringProperty(name="UUID")

    def get_history_item(self, context: bpy.types.Context) -> Optional[dict]:
        history_props = context.scene.history_properties
        for item in history_props.history_collection:
            if item.uuid == self.uuid:
                return item
        return None

    def execute(self, context: Optional[bpy.types.Context]) -> set[str]:
        assert context is not None
        assert bpy.context is not None

        scene = context.scene

        history_item = self.get_history_item(context)
        if history_item is None:
            self.report({"ERROR"}, "History item not found")
            return {"CANCELLED"}

        ID = history_item.id
        uuid_value = history_item.uuid

        scene.use_nodes = True
        tree = scene.node_tree
        assert tree is not None

        bpy.context.scene.view_layers["ViewLayer"].use_pass_z = True

        links = tree.links

        # Render Nodes
        rl = tree.nodes.new("CompositorNodeRLayers")
        rl.location = 185, 285

        # create output viewer node
        v = tree.nodes.new("CompositorNodeViewer")
        v.location = 750, 210
        v.use_alpha = False

        bpy.data.scenes["Scene"].render.resolution_x = 1024
        bpy.data.scenes["Scene"].render.resolution_y = 1024

        links.new(rl.outputs["Depth"], v.inputs[0])

        # Compute Render
        bpy.ops.render.render()

        # get viewer pixels
        viewer_image = bpy.data.images["Viewer Node"]

        # Process the depthmap
        if viewer_image.size[0] > 0 and viewer_image.size[1] > 0:

            width, height = viewer_image.size
            pixels = np.array(viewer_image.pixels[:])  # pyright: ignore
            arr = pixels.reshape((height, width, 4))

        else:
            self.report({"ERROR"}, "The Viewer Node does not have any image data")
            return {"CANCELLED"}

        # Flip X axis and Drop the alpha layer for the depthmap
        arr = arr[::-1, :, :-1]

        positions = np.unique(arr)
        if len(positions) <= 2:
            self.report(
                {"ERROR"},
                "No Depth detected, aborting the generation",
            )
            return {"CANCELLED"}

        threshold_distance = positions[-2] * 1.05

        arr = np.minimum(arr, threshold_distance)
        arr = normalize_array(arr)
        image_array = linear_to_srgb_array(arr)
        reverse = reverse_color(image_array)

        # Convert to PIL format before sending request

        image = Image.fromarray(reverse)
        file_path = bpy.data.scenes["Scene"].render.filepath
        save_path = os.path.join(file_path, f"depth_{ID}.png")
        image.save(save_path)
        bpy.data.images.load(save_path, check_existing=True)

        # TODO: Pop the render view for the loaded image

        input_depth_name = f"{uuid_value}_depth.png"

        # Call the sending request function
        response_code = send_image_function(
            scene=scene, image=image, image_name=input_depth_name
        )
        if response_code == 200:
            self.report(
                {"INFO"},
                f"Depth map has been sent to the server successfully",
            )
        else:
            self.report(
                {"ERROR"},
                f"Failed to send the image to the server, response code: {response_code}",
            )
            return {"CANCELLED"}

        return {"FINISHED"}


class ImageRenderOperator(bpy.types.Operator):
    """Render the opengl view from the current view,
    will be used for inpainting to generate part of a texture as a new texture
    """

    bl_idname = "diffusion.render_image"
    bl_label = "Render Image"
    bl_description = (
        "Render the current view of the 3D mesh to have a image2image workflow"
    )

    uuid: bpy.props.StringProperty(name="UUID")

    def get_history_item(self, context: bpy.types.Context) -> Optional[dict]:
        history_props = context.scene.history_properties
        for item in history_props.history_collection:
            if item.uuid == self.uuid:
                return item
        return None

    def execute(self, context: Optional[bpy.types.Context]) -> set[str]:
        assert context is not None
        assert bpy.context is not None

        scene = context.scene

        history_item = self.get_history_item(context)
        if history_item is None:
            self.report({"ERROR"}, "History item not found")
            return {"CANCELLED"}

        ID = history_item.id

        overlay_previous_status = bpy.context.space_data.overlay.show_overlays
        previous_output_path = context.scene.render.filepath
        bpy.context.space_data.overlay.show_overlays = False

        # change the output path to have the openGL output
        save_path = os.path.join(
            previous_output_path, f"tmp_render_opengl_inpainting_{ID}.png"
        )
        context.scene.render.filepath = save_path
        bpy.ops.render.opengl(write_still=True)
        bpy.context.space_data.overlay.show_overlays = overlay_previous_status

        context.scene.render.filepath = previous_output_path

        image = Image.open(save_path)

        # TODO: Pop the render view for the loaded image
        input_inpainting_name = f"{self.uuid}_inpainting.png"

        # Call the sending request function
        response_code = send_image_function(
            scene=scene, image=image, image_name=input_inpainting_name
        )
        if response_code == 200:
            self.report(
                {"INFO"},
                f"Inpainting image has been sent to the server successfully",
            )
        else:
            self.report(
                {"ERROR"},
                f"Failed to send the image to the server, response code: {response_code}",
            )
            return {"CANCELLED"}

        return {"FINISHED"}


class MaskRenderOperator(bpy.types.Operator):
    bl_idname = "diffusion.render_mask"
    bl_label = "Render Mask"
    bl_description = (
        "Render mask of the selected vertex of the 3D mesh for an image2image workflow"
    )

    uuid: bpy.props.StringProperty(name="UUID")

    def get_history_item(self, context: bpy.types.Context) -> Optional[dict]:
        """Retrieve the history item associated with the given UUID."""
        history_props = context.scene.history_properties
        for item in history_props.history_collection:
            if item.uuid == self.uuid:
                return item
        return None

    def execute(self, context: Optional[bpy.types.Context]) -> Set[str]:
        assert bpy.context is not None
        assert context is not None

        # Retrieve the scene and associated history item
        scene = context.scene
        history_item = self.get_history_item(context)
        if history_item is None:
            self.report({"ERROR"}, "History item not found")
            return {"CANCELLED"}

        ID = history_item.id

        mesh_name = history_item.mesh
        mesh = bpy.data.objects.get(mesh_name)
        if not mesh:
            self.report({"ERROR"}, f"Mesh '{mesh_name}' not found")
            return {"CANCELLED"}

        # Step 1: Create or get the mask material
        material_name = "white_mask_diffusion"
        if material_name in bpy.data.materials:
            mask_material = bpy.data.materials[material_name]
        else:
            mask_material = bpy.data.materials.new(name=material_name)
            mask_material.use_nodes = True

            assert mask_material.node_tree is not None

            nodes = mask_material.node_tree.nodes
            links = mask_material.node_tree.links

            # Clear existing nodes and setup new emission node with white color
            nodes.clear()
            output_node = nodes.new(type="ShaderNodeOutputMaterial")
            emission_node = nodes.new(type="ShaderNodeEmission")
            emission_node.inputs["Color"].default_value = (
                1.0,
                1.0,
                1.0,
                1.0,
            )  # White color
            links.new(emission_node.outputs["Emission"], output_node.inputs["Surface"])

        # Step 2: Assign the mask material to a new slot on the mesh and set for selected vertices
        mesh.select_set(True)
        assert mesh.data is not None
        assert type(mesh.data) is bpy.types.Mesh

        bm = bmesh.from_edit_mesh(mesh.data)

        # Check if the material slot already exists, otherwise add it
        if material_name not in [mat.name for mat in mesh.data.materials]:
            mesh.data.materials.append(mask_material)
        mat_index = mesh.data.materials.find(material_name)

        # Assign material to selected faces
        for face in bm.faces:
            if any(vert.select for vert in face.verts):
                face.material_index = mat_index

        # Update the mesh and return to object mode
        bmesh.update_edit_mesh(mesh.data)

        # Step 3: Set render mode to 'EMISSION'
        prev_shading = bpy.context.space_data.shading.type
        prev_render_pass = bpy.context.space_data.shading.render_pass
        prev_view_transform = bpy.context.scene.view_settings.view_transform

        bpy.context.space_data.shading.type = "MATERIAL"
        bpy.context.space_data.shading.render_pass = "EMISSION"
        bpy.context.scene.view_settings.view_transform = "Standard"

        overlay_previous_status = bpy.context.space_data.overlay.show_overlays
        previous_output_path = context.scene.render.filepath
        bpy.context.space_data.overlay.show_overlays = False

        # Change the output path to save the OpenGL output as a mask
        save_path = os.path.join(
            previous_output_path, f"tmp_render_opengl_mask_{ID}.png"
        )
        context.scene.render.filepath = save_path
        bpy.ops.render.opengl(write_still=True)
        bpy.context.space_data.overlay.show_overlays = overlay_previous_status

        # Restore previous output path
        context.scene.render.filepath = previous_output_path

        # Load the rendered mask image
        image = Image.open(save_path)

        # Step 5: Send the rendered mask to the server (pseudo-code for server communication)
        # TODO: Pop the render view for the loaded image
        input_mask_name = f"{self.uuid}_mask.png"

        # Call the sending request function
        response_code = send_image_function(
            scene=scene, image=image, image_name=input_mask_name
        )
        if response_code == 200:
            self.report(
                {"INFO"},
                f"Mask has been sent to the server successfully",
            )
        else:
            self.report(
                {"ERROR"},
                f"Failed to send the image to the server, response code: {response_code}",
            )
            return {"CANCELLED"}

        # Step 6: Restore the original state
        bpy.context.space_data.shading.type = prev_shading
        bpy.context.space_data.shading.render_pass = prev_render_pass
        bpy.context.scene.view_settings.view_transform = prev_view_transform

        bpy.ops.object.mode_set(mode="OBJECT")
        mesh.select_set(False)
        mesh.data.materials.pop(
            index=len(mesh.data.materials) - 1
        )  # Remove the mask material slot
        bpy.ops.object.mode_set(mode="EDIT")

        return {"FINISHED"}

    pass


def image_render_register():
    bpy.utils.register_class(DepthRenderOperator)
    bpy.utils.register_class(ImageRenderOperator)
    bpy.utils.register_class(MaskRenderOperator)


def image_render_unregister():
    bpy.utils.unregister_class(DepthRenderOperator)
    bpy.utils.unregister_class(ImageRenderOperator)
    bpy.utils.unregister_class(MaskRenderOperator)
