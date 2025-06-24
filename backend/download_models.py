import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from config import Config
import os
import shutil

def clean_model_dirs():
    """Clean up existing model directories"""
    print("Cleaning up existing model directories...")
    if os.path.exists("models"):
        shutil.rmtree("models")
    create_model_dirs()

def create_model_dirs():
    """Create directories for model storage"""
    print("Creating model directories...")
    os.makedirs("models/tlmg4eth/model", exist_ok=True)
    os.makedirs("models/mistral", exist_ok=True)

def verify_tlmg4eth_installation():
    """Verify TLMG4ETH model files"""
    required_files = {
        'model': {
            'required': ['config.json', 'model.safetensors'],
            'optional': ['generation_config.json']
        }
    }
    
    for dir_name, files in required_files.items():
        dir_path = f'models/tlmg4eth/{dir_name}'
        if not os.path.exists(dir_path):
            print(f"Missing directory: {dir_path}")
            return False
            
        # Check required files
        for file in files['required']:
            file_path = os.path.join(dir_path, file)
            if not os.path.exists(file_path):
                print(f"Missing required file: {file_path}")
                return False
    return True

def verify_mistral_installation():
    """Verify Mistral model files"""
    required_files = {
        'model': {
            'required': ['config.json'],
            'one_of': ['pytorch_model.bin', 'model.safetensors']
        },
        'tokenizer': {
            'required': ['tokenizer_config.json'],
            'one_of': ['tokenizer.json', 'vocab.json']
        }
    }
    
    for dir_name, files in required_files.items():
        dir_path = f'models/mistral/{dir_name}'
        if not os.path.exists(dir_path):
            print(f"Missing directory: {dir_path}")
            return False
            
        # Check required files
        for file in files['required']:
            file_path = os.path.join(dir_path, file)
            if not os.path.exists(file_path):
                print(f"Missing required file: {file_path}")
                return False
        
        # Check if at least one of the optional files exists
        found_one = False
        for file in files['one_of']:
            file_path = os.path.join(dir_path, file)
            if os.path.exists(file_path):
                found_one = True
                break
        if not found_one:
            print(f"Missing one of: {', '.join(files['one_of'])}")
            return False
    return True

def download_mistral():
    """Download and save Mistral model"""
    print("\nDownloading Mistral model...")
    
    if verify_mistral_installation():
        print("Mistral model already downloaded and verified!")
        return
    
    try:
        config = Config()
        
        print("Downloading Mistral tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(
            config.MISTRAL_MODEL,
            use_fast=True
        )
        tokenizer.save_pretrained('models/mistral/tokenizer')
        
        print("Downloading Mistral model...")
        model = AutoModelForCausalLM.from_pretrained(
            config.MISTRAL_MODEL,
            torch_dtype=torch.float16,
            device_map="auto",
        )
        model.save_pretrained('models/mistral/model')
        
        if verify_mistral_installation():
            print("✓ Mistral model downloaded and verified successfully!")
        else:
            print("✗ Mistral model verification failed after download!")
    except Exception as e:
        print(f"✗ Error downloading Mistral model: {str(e)}")
        raise

def main():
    print("Starting model downloads...")
    
    try:
        # Clean up and recreate directories
        clean_model_dirs()
        
        # Download Mistral model
        download_mistral()
        
        # Verify TLMG4ETH files exist
        if not verify_tlmg4eth_installation():
            print("\n⚠️ TLMG4ETH model files not found!")
            print("Please ensure you have the TLMG4ETH model files in models/tlmg4eth/model/")
            print("Required files: config.json, model.safetensors")
        
        # Final verification
        tlmg4eth_ok = verify_tlmg4eth_installation()
        mistral_ok = verify_mistral_installation()
        
        if tlmg4eth_ok and mistral_ok:
            print("\n✓ All models verified successfully!")
        else:
            failed = []
            if not tlmg4eth_ok:
                failed.append("TLMG4ETH")
            if not mistral_ok:
                failed.append("Mistral")
            print(f"\n✗ Some models failed verification: {', '.join(failed)}")
            
    except Exception as e:
        print(f"\n✗ Error during model download process: {str(e)}")
        print("Please check your internet connection and try again.")
        print("If the error persists, you may need to manually download the models.")

if __name__ == "__main__":
    main() 