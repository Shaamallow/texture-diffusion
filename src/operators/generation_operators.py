import json
import random
import uuid
from pathlib import Path
from typing import Literal, Optional, Set
from urllib import request

import bmesh
import bpy

# pyright: reportAttributeAccessIssue=false


class ApplyTextureOperator(bpy.types.Operator):
    bl_idname = "diffusion.apply_texture"
    bl_label = "Apply Texture"
    bl_description = "Create a new material for object, project UV from relevant Camera, load generated image and set it in the shading node"

    id: bpy.props.IntProperty(name="ID")

    def find_history_item(self, collection):
        for history_item in collection:
            if history_item.id == self.id:
                return history_item
        return None

    def find_camera_object(self, context, collections):

        backend_props = context.scene.backend_properties

        for collection in collections:
            if collection.name == backend_props.history_collection_name:
                for obj in collection.objects:
                    if obj.name == f"Camera {self.id}":
                        return obj
        return None

    def execute(self, context: Optional[bpy.types.Context]):
        assert context is not None
        assert bpy.context is not None

        scene = context.scene
        history_props = scene.history_properties
        diffusion_props = scene.diffusion_properties

        # Loop through the history collection and find the item with the right id
        history_item = self.find_history_item(history_props.history_collection)

        if history_item is None:
            self.report({"ERROR"}, "No mesh found with the given ID")
            return {"CANCELLED"}

        mesh_name = history_item.mesh
        mesh = bpy.data.objects[mesh_name]

        ### Materials and Textures

        if diffusion_props.toggle_inpainting:

            material = mesh.data.materials[0]
            tree = material.node_tree
            nodes = tree.nodes
            links = tree.links

            # Create necessary nodes
            uv_node_new = nodes.new("ShaderNodeUVMap")
            image_node_new = nodes.new("ShaderNodeTexImage")
            color_mix = nodes.new("ShaderNodeMix")
            color_attribute = nodes.new("ShaderNodeVertexColor")

            # Fetch existing mix nodes
            color_mix_existing_set = []
            for node in nodes:
                if node.type == "MIX":
                    color_mix_existing_set.append(node)
            n_existing_mix = len(color_mix_existing_set)

            # Set locations
            uv_node_new.location = (-1000, 100 + (150 * n_existing_mix))
            image_node_new.location = (-800, 100 + (150 * n_existing_mix))
            color_attribute.location = (-600, 100 + (150 * n_existing_mix))
            color_mix.location = (-400, 100 + (150 * n_existing_mix))

            # Set values
            color_mix.data_type = "RGBA"
            color_attribute.layer_name = f"mask {self.id}"
            uv_node_new.uv_map = f"Texture {self.id}"
            image_node_new.image = bpy.data.images[f"Generation_{self.id}.png"]

            # Links the nodes
            links.new(color_attribute.outputs[0], color_mix.inputs[0])

            ## new generation links
            links.new(uv_node_new.outputs[0], image_node_new.inputs[0])
            links.new(image_node_new.outputs[0], color_mix.inputs["A"])

            if len(color_mix_existing_set) == 1:
                # No existing mix node
                links.new(nodes["Image Texture"].outputs[0], color_mix.inputs["B"])
            else:
                # get the previous mix node
                color_mix_existing_set.sort(key=lambda x: x.name)
                color_mix_previous = color_mix_existing_set[-2]

                links.new(color_mix_previous.outputs["Result"], color_mix.inputs["B"])

            links.new(color_mix.outputs["Result"], nodes["Principled BSDF"].inputs[0])

        else:
            material = bpy.data.materials.new(name=f"Material {self.id}")
            material.use_nodes = True

            # Add the material to the object
            mesh.data.materials.append(material)

            # Add nodes
            tree = material.node_tree
            assert tree is not None
            nodes = tree.nodes
            assert nodes is not None
            links = tree.links
            assert links is not None

            uv_node = nodes.new("ShaderNodeUVMap")
            image_node = nodes.new("ShaderNodeTexImage")

            # set locations
            uv_node.location = (-1000, 100)
            image_node.location = (-800, 100)

            # Set values
            uv_node.uv_map = f"Texture {self.id}"
            image_node.image = bpy.data.images[f"Generation_{self.id}.png"]

            # Links the nodes
            links.new(uv_node.outputs[0], image_node.inputs[0])
            links.new(image_node.outputs[0], nodes["Principled BSDF"].inputs[0])

        # Set the material as active
        mesh.active_material = material

        return {"FINISHED"}


