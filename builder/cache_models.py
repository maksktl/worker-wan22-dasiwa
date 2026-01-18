# builder/cache_models.py
"""
Downloads DaSiWa model files from Yandex.Disk during Docker build.
"""

import os
import sys
import requests

# Model paths configuration (ComfyUI structure)
COMFYUI_BASE = "/ComfyUI/models"
CHECKPOINTS_PATH = os.path.join(COMFYUI_BASE, "checkpoints")
VAE_PATH = os.path.join(COMFYUI_BASE, "vae")
TEXT_ENCODERS_PATH = os.path.join(COMFYUI_BASE, "text_encoders")

# ============================================================================
# МИНИМАЛЬНЫЙ НАБОР ДЛЯ DaSiWa I2V (4 файла)
# ============================================================================
# 
# 1. TastySin-HIGH-v8.1.safetensors - основная модель HIGH
#    Источник: CivitAI (DaSiWa / TastySin)
#    Папка: /ComfyUI/models/checkpoints/
#
# 2. TastySin-LOW-v8.1.safetensors - основная модель LOW  
#    Источник: CivitAI (DaSiWa / TastySin)
#    Папка: /ComfyUI/models/checkpoints/
#
# 3. wan_2.1_vae.safetensors - VAE для декодирования видео
#    Источник: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/blob/main/split_files/vae/wan_2.1_vae.safetensors
#    Папка: /ComfyUI/models/vae/
#
# 4. umt5_xxl_fp8_e4m3fn_scaled.safetensors - Text Encoder
#    Источник: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors
#    Папка: /ComfyUI/models/text_encoders/
#
# ⚠️ CLIP Vision НЕ НУЖЕН для DaSiWa I2V workflow!
# ============================================================================

YANDEX_DISK_LINKS = {
    # 1. TastySin v8.1 HIGH - основная модель DaSiWa
    "tastysin_high": {
        "url": "https://disk.yandex.ru/d/ZJrBC_MQ91v3pg",
        "path": os.path.join(CHECKPOINTS_PATH, "TastySin-HIGH-v8.1.safetensors"),
    },
    
    # 2. TastySin v8.1 LOW - основная модель DaSiWa
    "tastysin_low": {
        "url": "https://disk.yandex.ru/d/fd8gaa1MGsIDJQ",
        "path": os.path.join(CHECKPOINTS_PATH, "TastySin-LOW-v8.1.safetensors"),
    },
    
    # 3. VAE - обязательно для декодирования видео
    # Источник: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/blob/main/split_files/vae/wan_2.1_vae.safetensors
    "vae": {
        "url": "https://disk.yandex.ru/d/U9NowrvDo9-qgA",
        "path": os.path.join(VAE_PATH, "wan_2.1_vae.safetensors"),
    },
    
    # 4. Text Encoder (FP8) - обязательно для обработки промпта
    # Источник: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors
    "text_encoder": {
        "url": "https://disk.yandex.ru/d/6kx5cx5cXzgdTQ",
        "path": os.path.join(TEXT_ENCODERS_PATH, "umt5_xxl_fp8_e4m3fn_scaled.safetensors"),
    },
}

# ============================================================================


def get_yandex_download_url(public_url: str) -> str:
    """
    Получает прямую ссылку на скачивание из публичной ссылки Яндекс.Диска.
    """
    api_url = "https://cloud-api.yandex.net/v1/disk/public/resources/download"
    response = requests.get(api_url, params={"public_key": public_url})
    
    if response.status_code != 200:
        raise Exception(f"Failed to get download URL: {response.status_code} - {response.text}")
    
    return response.json()["href"]


def download_file(url: str, destination: str, name: str):
    """
    Скачивает файл с прогрессом.
    """
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    
    print(f"\n📥 Downloading {name}...")
    print(f"   Destination: {destination}")
    
    download_url = get_yandex_download_url(url)
    
    response = requests.get(download_url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    downloaded = 0
    chunk_size = 8192 * 1024  # 8MB chunks
    
    with open(destination, 'wb') as f:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    mb_downloaded = downloaded / (1024 * 1024)
                    mb_total = total_size / (1024 * 1024)
                    print(f"   Progress: {mb_downloaded:.1f}/{mb_total:.1f} MB ({percent:.1f}%)", end='\r')
    
    print(f"\n   ✓ Downloaded {name} successfully!")


def download_models():
    """
    Скачивает все модели из Яндекс.Диска.
    """
    print("=" * 60)
    print("🚀 Starting DaSiWa model download from Yandex.Disk...")
    print("=" * 60)
    
    for name, config in YANDEX_DISK_LINKS.items():
        url = config["url"]
        path = config["path"]
        
        if "ВСТАВЬТЕ_ССЫЛКУ" in url:
            print(f"\n❌ ERROR: Please set Yandex.Disk URL for '{name}' in cache_models.py")
            sys.exit(1)
        
        if os.path.exists(path):
            print(f"\n✓ {name} already exists, skipping...")
            continue
        
        try:
            download_file(url, path, name)
        except Exception as e:
            print(f"\n❌ ERROR downloading {name}: {e}")
            sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ All DaSiWa models downloaded successfully!")
    print("=" * 60)


if __name__ == "__main__":
    download_models()
