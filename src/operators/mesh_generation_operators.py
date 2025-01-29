import base64
import os
import tempfile
import threading

import bpy
import requests


class MeshGenerationOperator(bpy.types.Operator):
    bl_idname = "diffusion.generate_3d"
    bl_label = "Generate 3D Model"
    bl_description = (
        "Generate a 3D model from text description, an image or a selected mesh"
    )

    job_id = ""
    prompt = ""
    api_url = ""
    image_path = ""
    octree_resolution = 256
    num_inference_steps = 20
    guidance_scale = 5.5
    texture = False
    selected_mesh_base64 = ""
    selected_mesh = None

    thread = None
    task_finished = False

    def modal(self, context, event):
        if event.type in {"RIGHTMOUSE", "ESC"}:
            return {"CANCELLED"}

        if self.task_finished:
            print("Threaded task completed")
            self.task_finished = False
            props = context.scene.mesh_generation_properties
            props.is_processing = False

        return {"PASS_THROUGH"}

    def invoke(self, context, event):
        props = context.scene.mesh_generation_properties
        self.prompt = props.prompt
        self.api_url = props.api_url
        self.image_path = props.image_path
        self.octree_resolution = props.octree_resolution
        self.num_inference_steps = props.num_inference_steps
        self.guidance_scale = props.guidance_scale
        self.texture = props.texture

        if self.prompt == "" and self.image_path == "":
            self.report({"WARNING"}, "Please enter some text or select an image first.")
            return {"FINISHED"}

        for obj in context.selected_objects:
            if obj.type == "MESH":
                self.selected_mesh = obj
                break

        if self.selected_mesh:
            temp_glb_file = tempfile.NamedTemporaryFile(delete=False, suffix=".glb")
            temp_glb_file.close()
            bpy.ops.export_scene.gltf(filepath=temp_glb_file.name, use_selection=True)
            with open(temp_glb_file.name, "rb") as file:
                mesh_data = file.read()
            mesh_b64_str = base64.b64encode(mesh_data).decode()
            os.unlink(temp_glb_file.name)
            self.selected_mesh_base64 = mesh_b64_str

        props.is_processing = True

        blend_file_dir = os.path.dirname(bpy.data.filepath)
        if self.image_path.startswith("//"):
            self.image_path = os.path.join(blend_file_dir, self.image_path[2:])

        self.thread = threading.Thread(target=self.generate_model)
        self.thread.start()

        wm = context.window_manager
        wm.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def generate_model(self):
        base_url = self.api_url.rstrip("/")

        try:
            if self.selected_mesh_base64 and self.texture:
                if self.image_path and os.path.exists(self.image_path):
                    with open(self.image_path, "rb") as file:
                        image_data = file.read()
                    img_b64_str = base64.b64encode(image_data).decode()
                    response = requests.post(
                        f"{base_url}/generate",
                        json={
                            "mesh": self.selected_mesh_base64,
                            "image": img_b64_str,
                            "octree_resolution": self.octree_resolution,
                            "num_inference_steps": self.num_inference_steps,
                            "guidance_scale": self.guidance_scale,
                            "texture": self.texture,
                        },
                    )
                else:
                    response = requests.post(
                        f"{base_url}/generate",
                        json={
                            "mesh": self.selected_mesh_base64,
                            "text": self.prompt,
                            "octree_resolution": self.octree_resolution,
                            "num_inference_steps": self.num_inference_steps,
                            "guidance_scale": self.guidance_scale,
                            "texture": self.texture,
                        },
                    )
            else:
                if self.image_path and os.path.exists(self.image_path):
                    with open(self.image_path, "rb") as file:
                        image_data = file.read()
                    img_b64_str = base64.b64encode(image_data).decode()
                    response = requests.post(
                        f"{base_url}/generate",
                        json={
                            "image": img_b64_str,
                            "octree_resolution": self.octree_resolution,
                            "num_inference_steps": self.num_inference_steps,
                            "guidance_scale": self.guidance_scale,
                            "texture": self.texture,
                        },
                    )
                else:
                    response = requests.post(
                        f"{base_url}/generate",
                        json={
                            "text": self.prompt,
                            "octree_resolution": self.octree_resolution,
                            "num_inference_steps": self.num_inference_steps,
                            "guidance_scale": self.guidance_scale,
                            "texture": self.texture,
                        },
                    )

            if response.status_code != 200:
                self.report({"ERROR"}, f"Generation failed: {response.text}")
                return

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".glb")
            temp_file.write(response.content)
            temp_file.close()

            def import_handler():
                bpy.ops.import_scene.gltf(filepath=temp_file.name)
                os.unlink(temp_file.name)
                return None

            bpy.app.timers.register(import_handler)

        except Exception as e:
            self.report({"ERROR"}, f"Error: {str(e)}")

        finally:
            self.task_finished = True
            self.selected_mesh_base64 = ""


def mesh_generation_register():
    bpy.utils.register_class(MeshGenerationOperator)


def mesh_generation_unregister():
    bpy.utils.unregister_class(MeshGenerationOperator)
