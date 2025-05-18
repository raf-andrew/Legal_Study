"""
AI Service
"""

import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="AI Service")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Model configuration
MODEL_PATH = os.getenv("MODEL_PATH", "/models")
MODEL_NAME = "gpt2"  # Using GPT-2 as a simple example

# Load model and tokenizer
try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
    model.eval()
    if torch.cuda.is_available():
        model = model.to("cuda")
    logger.info(f"Loaded model {MODEL_NAME}")
except Exception as e:
    logger.error(f"Error loading model: {e}")
    model = None
    tokenizer = None

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post("/api/ai")
async def generate_text(prompt: str, max_length: int = 100):
    """Generate text using the AI model"""
    if model is None or tokenizer is None:
        raise HTTPException(status_code=500, detail="Model not loaded")

    try:
        # Tokenize input
        inputs = tokenizer(prompt, return_tensors="pt")
        if torch.cuda.is_available():
            inputs = inputs.to("cuda")

        # Generate text
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_length=max_length,
                num_return_sequences=1,
                pad_token_id=tokenizer.eos_token_id
            )

        # Decode output
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return {"generated_text": generated_text}
    except Exception as e:
        logger.error(f"Error generating text: {e}")
        raise HTTPException(status_code=500, detail="Text generation failed")

@app.get("/api/ai/status")
async def model_status():
    """Get model status"""
    return {
        "model_loaded": model is not None,
        "model_name": MODEL_NAME,
        "device": "cuda" if torch.cuda.is_available() else "cpu",
        "tokenizer_loaded": tokenizer is not None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
