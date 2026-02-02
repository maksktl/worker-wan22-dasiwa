# 🗡️💀 DaSiWa I2V/FLF2V Worker - RunPod Serverless 💀🗡️

This project provides a RunPod Serverless Worker for generating videos from images using **DaSiWa (SynthSeduction v9)** model - a high-performance Wan 2.2 checkpoint optimized for fast, high-quality image-to-video generation.

**DaSiWa** is an optimized Wan 2.2 checkpoint that generates high-quality videos with just **4 steps** and **CFG 1**, making it extremely fast while maintaining excellent quality.

## ✨ Key Features

*   **DaSiWa Model**: Powered by SynthSeduction v9 HIGH/LOW checkpoints for fast, high-quality video generation
*   **Ultra-Fast Generation**: 4-step generation with CFG 1 (built-in speed optimization)
*   **I2V Mode**: Image-to-Video - converts a single image into dynamic video
*   **FLF2V Mode**: First-Last-Frame-to-Video - generates smooth transitions between two images
*   **Base64 Encoding Support**: Handles image encoding/decoding automatically
*   **Minimal Dependencies**: Only 4 model files required (no CLIP Vision needed!)
*   **ComfyUI Integration**: Built on ComfyUI for flexible workflow management
*   **Yandex.Disk Model Download**: Automatic model downloading from Yandex.Disk during build

## 🚀 RunPod Serverless Template

This template includes all necessary components to run **DaSiWa I2V/FLF2V** as a RunPod Serverless Worker.

*   **Dockerfile**: Configures the environment and installs all dependencies
*   **handler.py**: Implements the handler function for RunPod Serverless
*   **entrypoint.sh**: Performs initialization tasks when the worker starts
*   **dasiwa_i2v_api.json**: Optimized DaSiWa I2V workflow configuration
*   **builder/cache_models.py**: Downloads models from Yandex.Disk during build

## 📥 Required Models (4 files)

The worker requires **only 4 model files**:

| # | File | Location | Source |
|---|------|----------|-------|
| 1 | `TastySin-HIGH-v8.1.safetensors` | `checkpoints/` | CivitAI |
| 2 | `TastySin-LOW-v8.1.safetensors` | `checkpoints/` | CivitAI |
| 3 | `wan_2.1_vae.safetensors` | `vae/Wan/` | [HuggingFace](https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/blob/main/split_files/vae/wan_2.1_vae.safetensors) |
| 4 | `umt5_xxl_fp8_e4m3fn_scaled.safetensors` | `text_encoders/` | [HuggingFace](https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors) |

**⚠️ CLIP Vision is NOT required** for DaSiWa I2V workflow!

### Setup Instructions

1. **Download models** from the sources above
2. **Upload to Yandex.Disk** and create public links
3. **Update `builder/cache_models.py`** - replace `"ВСТАВЬТЕ_ССЫЛКУ_ЯНДЕКС_ДИСК"` with your Yandex.Disk links
4. **Build Docker image** - models will be downloaded automatically during build

## 🔧 API Reference

### Input

The `input` object must contain the following fields. Images can be input using **path, URL or Base64** - use only one method.

#### First Frame Image Input (required - use only one)
| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `image_path` | `string` | No | - | Local path to the first frame image |
| `image_url` | `string` | No | - | URL of the first frame image |
| `image_base64` | `string` | No | - | Base64 encoded string of the first frame image |

#### Last Frame Image Input (optional - for FLF2V mode, use only one)
| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `last_image_path` | `string` | No | - | Local path to the last frame image |
| `last_image_url` | `string` | No | - | URL of the last frame image |
| `last_image_base64` | `string` | No | - | Base64 encoded string of the last frame image |

> 💡 **Tip**: If you provide a last frame image, the worker automatically switches to **FLF2V mode** (First-Last-Frame-to-Video), creating a smooth transition between the two images.

#### Video Generation Parameters
| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `prompt` | `string` | Yes | - | Description text for the video to be generated |
| `seed` | `integer` | No | `-1` (random) | Random seed for video generation |
| `cfg` | `float` | No | `1.0` | CFG scale (DaSiWa optimized for CFG 1) |
| `width` | `integer` | No | `528` | Width of the output video in pixels |
| `height` | `integer` | No | `768` | Height of the output video in pixels |
| `length` | `integer` | No | `81` | Number of frames (~5 seconds at 16fps) |
| `steps` | `integer` | No | `4` | Number of denoising steps (DaSiWa optimized) |
| `fps` | `integer` | No | `16` | Frames per second |
| `negative_prompt` | `string` | No | (default) | Negative prompt (note: CFG 1 limits negative prompt effectiveness) |
| `sampler_name` | `string` | No | `euler` | Sampler name (FastFidelity C-AiO default: euler) |
| `scheduler` | `string` | No | `linear_quadratic` | Scheduler type (FastFidelity C-AiO default: linear_quadratic) |

**Request Examples:**

#### 1. Basic Generation
```json
{
  "input": {
    "prompt": "woman dancing gracefully",
    "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD...",
    "width": 528,
    "height": 768,
    "length": 81,
    "steps": 4,
    "cfg": 1.0,
    "seed": 42
  }
}
```

#### 2. Custom Resolution
```json
{
  "input": {
    "prompt": "running man, grab the gun",
    "image_url": "https://example.com/image.jpg",
    "width": 560,
    "height": 720,
    "length": 81,
    "steps": 4,
    "cfg": 1.0
  }
}
```

#### 3. Using Network Volume Path
```json
{
  "input": {
    "prompt": "beautiful landscape animation",
    "image_path": "/my_volume/images/landscape.jpg",
    "width": 608,
    "height": 1072,
    "length": 81,
    "steps": 4,
    "cfg": 1.0,
    "fps": 16
  }
}
```

