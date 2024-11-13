from typing import List

import bpy
import requests


class MeshItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Mesh Name")


class DiffusionProperties(bpy.types.PropertyGroup):

    # Update the model
    def update_models(self, context):

        base_url = context.scene.backend_properties.url
        route = "/models/checkpoints"
        response = requests.get(f"{base_url}{route}")

        if response.status_code == 200:
            models: List[str] = response.json()
            models_list = [
                (
                    model,
                    model.replace(".safetensors", ""),
                    "",
                )
                for model in models
            ]
        else:
            models_list = []
        return models_list

    def update_loras(self, context):

        base_url = context.scene.backend_properties.url
        route = "/models/loras"
        response = requests.get(f"{base_url}{route}")

        output = [("None", "None", "")]
        if response.status_code == 200:
            loras: List[str] = response.json()
            loras_list = [
                (
                    lora,
                    lora.replace(".safetensors", ""),
                    "",
                )
                for lora in loras
            ]
            output += loras_list
        return output

    mesh_objects: bpy.props.CollectionProperty(type=MeshItem)

    models_available: bpy.props.EnumProperty(
        name="Models",
        description="Pick a model from the available models you have downloaded",
        items=update_models,
        default=None,
    )
    loras_available: bpy.props.EnumProperty(
        name="Loras",
        description="Pick a lora from the available loras you have downloaded",
        items=update_loras,
        default=0,
    )
    lora_scale: bpy.props.FloatProperty(
        name="Lora Scale",
        description="Weight for the lora",
        default=1.0,
        min=0.0,
        max=3.0,
    )

    # Properties for the diffusion generation
    prompt: bpy.props.StringProperty(
        name="Prompt", description="Text prompt for the diffusion effect"
    )
    n_steps: bpy.props.IntProperty(
        name="N_Steps",
        description="Number of steps for the diffusion process",
        default=30,
        min=1,
    )
    cfg_scale: bpy.props.FloatProperty(
        name="CFG Scale",
        description="Classifier-Free Guidance scale for the diffusion process",
        default=5.5,
        min=0.0,
    )
    controlnet_scale: bpy.props.FloatProperty(
        name="ControlNet Scale",
        description="Controlnet Strengh for the conditioning. 0 means no depth conditioning",
        default=0.7,
        min=0.0,
    )
    seed: bpy.props.IntProperty(
        name="seed",
        description="Seed for the generation.",
        default=42,
        min=0,
        max=1000000,
    )
    random_seed: bpy.props.BoolProperty(
        name="Use a random seed",
        description="Toggle random seed for generationg",
        default=False,
    )
    sampler_name: bpy.props.EnumProperty(
        name="Sampler Name",
        description="Sampler Name",
        items=[
            ("euler", "Euler", ""),
            ("euler_cfg_pp", "Euler CFG PP", ""),
            ("euler_ancestral", "Euler Ancestral", ""),
            ("euler_ancestral_cfg_pp", "Euler Ancestral CFG PP", ""),
            ("heun", "Heun", ""),
            ("heunpp2", "Heun PP2", ""),
            ("dpm_2", "DPM 2", ""),
            ("dpm_2_ancestral", "DPM 2 Ancestral", ""),
            ("lms", "LMS", ""),
            ("dpm_fast", "DPM Fast", ""),
            ("dpm_adaptive", "DPM Adaptive", ""),
            ("dpmpp_2s_ancestral", "DPM++ 2S Ancestral", ""),
            ("dpmpp_2s_ancestral_cfg_pp", "DPM++ 2S Ancestral CFG PP", ""),
            ("dpmpp_sde", "DPM++ SDE", ""),
            ("dpmpp_sde_gpu", "DPM++ SDE GPU", ""),
            ("dpmpp_2m", "DPM++ 2M", ""),
            ("dpmpp_2m_cfg_pp", "DPM++ 2M CFG PP", ""),
            ("dpmpp_2m_sde", "DPM++ 2M SDE", ""),
            ("dpmpp_2m_sde_gpu", "DPM++ 2M SDE GPU", ""),
            ("dpmpp_3m_sde", "DPM++ 3M SDE", ""),
            ("dpmpp_3m_sde_gpu", "DPM++ 3M SDE GPU", ""),
            ("ddpm", "DDPM", ""),
            ("lcm", "LCM", ""),
            ("ipndm", "IPNDM", ""),
            ("ipndm_v", "IPNDM V", ""),
            ("deis", "DEIS", ""),
            ("ddim", "DDIM", ""),
            ("uni_pc", "Uni PC", ""),
            ("uni_pc_bh2", "Uni PC BH2", ""),
        ],
        default="euler",
    )

    # Inpainting properties
    toggle_inpainting: bpy.props.BoolProperty(
        name="Toggle Inpainting",
        description="Toggle Inpainting",
        default=False,
    )
    inpainting_mode: bpy.props.EnumProperty(
        name="Inpainting Mode",
        description="Inpainting Mode",
        items=[("blending", "Blending", ""), ("hard edges", "Hard Edges", "")],
        default="blending",
    )

    toggle_ipadapter: bpy.props.BoolProperty(
        name="Toggle IPAdapter",
        description="Toggle IPAdapter",
        default=False,
    )
    scale_ipadapter: bpy.props.FloatProperty(
        name="Scale IPAdapter",
        description="Scale IPAdapter",
        default=1.0,
        min=0.0,
        max=10.0,
    )
    toggle_instantstyle: bpy.props.BoolProperty(
        name="Toggle InstantStyle",
        description="Toggle InstantStyle",
        default=False,
    )
    ip_adapter_image: bpy.props.StringProperty(name="IPAdapter Image", default="")

    toggle_image2image: bpy.props.BoolProperty(
        name="Toggle Image2Image",
        description="Toggle Image2Image",
        default=False,
    )
    denoising_strength: bpy.props.FloatProperty(
        name="Denoising Strength",
        description="Denoising Strength",
        default=1.0,
        max=1.0,
        min=0.0,
    )

    negative_prompt: bpy.props.StringProperty(
        name="Negative Prompt",
        description="Negative text prompt for the diffusion effect",
    )
    scheduler: bpy.props.EnumProperty(
        name="Scheduler",
        description="Scheduler for the diffusion process",
        items=[
            ("normal", "Normal", ""),
            ("karras", "Karras", ""),
            ("exponential", "Exponential", ""),
            ("sgm_uniform", "SGM Uniform", ""),
            ("simple", "Simple", ""),
            ("ddim_uniform", "DDIM Uniform", ""),
            ("beta", "Beta", ""),
            ("linear_quadratic", "Linear Quadratic", ""),
        ],
        default="normal",
    )

    clip_skip: bpy.props.IntProperty(
        name="Clip Skip", description="Clip Skip", min=-24, max=-1, default=-1
    )

    height: bpy.props.IntProperty(
        name="Height", description="Height of the generated image", default=1024
    )

    width: bpy.props.IntProperty(
        name="Width", description="Height of the generated image", default=1024
    )

    def update_mesh_collection(self, context):
        """Update the mesh_objects collection to match the current scene"""
        self.mesh_objects.clear()
        for obj in bpy.context.scene.objects:
            if obj.type == "MESH":
                mesh_item = self.mesh_objects.add()
                mesh_item.name = obj.name

    # New property for mesh selection
    mesh_objects: bpy.props.CollectionProperty(type=MeshItem)


def register():
    bpy.utils.register_class(MeshItem)
    bpy.utils.register_class(DiffusionProperties)
    bpy.types.Scene.diffusion_properties = bpy.props.PointerProperty(
        type=DiffusionProperties
    )


def unregister():
    bpy.utils.unregister_class(MeshItem)
    bpy.utils.unregister_class(DiffusionProperties)
    del bpy.types.Scene.diffusion_properties
