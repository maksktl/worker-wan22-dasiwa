import runpod
from runpod.serverless.utils import rp_upload
import os
import shutil
import websocket
import base64
import json
import uuid
import logging
import urllib.request
import urllib.parse
import binascii
import subprocess
import time

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

server_address = os.getenv('SERVER_ADDRESS', '127.0.0.1')
client_id = str(uuid.uuid4())


def to_nearest_multiple_of_16(value):
    """Adjust the given value to the nearest multiple of 16, ensuring minimum of 16"""
    try:
        numeric_value = float(value)
    except Exception:
        raise Exception(f"width/height value is not a number: {value}")
    adjusted = int(round(numeric_value / 16.0) * 16)
    if adjusted < 16:
        adjusted = 16
    return adjusted


def process_input(input_data, temp_dir, output_filename, input_type):
    """Process input data and return file path"""
    if input_type == "path":
        logger.info(f"📁 Processing path input: {input_data}")
        return input_data
    elif input_type == "url":
        logger.info(f"🌐 Processing URL input: {input_data}")
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.abspath(os.path.join(temp_dir, output_filename))
        return download_file_from_url(input_data, file_path)
    elif input_type == "base64":
        logger.info(f"🔢 Processing Base64 input")
        return save_base64_to_file(input_data, temp_dir, output_filename)
    else:
        raise Exception(f"Unsupported input type: {input_type}")


def download_file_from_url(url, output_path):
    """Download file from URL"""
    try:
        result = subprocess.run([
            'wget', '-O', output_path, '--no-verbose', url
        ], capture_output=True, text=True)

        if result.returncode == 0:
            logger.info(f"✅ Successfully downloaded file from URL: {url} -> {output_path}")
            return output_path
        else:
            logger.error(f"❌ wget download failed: {result.stderr}")
            raise Exception(f"URL download failed: {result.stderr}")
    except subprocess.TimeoutExpired:
        logger.error("❌ Download timeout")
        raise Exception("Download timeout")
    except Exception as e:
        logger.error(f"❌ Error during download: {e}")
        raise Exception(f"Error during download: {e}")


def save_base64_to_file(base64_data, temp_dir, output_filename):
    """Save Base64 data to file"""
    try:
        decoded_data = base64.b64decode(base64_data)
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.abspath(os.path.join(temp_dir, output_filename))
        with open(file_path, 'wb') as f:
            f.write(decoded_data)
        logger.info(f"✅ Saved Base64 input to file '{file_path}'.")
        return file_path
    except (binascii.Error, ValueError) as e:
        logger.error(f"❌ Base64 decoding failed: {e}")
        raise Exception(f"Base64 decoding failed: {e}")


def queue_prompt(prompt):
    url = f"http://{server_address}:8188/prompt"
    logger.info(f"Queueing prompt to: {url}")
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(url, data=data)
    return json.loads(urllib.request.urlopen(req).read())


def get_history(prompt_id):
    url = f"http://{server_address}:8188/history/{prompt_id}"
    logger.info(f"Getting history from: {url}")
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read())


def get_videos(ws, prompt):
    prompt_id = queue_prompt(prompt)['prompt_id']
    output_videos = {}
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                data = message['data']
                if data['node'] is None and data['prompt_id'] == prompt_id:
                    break
        else:
            continue

    history = get_history(prompt_id)[prompt_id]
    for node_id in history['outputs']:
        node_output = history['outputs'][node_id]
        videos_output = []
        if 'gifs' in node_output:
            for video in node_output['gifs']:
                with open(video['fullpath'], 'rb') as f:
                    video_data = base64.b64encode(f.read()).decode('utf-8')
                videos_output.append(video_data)
                try:
                    os.remove(video['fullpath'])
                    logger.info(f"Cleaned up video file: {video['fullpath']}")
                except OSError as e:
                    logger.warning(f"Failed to delete video file {video['fullpath']}: {e}")
        output_videos[node_id] = videos_output

    return output_videos


def load_workflow(workflow_path):
    with open(workflow_path, 'r') as file:
        return json.load(file)