class SendRequestOperator(bpy.types.Operator):
    """Operator used to send request to the comfyUI backend"""

    bl_idname = "diffusion.send_request"
    bl_label = "Send Request"
    bl_description = "Send a request to the comfyUI backend to generate the image"

    uuid: bpy.props.StringProperty(name="UUID")

    # TODO: change from diffusion props to history item props
    def get_history_item(self, context: bpy.types.Context) -> Optional[dict]:
        history_props = context.scene.history_properties
        for item in history_props.history_collection:
            if item.uuid == self.uuid:
                return item
        return None

    def execute(self, context: Optional[bpy.types.Context]) -> Set[str]:
        assert context is not None
        assert bpy.context is not None

        scene = context.scene
        diffusion_props = scene.diffusion_properties
        backend_props = scene.backend_properties

        output_prefix = f"blender-texture/{self.uuid}_output"
        url = backend_props.url

        input_depth_name = f"{self.uuid}_depth.png"
        input_inpainting_name = f"{self.uuid}_inpainting.png"
        input_mask_name = f"{self.uuid}_mask.png"

        # Prepare Request

        json_path = (
            Path(__file__).parent.parent.parent / "workflows" / "sdxl_workflow.json"
        )
        with open(json_path) as f:
            prompt_workflow_json = f.read()
        prompt_request = json.loads(prompt_workflow_json)

        # Seed Logic
        seed = diffusion_props.seed

        if diffusion_props.random_seed:
            seed = random.randint(1, 1000000)
            diffusion_props.seed = seed

        prompt_request["6"]["inputs"]["text"] = diffusion_props.prompt
        prompt_request["3"]["inputs"]["seed"] = seed
        prompt_request["3"]["inputs"]["cfg"] = diffusion_props.cfg_scale
        prompt_request["3"]["inputs"]["steps"] = diffusion_props.n_steps
        prompt_request["11"]["inputs"]["strength"] = diffusion_props.controlnet_scale

        # Input-Output Name format

        prompt_request["12"]["inputs"]["image"] = input_depth_name
        prompt_request["9"]["inputs"]["filename_prefix"] = output_prefix

        if diffusion_props.toggle_inpainting:
            # Update the latent input to use the mask latent
            prompt_request["16"]["inputs"]["image"] = input_inpainting_name
            prompt_request["33"]["inputs"]["image"] = input_mask_name

            prompt_request["3"]["inputs"]["latent_image"] = ["30", 0]
            prompt_request["3"]["inputs"][
                "denoise"
            ] = diffusion_props.denoising_strength

        if diffusion_props.toggle_ipadapter:
            # Update node to use IPAdapter model
            prompt_request["3"]["inputs"]["model"] = ["23", 0]
            prompt_request["23"]["inputs"]["weight"] = diffusion_props.scale_ipadapter

            if diffusion_props.toggle_instantstyle:
                prompt_request["23"]["inputs"]["weight_type"] = "style transfer"
            else:
                prompt_request["23"]["inputs"]["weight_type"] = "standard"

            prompt_request["35"]["inputs"]["image"] = diffusion_props.ip_adapter_image

        # output_name = f"{output_prefix}_output_00001_.png"
        # Add view register using this output_name

        # TODO: Pop the render view for the Depth image

        # Send Request to queue
        p = {"prompt": prompt_request}
        data = json.dumps(p).encode("utf-8")
        req = request.Request(f"{url}/prompt", data=data)
        request.urlopen(req)

        print("Request Sent!")

        return {"FINISHED"}


