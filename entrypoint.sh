#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# ============================================================================
# Network Volume Setup
# ============================================================================
# RunPod Network Volume is mounted at /runpod-volume
# We need to create symlinks to /ComfyUI/models

NETWORK_VOLUME="/runpod-volume"

echo "============================================================"
echo "🔍 Checking Network Volume..."
echo "============================================================"

# Check if Network Volume is mounted
if [ -d "$NETWORK_VOLUME" ]; then
    echo "✅ Network Volume found at $NETWORK_VOLUME"
    
    # List contents
    echo "📁 Volume contents:"
    ls -la "$NETWORK_VOLUME/" 2>/dev/null || echo "   (empty or not accessible)"
    
    # Check if models are in the Volume
    if [ -d "$NETWORK_VOLUME/ComfyUI/models" ]; then
        echo "✅ Found ComfyUI/models in Network Volume"
        
        # Create symlinks from Network Volume to /ComfyUI/models
        echo "🔗 Creating symlinks to /ComfyUI/models..."
        
        # Remove existing directories if they exist (they may be empty from Docker build)
        rm -rf /ComfyUI/models/checkpoints 2>/dev/null || true
        rm -rf /ComfyUI/models/vae 2>/dev/null || true
        rm -rf /ComfyUI/models/text_encoders 2>/dev/null || true
        rm -rf /ComfyUI/models/loras 2>/dev/null || true
        
        # Create symlinks
        mkdir -p /ComfyUI/models
        
        if [ -d "$NETWORK_VOLUME/ComfyUI/models/checkpoints" ]; then
            ln -sf "$NETWORK_VOLUME/ComfyUI/models/checkpoints" /ComfyUI/models/checkpoints
            echo "   ✅ Linked checkpoints"
        fi
        
        if [ -d "$NETWORK_VOLUME/ComfyUI/models/vae" ]; then
            ln -sf "$NETWORK_VOLUME/ComfyUI/models/vae" /ComfyUI/models/vae
            echo "   ✅ Linked vae"
        fi
        
        if [ -d "$NETWORK_VOLUME/ComfyUI/models/text_encoders" ]; then
            ln -sf "$NETWORK_VOLUME/ComfyUI/models/text_encoders" /ComfyUI/models/text_encoders
            echo "   ✅ Linked text_encoders"
        fi
        
        if [ -d "$NETWORK_VOLUME/ComfyUI/models/loras" ]; then
            ln -sf "$NETWORK_VOLUME/ComfyUI/models/loras" /ComfyUI/models/loras
            echo "   ✅ Linked loras"
        fi
        
        echo "✅ Symlinks created!"
    else
        echo "⚠️ ComfyUI/models not found in Network Volume"
        echo "   Expected path: $NETWORK_VOLUME/ComfyUI/models/"
        echo "   Please upload models to S3 with correct paths!"
    fi
else
    echo "⚠️ Network Volume not mounted at $NETWORK_VOLUME"
    echo "   Make sure to attach Network Volume to your Serverless Endpoint"
fi

# ============================================================================
# Check for DaSiWa models
# ============================================================================
echo ""
echo "============================================================"
echo "🔍 Checking for DaSiWa models..."
echo "============================================================"

HIGH_MODEL="/ComfyUI/models/checkpoints/TastySin-HIGH-v8.1.safetensors"
LOW_MODEL="/ComfyUI/models/checkpoints/TastySin-LOW-v8.1.safetensors"
VAE_MODEL="/ComfyUI/models/vae/wan_2.1_vae.safetensors"
TEXT_ENCODER="/ComfyUI/models/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors"

# Check each model
echo "Checking models:"
[ -f "$HIGH_MODEL" ] && echo "   ✅ TastySin-HIGH-v8.1.safetensors" || echo "   ❌ TastySin-HIGH-v8.1.safetensors MISSING"
[ -f "$LOW_MODEL" ] && echo "   ✅ TastySin-LOW-v8.1.safetensors" || echo "   ❌ TastySin-LOW-v8.1.safetensors MISSING"
[ -f "$VAE_MODEL" ] && echo "   ✅ wan_2.1_vae.safetensors" || echo "   ❌ wan_2.1_vae.safetensors MISSING"
[ -f "$TEXT_ENCODER" ] && echo "   ✅ umt5_xxl_fp8_e4m3fn_scaled.safetensors" || echo "   ❌ umt5_xxl_fp8_e4m3fn_scaled.safetensors MISSING"

if [ ! -f "$HIGH_MODEL" ] || [ ! -f "$LOW_MODEL" ] || [ ! -f "$VAE_MODEL" ] || [ ! -f "$TEXT_ENCODER" ]; then
    echo ""
    echo "❌ ERROR: Some models are missing!"
    echo ""
    echo "📋 Required models:"
    echo "   - ComfyUI/models/checkpoints/TastySin-HIGH-v8.1.safetensors"
    echo "   - ComfyUI/models/checkpoints/TastySin-LOW-v8.1.safetensors"
    echo "   - ComfyUI/models/vae/wan_2.1_vae.safetensors"
    echo "   - ComfyUI/models/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors"
    echo ""
    echo "💡 Solutions:"
    echo "   1. Upload models to Network Volume via S3"
    echo "   2. Make sure Network Volume is attached to Serverless Endpoint"
    echo "   3. Check that mount path is /runpod-volume"
    exit 1
else
    echo ""
    echo "✅ All DaSiWa models found!"
fi

# Start ComfyUI in the background
echo "Starting ComfyUI in the background..."
python /ComfyUI/main.py --listen --use-sage-attention &

# Wait for ComfyUI to be ready
echo "Waiting for ComfyUI to be ready..."
max_wait=120  # Maximum 2 minute wait
wait_count=0
while [ $wait_count -lt $max_wait ]; do
    if curl -s http://127.0.0.1:8188/ > /dev/null 2>&1; then
        echo "ComfyUI is ready!"
        break
    fi
    echo "Waiting for ComfyUI... ($wait_count/$max_wait)"
    sleep 2
    wait_count=$((wait_count + 2))
done

if [ $wait_count -ge $max_wait ]; then
    echo "Error: ComfyUI failed to start within $max_wait seconds"
    exit 1
fi

# Start the handler in the foreground
# This script becomes the main process of the container
echo "Starting the handler..."
exec python handler.py