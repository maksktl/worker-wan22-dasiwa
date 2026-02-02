# builder/cache_models.py
"""
Downloads DaSiWa model files from Yandex.Disk during Docker build.
"""

import os
import sys
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Model paths configuration (ComfyUI structure)
COMFYUI_BASE = "/ComfyUI/models"
CHECKPOINTS_PATH = os.path.join(COMFYUI_BASE, "checkpoints")
VAE_PATH = os.path.join(COMFYUI_BASE, "vae")
TEXT_ENCODERS_PATH = os.path.join(COMFYUI_BASE, "text_encoders")

# ============================================================================
# МИНИМАЛЬНЫЙ НАБОР ДЛЯ DaSiWa I2V (4 файла)
# ============================================================================
# 
# 1. DasiwaWAN22I2V14B_synthseductionHighV9.safetensors - основная модель HIGH
#    Источник: CivitAI (DaSiWa / SynthSeduction v9)
#    Папка: /ComfyUI/models/checkpoints/
#
# 2. DasiwaWAN22I2V14B_synthseductionLowV9.safetensors - основная модель LOW  
#    Источник: CivitAI (DaSiWa / SynthSeduction v9)
#    Папка: /ComfyUI/models/checkpoints/
#
# 3. wan_2.1_vae.safetensors - VAE для декодирования видео
#    Источник: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/blob/main/split_files/vae/wan_2.1_vae.safetensors
#    Папка: /ComfyUI/models/vae/Wan/
#
# 4. umt5_xxl_fp8_e4m3fn_scaled.safetensors - Text Encoder
#    Источник: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors
#    Папка: /ComfyUI/models/text_encoders/
#
# ⚠️ CLIP Vision НЕ НУЖЕН для DaSiWa I2V workflow!
# ============================================================================

YANDEX_DISK_LINKS = {
    # 1. TastySin-HIGH-v8.1 - основная модель DaSiWa
    "tastysin_high": {
        "url": "ВСТАВЬТЕ_ССЫЛКУ_ЯНДЕКС_ДИСК",
        "path": os.path.join(CHECKPOINTS_PATH, "TastySin-HIGH-v8.1.safetensors"),
    },
    
    # 2. TastySin-LOW-v8.1 - основная модель DaSiWa
    "tastysin_low": {
        "url": "ВСТАВЬТЕ_ССЫЛКУ_ЯНДЕКС_ДИСК",
        "path": os.path.join(CHECKPOINTS_PATH, "TastySin-LOW-v8.1.safetensors"),
    },
    
    # 3. VAE - обязательно для декодирования видео
    # Источник: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/blob/main/split_files/vae/wan_2.1_vae.safetensors
    "vae": {
        "url": "https://disk.yandex.ru/d/U9NowrvDo9-qgA",
        "path": os.path.join(VAE_PATH, "Wan", "wan_2.1_vae.safetensors"),
    },
    
    # 4. Text Encoder (FP8) - обязательно для обработки промпта
    # Источник: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors
    "text_encoder": {
        "url": "https://disk.yandex.ru/d/6kx5cx5cXzgdTQ",
        "path": os.path.join(TEXT_ENCODERS_PATH, "umt5_xxl_fp8_e4m3fn_scaled.safetensors"),
    },
}

# ============================================================================


def get_session():
    """
    Создает сессию requests с retry и таймаутами.
    """
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=10,
        pool_maxsize=10
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def get_yandex_download_url(public_url: str) -> str:
    """
    Получает прямую ссылку на скачивание из публичной ссылки Яндекс.Диска.
    """
    api_url = "https://cloud-api.yandex.net/v1/disk/public/resources/download"
    session = get_session()
    response = session.get(
        api_url,
        params={"public_key": public_url},
        timeout=30
    )
    
    if response.status_code != 200:
        raise Exception(f"Failed to get download URL: {response.status_code} - {response.text}")
    
    return response.json()["href"]


def download_file(url: str, destination: str, name: str):
    """
    Скачивает файл с оптимизированными настройками для быстрого скачивания.
    """
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    
    print(f"\n📥 Downloading {name}...")
    print(f"   Destination: {destination}")
    
    download_url = get_yandex_download_url(url)
    
    session = get_session()
    response = session.get(
        download_url,
        stream=True,
        timeout=(30, 300)  # connect timeout, read timeout
    )
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    downloaded = 0
    chunk_size = 32 * 1024 * 1024  # 32MB chunks (увеличено для скорости)
    last_percent = -1
    
    with open(destination, 'wb') as f:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                
                # Выводим прогресс только каждые 5% чтобы не спамить логи
                if total_size > 0:
                    percent = int((downloaded / total_size) * 100)
                    if percent != last_percent and percent % 5 == 0:
                        mb_downloaded = downloaded / (1024 * 1024)
                        mb_total = total_size / (1024 * 1024)
                        print(f"   Progress: {mb_downloaded:.1f}/{mb_total:.1f} MB ({percent}%)")
                        last_percent = percent
    
    print(f"   ✓ Downloaded {name} successfully! ({downloaded / (1024 * 1024):.1f} MB)")


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