class ProjectionOperator(bpy.types.Operator):
    """Projection Operator used to project the complete UV or portion of it.
    Will create additional UV maps and vertex attribute if ncessary
    """

    bl_idname = "diffusion.projection_from_view"
    bl_label = "Projection from View"
    bl_description = "Project the UVs and the vertex attributes from the current view to match the generated image and depth map"

    uuid: bpy.props.StringProperty(name="UUID")

    def get_history_item(self, context: bpy.types.Context) -> Optional[dict]:
        history_props = context.scene.history_properties
        for item in history_props.history_collection:
            if item.uuid == self.uuid:
                return item
        return None

    def get_camera_object(
        self, context: bpy.types.Context, id: int
    ) -> Optional[bpy.types.Object]:
        backend_props = context.scene.backend_properties
        for collection in context.scene.collection.children:
            if collection.name == backend_props.history_collection_name:
                for obj in collection.objects:
                    if obj.name == f"Camera {id}":
                        return obj
        return None

    def execute(self, context: Optional[bpy.types.Context]) -> Set[str]:
        assert context is not None

        scene = context.scene
        diffusion_props = scene.diffusion_properties

        history_item = self.get_history_item(context)
        if history_item is None:
            self.report({"ERROR"}, "History item not found")
            return {"CANCELLED"}

        ID = history_item.id

        mesh_name = history_item.mesh
        mesh = bpy.data.objects[mesh_name]

        # Create a new uv mesh
        mesh.data.uv_layers.new(name=f"Texture {ID}")

        # assign the new uv mesh as active
        mesh.data.uv_layers.active_index = len(mesh.data.uv_layers) - 1

        ### Projection

        bpy.ops.object.mode_set(mode="OBJECT")
        modifier = mesh.modifiers.new(name="Projection", type="UV_PROJECT")
        modifier.uv_layer = f"Texture {ID}"
        modifier.projector_count = 1

        # Get the right camera from the diffusion history collection
        camera = self.get_camera_object(context, ID)
        if camera is None:
            self.report({"ERROR"}, "No camera found with the given ID")
            return {"CANCELLED"}

        modifier.projectors[0].object = camera

        # Apply the projection with context override
        context_override = context.copy()
        context_override["object"] = mesh
        with context.temp_override(**context_override):
            bpy.ops.object.modifier_apply(modifier=modifier.name)

        self.report({"INFO"}, "FULL UV Vertex have been projected")
        if diffusion_props.toggle_inpainting:

            bpy.ops.object.mode_set(mode="EDIT")
            obj = mesh
            bm = bmesh.from_edit_mesh(obj.data)

            blending_mode: Literal["blending", "hard edeges"] = (
                diffusion_props.inpainting_mode
            )

            if blending_mode == "blending":
                collayer = bm.verts.layers.color.new(f"mask {ID}")
                for v in bm.verts:
                    if v.select:
                        v[collayer] = [0, 0, 0, 1]

            elif blending_mode == "hard edges":
                collayer = bm.loops.layers.color.new(f"mask {ID}")

                for f in bm.faces:
                    if f.select:
                        for l in f.loops:
                            l[collayer] = [0, 0, 0, 1]

            self.report({"INFO"}, "Partial UV Vertex attributes have been set")

        return {"FINISHED"}