def handler(job):
    logger.info("=" * 80)
    logger.info("NEW JOB STARTED - DaSiWa I2V")
    logger.info("=" * 80)

    job_input = job.get("input", {})

    # Sanitized logging
    job_input_log = job_input.copy()
    if "image_base64" in job_input_log and job_input_log["image_base64"]:
        job_input_log["image_base64"] = f"[BASE64_TRUNCATED_{len(job_input_log['image_base64'])}chars]"

    logger.info(f"Received job input: {job_input_log}")

    task_id = f"task_{uuid.uuid4()}"
    temp_dirs_created = set()

    # Process image input
    image_path = None
    if "image_path" in job_input:
        image_path = process_input(job_input["image_path"], task_id, "input_image.png", "path")
    elif "image_url" in job_input:
        temp_dirs_created.add(task_id)
        image_path = process_input(job_input["image_url"], task_id, "input_image.png", "url")
    elif "image_base64" in job_input:
        temp_dirs_created.add(task_id)
        image_path = process_input(job_input["image_base64"], task_id, "input_image.png", "base64")
    else:
        image_path = "/example_image.png"
        logger.info("Using default image file: /example_image.png")

    # Load DaSiWa I2V workflow
    workflow_file = "/dasiwa_i2v_api.json"
    logger.info(f"Loading DaSiWa I2V workflow: {workflow_file}")
    prompt = load_workflow(workflow_file)

    # === DaSiWa Settings ===
    # Defaults from DaSiWa documentation
    width = job_input.get("width", 528)
    height = job_input.get("height", 768)
    length = job_input.get("length", 81)  # 81 frames = ~5 seconds at 16fps
    steps = job_input.get("steps", 4)  # DaSiWa: 4 steps
    cfg = job_input.get("cfg", 1.0)  # DaSiWa: CFG 1
    seed = job_input.get("seed", -1)
    fps = job_input.get("fps", 16)

    # Adjust to multiples of 16
    adjusted_width = to_nearest_multiple_of_16(width)
    adjusted_height = to_nearest_multiple_of_16(height)
    if adjusted_width != width:
        logger.info(f"Width adjusted: {width} -> {adjusted_width}")
    if adjusted_height != height:
        logger.info(f"Height adjusted: {height} -> {adjusted_height}")

    # Random seed if -1
    if seed == -1:
        import random
        seed = random.randint(0, 2**63 - 1)
    logger.info(f"Using seed: {seed}")

    # === Apply settings to workflow ===
    
    # Node 5: Positive prompt
    prompt["5"]["inputs"]["text"] = job_input.get("prompt", "")
    
    # Node 6: Negative prompt (use default or custom)
    negative_prompt = job_input.get("negative_prompt", prompt["6"]["inputs"]["text"])
    prompt["6"]["inputs"]["text"] = negative_prompt
    
    # Node 7: Load image
    prompt["7"]["inputs"]["image"] = image_path
    
    # Node 8: WanImageToVideo
    prompt["8"]["inputs"]["width"] = adjusted_width
    prompt["8"]["inputs"]["height"] = adjusted_height
    prompt["8"]["inputs"]["length"] = length
    
    # Node 11: KSampler High
    prompt["11"]["inputs"]["seed"] = seed
    prompt["11"]["inputs"]["steps"] = steps
    prompt["11"]["inputs"]["cfg"] = cfg
    prompt["11"]["inputs"]["end_at_step"] = steps // 2  # Half steps for HIGH
    
    # Node 12: KSampler Low
    prompt["12"]["inputs"]["seed"] = seed
    prompt["12"]["inputs"]["steps"] = steps
    prompt["12"]["inputs"]["cfg"] = cfg
    prompt["12"]["inputs"]["start_at_step"] = steps // 2  # Start from half for LOW
    
    # Node 14: Video output
    prompt["14"]["inputs"]["frame_rate"] = fps

    logger.info(f"DaSiWa settings: {adjusted_width}x{adjusted_height}, {length} frames, {steps} steps, CFG {cfg}, {fps} fps")

    # === Connect to ComfyUI ===
    ws_url = f"ws://{server_address}:8188/ws?clientId={client_id}"
    http_url = f"http://{server_address}:8188/"
    
    logger.info(f"Connecting to ComfyUI at {http_url}")

    # HTTP connection check
    max_http_attempts = 180
    for http_attempt in range(max_http_attempts):
        try:
            response = urllib.request.urlopen(http_url, timeout=5)
            logger.info(f"HTTP connection successful (attempt {http_attempt+1})")
            break
        except Exception as e:
            logger.warning(f"HTTP connection failed (attempt {http_attempt+1}/{max_http_attempts}): {e}")
            if http_attempt == max_http_attempts - 1:
                raise Exception("Cannot connect to ComfyUI server.")
            time.sleep(1)

    # WebSocket connection
    ws = websocket.WebSocket()
    max_attempts = 36
    for attempt in range(max_attempts):
        try:
            ws.connect(ws_url)
            logger.info(f"WebSocket connection successful (attempt {attempt+1})")
            break
        except Exception as e:
            logger.warning(f"WebSocket connection failed (attempt {attempt+1}/{max_attempts}): {e}")
            if attempt == max_attempts - 1:
                raise Exception("WebSocket connection timeout")
            time.sleep(5)

    # Generate video
    videos = get_videos(ws, prompt)
    ws.close()

    # Cleanup
    logger.info("=" * 80)
    logger.info("JOB COMPLETE - CLEANUP")
    logger.info("=" * 80)

    for temp_dir in temp_dirs_created:
        try:
            shutil.rmtree(temp_dir)
            logger.info(f"Cleaned up: {temp_dir}")
        except Exception as e:
            logger.warning(f"Failed to clean up {temp_dir}: {e}")

    output_dir = "/ComfyUI/output"
    try:
        if os.path.exists(output_dir):
            for filename in os.listdir(output_dir):
                file_path = os.path.join(output_dir, filename)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    logger.warning(f"Failed to remove {file_path}: {e}")
    except Exception as e:
        logger.warning(f"Failed to clean output directory: {e}")

    # Return result
    for node_id in videos:
        if videos[node_id]:
            return {"video": videos[node_id][0]}

    return {"error": "Video not found."}


runpod.serverless.start({"handler": handler})
