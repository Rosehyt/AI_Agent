import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline, BitsAndBytesConfig
from langchain_huggingface import HuggingFacePipeline

def load_local_llm(model_id="Qwen/Qwen2.5-3B-Instruct"):
    """
    Loads a local Hugging Face model for use in the query system.
    Using 4-bit quantization to fit within low-VRAM GPUs (e.g., 2GB GT 1030).
    """
    print(f"🔍 Loading Local LLM (4-bit mode): {model_id}...")
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        
        # Check if CUDA is available for GPU acceleration
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🚀 Using device: {device}")
        
        # Configure BitsAndBytes for 4-bit quantization
        bnb_config = None
        if torch.cuda.is_available():
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True
            )
        
        # Load model with quantization
        try:
            model = AutoModelForCausalLM.from_pretrained(
                model_id,
                quantization_config=bnb_config,
                device_map="auto" if torch.cuda.is_available() else None
            )
        except Exception as e:
            print(f"⚠️ 4-bit loading failed with error: {e}")
            print("Trying default load...")
            model = AutoModelForCausalLM.from_pretrained(
                model_id,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None
            )
        
        # Set up the text-generation pipeline
        generation_pipeline = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=512,
            temperature=0.1,
            top_p=0.9,
            do_sample=True,
            repetition_penalty=1.1,
            return_full_text=False
        )
        
        print("✅ Local LLM Loaded Successfully.")
        return HuggingFacePipeline(pipeline=generation_pipeline)
    
    except Exception as e:
        print(f"❌ Failed to load local LLM ({model_id}): {e}")
        # Prevent infinite recursion: only fallback if not already using the fallback model
        fallback_id = "Qwen/Qwen2.5-1.5B-Instruct"
        if model_id != fallback_id:
            print(f"⚠️ Attempting fallback to {fallback_id}...")
            return load_local_llm(model_id=fallback_id)
        else:
            print("🛑 No more fallbacks available. Please check dependencies (pip install accelerate).")
            raise e

if __name__ == "__main__":
    # Test loading
    llm = load_local_llm()
    print("Self-test prompt: 'What is NCU?'")
    print(llm.invoke("What is NCU?"))