class SetupCameraOperator(bpy.types.Operator):
    bl_idname = "diffusion.camera_setup"
    bl_label = "Setup Camera"
    bl_description = "Create a camera, align it to current view and set it as active"

    @classmethod
    def poll(cls, context: Optional[bpy.types.Context]):
        """Ensure the operator is called with the right conditions :
        - from a 3D view
        - not in camera view (as we want to setup a new camera for the current view)
        - edit mode if inpainting is toggled

        NOTE:   Behaviour is subject to be changed later on for better user control
                with a dedicated "diffusion Camera"
        """

        assert context is not None

        space = context.space_data
        if space.type != "VIEW_3D" or space.region_3d.view_perspective == "CAMERA":
            return False

        if context.scene.diffusion_properties.toggle_inpainting:
            if context.mode != "EDIT_MESH":
                return False
        else:
            if context.mode == "EDIT_MESH":
                return False

        return True

    def check_collection(
        self, collections: bpy.types.Collection
    ) -> bpy.types.Collection:
        """History of generated camera view
        - Create the collection if it doesn't exist
        - Return the collection if it exists

        Input:
        - collections : bpy.types.Collection.children

        Returns:
        - bpy.types.Collection: The "Diffusion Camera History" collections
        """

        for collection in collections:
            if collection.name == "Diffusion Camera History":
                return collection
        camera_history_collection = bpy.data.collections.new("Diffusion Camera History")

        context = bpy.context
        assert context is not None

        context.scene.collection.children.link(camera_history_collection)
        return camera_history_collection

    def execute(self, context: Optional[bpy.types.Context]) -> Set[str]:
        """Blender Operator used to setup the Projection Camera before the rest
        - Create a New Camera Object
        - Align it to the current view
        - Set it as active

        - Generate an UUID for the request

        - Hide all other Objects
        - Call Projection Operator (UV project, vertex attributes...)

        - Call Images Operators
        """

        assert context is not None

        scene = context.scene
        diffusion_props = scene.diffusion_properties
        history_props = scene.history_properties

        # Check if any objects have been selected in the diffusion_props.mesh_objects collection
        if not diffusion_props.mesh_objects:
            self.report({"WARNING"}, "No objects selected in the Mesh Collection")
            return {"CANCELLED"}

        # Check if selected object still exists
        for mesh_item in diffusion_props.mesh_objects:
            if mesh_item.name not in bpy.data.objects:
                self.report(
                    {"ERROR"},
                    f"Object {mesh_item.name} does not exist in the scene anymore",
                )
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

        # Add a camera in Camera History Collection
        diffusion_history_collection = self.check_collection(scene.collection.children)

        # Increment ID and generate camera with corresponding ID
        history_props.history_counter += 1
        ID = history_props.history_counter

        camera_data = bpy.data.cameras.new(name="Camera")
        camera_object = bpy.data.objects.new(f"Camera {ID}", camera_data)
        diffusion_history_collection.objects.link(camera_object)

        generation_uuid = str(uuid.uuid4())
        # Assign diffusion parameters to history item
        bpy.ops.diffusion.update_history(uuid=generation_uuid)

        scene.camera = camera_object
        assert camera_object is not None

        # align to view with a context override
        win = context.window
        scr = win.screen
        areas3d = [area for area in scr.areas if area.type == "VIEW_3D"]
        region = [region for region in areas3d[0].regions if region.type == "WINDOW"]

        with bpy.context.temp_override(window=win, area=areas3d[0], region=region[0]):
            bpy.ops.view3d.camera_to_view()

        self.report({"INFO"}, f"Camera {ID} has been setup and aligned to view")

        # Project the UVs and the vertex attributes
        bpy.ops.diffusion.projection_from_view(uuid=generation_uuid)

        bpy.ops.diffusion.render_depth(uuid=generation_uuid)

        if diffusion_props.toggle_inpainting:
            bpy.ops.diffusion.render_image(uuid=generation_uuid)
            bpy.ops.diffusion.render_mask(uuid=generation_uuid)

        if diffusion_props.toggle_ipadapter:
            bpy.ops.diffusion.render_ipadapter_image()

        # CALL REQUEST OPERATOR
        bpy.ops.diffusion.send_request(uuid=generation_uuid)

        # Launch a watchdog to get the result
        bpy.ops.diffusion.fetch_history(uuid=generation_uuid)

        return {"FINISHED"}


def generation_register():
    bpy.utils.register_class(ApplyTextureOperator)
    bpy.utils.register_class(SetupCameraOperator)
    bpy.utils.register_class(ProjectionOperator)
    bpy.utils.register_class(SendRequestOperator)


def generation_unregister():
    bpy.utils.unregister_class(ApplyTextureOperator)
    bpy.utils.unregister_class(SetupCameraOperator)
    bpy.utils.unregister_class(ProjectionOperator)
    bpy.utils.unregister_class(SendRequestOperator)
