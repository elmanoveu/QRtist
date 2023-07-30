import torch
from diffusers import StableDiffusionControlNetImg2ImgPipeline,StableDiffusionControlNetPipeline, ControlNetModel, DDIMScheduler


controlnet = ControlNetModel.from_pretrained("monster-labs/control_v1p_sd15_qrcode_monster",
                                             torch_dtype=torch.float16)
pipe = StableDiffusionControlNetPipeline.from_pretrained("dreamlike-art/dreamlike-photoreal-2.0",
    controlnet=controlnet,
    safety_checker=None,
    torch_dtype=torch.float16,
    use_safetensors=True)

pipe.enable_xformers_memory_efficient_attention()
pipe.scheduler = DDIMScheduler.from_config(pipe.scheduler.config)
pipe.enable_model_cpu_offload()