# 🎬 DaSiWa I2V API Integration Guide

Краткое руководство по интеграции генерации видео в ваш проект.

## 🔗 Endpoint

```
POST https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync
```

**Headers:**
```
Authorization: Bearer {RUNPOD_API_KEY}
Content-Type: application/json
```

---

## 📤 Базовый запрос

```python
import requests
import base64

ENDPOINT_ID = "your-endpoint-id"
API_KEY = "your-api-key"

# Загрузка изображения в base64
with open("image.png", "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode()

response = requests.post(
    f"https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync",
    headers={"Authorization": f"Bearer {API_KEY}"},
    json={
        "input": {
            "prompt": "woman dancing gracefully",
            "image_base64": image_base64,
            "width": 528,
            "height": 768,
            "length": 81,
            "steps": 4,
            "cfg": 1.0,
            "seed": -1,
            "fps": 16
        }
    },
    timeout=600
)

result = response.json()
```

---

## 📥 Обработка ответа

```python
if "output" in result and "video" in result["output"]:
    # Декодируем base64 видео
    video_base64 = result["output"]["video"]
    video_bytes = base64.b64decode(video_base64)
    
    # Сохраняем в файл
    with open("output.mp4", "wb") as f:
        f.write(video_bytes)
    print("✅ Видео сохранено: output.mp4")
    
elif "error" in result:
    print(f"❌ Ошибка: {result['error']}")
```

---

## ⚙️ Параметры запроса

### Обязательные

| Параметр | Тип | Описание |
|----------|-----|----------|
| `prompt` | string | Описание желаемого видео |
| `image_*` | string | Входное изображение (один из вариантов ниже) |

### Варианты передачи изображения

```python
# Вариант 1: Base64 (рекомендуется)
"image_base64": "iVBORw0KGgo..."

# Вариант 2: URL
"image_url": "https://example.com/image.jpg"

# Вариант 3: Путь на Network Volume
"image_path": "/runpod-volume/images/photo.png"
```

### Опциональные параметры

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| `width` | int | 528 | Ширина видео (кратно 16) |
| `height` | int | 768 | Высота видео (кратно 16) |
| `length` | int | 81 | Количество кадров |
| `steps` | int | 4 | Шаги генерации |
| `cfg` | float | 1.0 | CFG scale |
| `seed` | int | -1 | Сид (-1 = рандом) |
| `fps` | int | 16 | Кадров в секунду |
| `negative_prompt` | string | (default) | Негативный промпт |

---

## 📐 Рекомендуемые разрешения

```python
RESOLUTIONS = {
    "portrait_3_4": {"width": 528, "height": 768},   # 3:4
    "portrait_9_16": {"width": 608, "height": 1072}, # 9:16
    "landscape_4_3": {"width": 768, "height": 528},  # 4:3
    "square": {"width": 720, "height": 720},         # 1:1
}
```

**⚠️ Важно:** Размеры автоматически округляются до кратных 16.

---

## ⏱️ Длительность видео

```python
# Формула: длительность = length / fps
DURATIONS = {
    "3_sec": {"length": 49, "fps": 16},
    "5_sec": {"length": 81, "fps": 16},   # рекомендуется
    "7_sec": {"length": 113, "fps": 16},
    "10_sec": {"length": 161, "fps": 16},
}
```

---

## 🎯 Оптимальные настройки DaSiWa

```python
OPTIMAL_SETTINGS = {
    "steps": 4,      # НЕ увеличивать — DaSiWa оптимизирован под 4
    "cfg": 1.0,      # НЕ увеличивать — работает лучше с CFG 1
    "fps": 16,       # Стандартный FPS
    "length": 81,    # ~5 секунд видео
}
```

**⚠️ Ограничения:**
- `cfg: 1.0` = негативный промпт почти не работает
- `steps: 4` = увеличение не улучшает качество
- Разрешение выше 720p может замедлить генерацию

---

## 🐍 Python класс для интеграции

