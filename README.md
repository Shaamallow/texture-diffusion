# Texture Diffusion

<p align="center" style="padding: 20px;">
    <a href="https://www.python.org/">
	    <img alt="python version" src='https://img.shields.io/badge/python-3.10-blue'/>
	</a>
    <a href="https://github.com/psf/black">
        <img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-black">
    </a>
    <a href="https://pycqa.github.io/isort/">
        <img alt="Code style: isort" src="https://img.shields.io/badge/code%20style-isort-yellow">
    </a>
    <a href="https://www.blender.org/">
        <img alt="Blender version" src="https://img.shields.io/badge/blender-4.2-orange">
    </a>
</p>

_Generate textures for your models and render scenes directly inside blender using diffusion models._

## Installation

## Usage

Add images for :

- depth estimation
- texture generation
- inpating / Vertex Paint
- Shading Nodes (multi-texturing)
- Rendering

### Texturing

#### Static Scene

#### Inpainting

### Rendering

## Credits

- [Blender](https://www.blender.org/)
- [BlenderAPI](https://docs.blender.org/api/current/index.html)
- [ComfyUI](https://github.com/comfyanonymous/ComfyUI)
- **ME**

# Features Roadmap

- Change camera behavior : Diffusion Camera + Camera Selector. Allow lock to view. Need to rework history to :

  - Save camera position
  - Assign function = assign textures + Update camera with old position
  - [x] Fix the Camera error with wrong context

- Open render window for depth map estimation AND image generation
- Support FLUX models (update the comfy Workflow)
- Add inpainting (for multi texturing) using vertex paint
- Add option for rendering scene (discard selected mesh and don't apply texture)