#### 4. FLF2V Mode (First-Last Frame to Video)
```json
{
  "input": {
    "prompt": "smooth morphing transition",
    "image_base64": "<first_frame_base64>",
    "last_image_base64": "<last_frame_base64>",
    "width": 528,
    "height": 768,
    "length": 81,
    "steps": 4,
    "cfg": 1.0
  }
}
```

#### 5. FLF2V with URLs
```json
{
  "input": {
    "prompt": "person walking from point A to point B",
    "image_url": "https://example.com/start_frame.jpg",
    "last_image_url": "https://example.com/end_frame.jpg",
    "width": 560,
    "height": 720,
    "length": 81
  }
}
```

### Output

#### Success

If the job is successful, it returns a JSON object with the generated video Base64 encoded.

| Parameter | Type | Description |
| --- | --- | --- |
| `video` | `string` | Base64 encoded video file data (MP4 format) |

**Success Response Example:**

```json
{
  "video": "data:video/mp4;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
}
```

#### Error

If the job fails, it returns a JSON object containing an error message.

| Parameter | Type | Description |
| --- | --- | --- |
| `error` | `string` | Description of the error that occurred |

**Error Response Example:**

```json
{
  "error": "Video not found."
}
```

## 🛠️ Direct API Usage

1. Create a Serverless Endpoint on RunPod based on this repository
2. Configure Yandex.Disk links in `builder/cache_models.py` before building
3. Once the build is complete and the endpoint is active, submit jobs via HTTP POST requests according to the API Reference above

### 📁 Using Network Volumes

Instead of directly transmitting Base64 encoded files, you can use RunPod's Network Volumes to handle large files.

1. **Create and Connect Network Volume**: Create a Network Volume from the RunPod dashboard and connect it to your Serverless Endpoint settings
2. **Upload Files**: Upload your image files to the Network Volume
3. **Specify Paths**: When making an API request, use `image_path` with the full path to your image file (e.g., `"/my_volume/images/portrait.jpg"`)

## ⚙️ DaSiWa Recommended Settings

| Setting | Value | Description |
|---------|-------|-------------|
| **Steps** | 4 | Optimal for DaSiWa (built-in speed optimization) |
| **CFG** | 1.0 | DaSiWa optimized for CFG 1 |
| **Resolution** | Up to 720p | Native quality (e.g., 528x768, 560x720, 608x1072) |
| **FPS** | 16 | Standard frame rate |
| **Length** | 81 frames | ~5 seconds at 16fps |
| **Sampler** | euler | FastFidelity C-AiO default sampler |
| **Scheduler** | linear_quadratic | FastFidelity C-AiO default scheduler |

### Recommended Aspect Ratios

- **3:4** - 528x768 or 560x720
- **9:16** - 608x1072
- **Native** - Up to 720p for best quality

## ⚠️ Important Notes

1. **CFG 1 = Limited Negative Prompt**: Negative prompts have limited effectiveness with CFG 1 (this is a limitation of fast generation methods)
2. **4 Steps Optimal**: DaSiWa is optimized for 4 steps - increasing steps may not improve quality significantly
3. **No Speed-Up LoRA Needed**: Speed optimization is already built into DaSiWa models
4. **Low Resolution Warning**: Resolutions below 480p will blur fine details - use 720p for quality

## 🔧 DaSiWa Workflow Configuration

This template uses an optimized workflow configuration based on **FastFidelity C-AiO**:

*   **dasiwa_i2v_api.json**: DaSiWa I2V/FLF2V generation workflow

The workflow is based on ComfyUI and includes:
- CheckpointLoaderSimple nodes for HIGH/LOW models
- CLIP text encoding for prompts
- VAE loading and processing
- **WanFirstLastFrameToVideo** node for FLF2V mode (with first + last frame)
- **WanImageToVideo** node for I2V mode (single image, backward compatible)
- KSamplerAdvanced nodes for HIGH/LOW sampling
- VHS_VideoCombine for video output

### Generation Modes

| Mode | Description | Required Parameters |
|------|-------------|--------------------|
| **I2V** | Image-to-Video | `image_*` (first frame only) |
| **FLF2V** | First-Last-Frame-to-Video | `image_*` + `last_image_*` |

## 🙏 About DaSiWa

**DaSiWa** is an optimized Wan 2.2 checkpoint created by [darksidewalker](https://civitai.com/user/darksidewalker) that provides:

- **🔥 LoRA-Free Generations**: Generate high-quality videos without stacking multiple LoRAs
- **☄️ Fast**: 4-step generation
- **Extreme Versatile**: More built-in concepts
- **Quality Motions**: Less slowdowns
- **🔞 NSFW + SFW**: Enhanced anatomy, poses, and framing

### Model Information

- **Model**: [DaSiWa WAN 2.2 I2V 14B Lightspeed](https://civitai.com/models/1981116)
- **Version Used**: TastySin v8.1 HIGH/LOW
- **Workflow**: [FastFidelity C-AiO](https://civitai.com/models/1823089)

## 🙏 Credits & Original Projects

This project is based on the following original repositories:

*   **DaSiWa**: [CivitAI - DaSiWa Collection](https://civitai.com/models/2190659)
*   **Wan2.2**: [https://github.com/Wan-Video/Wan2.2](https://github.com/Wan-Video/Wan2.2)
*   **ComfyUI**: [https://github.com/comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI)
*   **ComfyUI-WanVideoWrapper**: [https://github.com/kijai/ComfyUI-WanVideoWrapper](https://github.com/kijai/ComfyUI-WanVideoWrapper)
*   **ComfyUI-VideoHelperSuite**: [https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite)

## 📄 License

This project follows the licenses of the original projects it is based on.