```python
import requests
import base64
from pathlib import Path


class DaSiWaClient:
    def __init__(self, endpoint_id: str, api_key: str):
        self.endpoint_id = endpoint_id
        self.api_key = api_key
        self.base_url = f"https://api.runpod.ai/v2/{endpoint_id}"
    
    def generate_video(
        self,
        image_path: str,
        prompt: str,
        width: int = 528,
        height: int = 768,
        length: int = 81,
        steps: int = 4,
        cfg: float = 1.0,
        seed: int = -1,
        fps: int = 16,
        timeout: int = 600
    ) -> dict:
        """Генерация видео из изображения."""
        
        # Загрузка изображения
        with open(image_path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode()
        
        # Запрос
        response = requests.post(
            f"{self.base_url}/runsync",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "input": {
                    "prompt": prompt,
                    "image_base64": image_base64,
                    "width": width,
                    "height": height,
                    "length": length,
                    "steps": steps,
                    "cfg": cfg,
                    "seed": seed,
                    "fps": fps
                }
            },
            timeout=timeout
        )
        
        return response.json()
    
    def save_video(self, result: dict, output_path: str) -> bool:
        """Сохранение видео из результата."""
        try:
            video_base64 = result["output"]["video"]
            video_bytes = base64.b64decode(video_base64)
            
            Path(output_path).write_bytes(video_bytes)
            return True
        except (KeyError, Exception):
            return False


# Использование
client = DaSiWaClient(
    endpoint_id="your-endpoint-id",
    api_key="your-api-key"
)

result = client.generate_video(
    image_path="photo.png",
    prompt="woman walking in the park",
    width=528,
    height=768
)

if client.save_video(result, "output.mp4"):
    print("✅ Видео сохранено!")
else:
    print(f"❌ Ошибка: {result.get('error', 'Unknown')}")
```

---

## 🔄 Асинхронный запрос (для длинных видео)

```python
import time

# 1. Отправляем задачу
response = requests.post(
    f"https://api.runpod.ai/v2/{ENDPOINT_ID}/run",  # /run вместо /runsync
    headers={"Authorization": f"Bearer {API_KEY}"},
    json={"input": {...}}
)
job_id = response.json()["id"]

# 2. Проверяем статус
while True:
    status = requests.get(
        f"https://api.runpod.ai/v2/{ENDPOINT_ID}/status/{job_id}",
        headers={"Authorization": f"Bearer {API_KEY}"}
    ).json()
    
    if status["status"] == "COMPLETED":
        video_base64 = status["output"]["video"]
        break
    elif status["status"] == "FAILED":
        print(f"Ошибка: {status.get('error')}")
        break
    
    time.sleep(2)  # Проверяем каждые 2 секунды
```

---

## 📊 Примерное время генерации

| Параметры | RTX 4090 | RTX 3090 |
|-----------|----------|----------|
| 81 кадров, 528x768 | ~60-90 сек | ~90-120 сек |
| 81 кадров, 720x1280 | ~90-150 сек | ~150-200 сек |
| Холодный старт | +30-60 сек | +30-60 сек |

---

## ❌ Обработка ошибок

```python
def handle_response(result: dict):
    # Проверка на ошибку API
    if "error" in result:
        raise Exception(f"API Error: {result['error']}")
    
    # Проверка статуса
    status = result.get("status")
    if status == "FAILED":
        raise Exception(f"Job Failed: {result.get('error', 'Unknown')}")
    
    # Проверка наличия видео
    if "output" not in result or "video" not in result["output"]:
        raise Exception("No video in response")
    
    return result["output"]["video"]
```

---

## 💡 Tips & Best Practices

1. **Timeout**: Ставьте timeout минимум 600 сек (10 мин)
2. **Retry**: При ошибках сети делайте 2-3 повторных попытки
3. **Seed**: Сохраняйте seed для воспроизводимости результатов
4. **Batch**: Отправляйте запросы пока воркер активен (экономия на холодных стартах)
5. **Resolution**: Используйте разрешения кратные 16
6. **Prompt**: Пишите описательные промпты на английском

---

## 🔗 Полезные ссылки

- [RunPod API Docs](https://docs.runpod.io/serverless/endpoints/job-operations)
- [DaSiWa Model](https://civitai.com/models/1981116)
- [Wan 2.2 Documentation](https://github.com/Wan-Video/Wan2.2)
