from ollama_engine import check_ollama as _check_ollama
from ollama_engine import generate_blender_code
from ollama_engine import get_models


def ask_ai(prompt, model="deepseek-coder:6.7b", timeout=120):
    """Backward-compatible wrapper that returns one complete response string."""
    _ = timeout
    return generate_blender_code(prompt=prompt, model=model, on_token=None)


def check_ollama():
    """Check if Ollama server is reachable."""
    return _check_ollama()


def list_models():
    """List available Ollama models."""
    return get_models()