import hmac
import hashlib
import base64
from transformers import BertTokenizer, BertForSequenceClassification
import torch

# HMAC Functions
def generate_hmac(secret_key, message):
    hmac_object = hmac.new(secret_key.encode(), message.encode(), hashlib.sha256)
    return base64.b64encode(hmac_object.digest()).decode()

def verify_hmac(secret_key, message, signature):
    expected_signature = generate_hmac(secret_key, message)
    return hmac.compare_digest(expected_signature, signature)

# BERT Model Setup
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=2)

# Preprocess Log Message
def preprocess_log(log_message):
    inputs = tokenizer(log_message, return_tensors='pt', truncation=True, padding=True, max_length=512)
    return inputs

# Analyze Log Function
def analyze_log(log_message):
    inputs = preprocess_log(log_message)
    
    with torch.no_grad():
        outputs = model(**inputs)
    
    logits = outputs.logits
    predicted_class = torch.argmax(logits, dim=-1).item()
    
    return predicted_class

