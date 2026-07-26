from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments
)
import torch
from torch.utils.data import DataLoader

# Load the dataset
dataset_path = Path(__file__).resolve().parent.parent / 'data' / 'raw' / 'pds_dataset.txt'
data = pd.read_csv(dataset_path, sep='\t', header=None, names=['text1', 'text2', 'label'])

# Combine text1 and text2 for training
data['combined_text'] = data['text1'] + " " + data['text2']
data['combined_text'] = data['combined_text'].fillna("")  # Fill NaN values

X = data['combined_text']
y = data['label']

# Split the dataset into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Use a smaller subset of the data for quick testing (optional)
data_sample = data.sample(frac=0.1, random_state=42)  # Use only 10% of the dataset
X_train, X_test, y_train, y_test = train_test_split(data_sample['combined_text'], data_sample['label'], test_size=0.2, random_state=42)

# Load TinyBERT tokenizer and model from local directory
model_dir = Path(__file__).resolve().parent / 'tinybert_model'
tokenizer = AutoTokenizer.from_pretrained(model_dir, local_files_only=True)
model = AutoModelForSequenceClassification.from_pretrained(model_dir, num_labels=2, local_files_only=True)

# Tokenize the dataset with max_length specified: Adjusted maximum sequence length
max_length = 256 

train_encodings = tokenizer(list(X_train), truncation=True, padding=True, max_length=max_length)
test_encodings = tokenizer(list(X_test), truncation=True, padding=True, max_length=max_length)

class PlagiarismDataset(torch.utils.data.Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx])
        return item

    def __len__(self):
        return len(self.labels)

# Create datasets
train_dataset = PlagiarismDataset(train_encodings, y_train.to_numpy())
test_dataset = PlagiarismDataset(test_encodings, y_test.to_numpy())

# Use DataLoader for optimized data loading with multiple workers
train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True, num_workers=4)
test_loader = DataLoader(test_dataset, batch_size=128)

# Set up training arguments for TinyBERT model training with mixed precision
training_args = TrainingArguments(
    output_dir='./results',
    num_train_epochs=2,
    per_device_train_batch_size=64,
    per_device_eval_batch_size=128,
    warmup_steps=500,
    weight_decay=0.01,
    logging_dir='./logs',
    eval_strategy="epoch",
    save_total_limit=2,
    fp16=torch.cuda.is_available(),
)

# Create a Trainer instance using DataLoader instead of direct datasets for better performance
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=test_dataset,
)

# Train the model with gradient accumulation if needed (for larger effective batch sizes)
trainer.train()

# Evaluate the model's performance on the test set.
trainer.evaluate()

# Save the trained model and tokenizer for future use
model.save_pretrained('./tinybert_plagiarism_model')
tokenizer.save_pretrained('./tinybert_plagiarism_model')
