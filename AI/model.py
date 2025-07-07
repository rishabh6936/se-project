import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from transformers import pipeline
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple
class AdvancedTopicClassifier:
    def __init__(self):
        """
        Initialize with a model specifically trained for topic classification.
        """
        # Using a model trained specifically for topic classification
        self.model_name = "cardiffnlp/tweet-topic-21-multi"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
        
        # Topic labels for this specific model
        self.topic_labels = [
            'arts_&_culture', 'business_&_entrepreneurs', 'celebrity_&_pop_culture',
            'diaries_&_daily_life', 'family', 'fashion_&_style', 'film_tv_&_video',
            'fitness_&_health', 'food_&_dining', 'gaming', 'learning_&_educational',
            'music', 'news_&_social_concern', 'other_hobbies', 'relationships',
            'science_&_technology', 'sports', 'travel_&_adventure', 'youth_&_student_life'
        ]
    
    def classify_text(self, text: str, top_k: int = 3) -> Dict:
        """
        Classify text using the dedicated topic classification model.
        """
        # Tokenize input
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
        
        # Get predictions
        with torch.no_grad():
            outputs = self.model(**inputs)
            predictions = torch.sigmoid(outputs.logits).numpy()[0]
        
        # Get top-k predictions
        top_indices = np.argsort(predictions)[-top_k:][::-1]
        top_predictions = []
        
        for idx in top_indices:
            top_predictions.append({
                'topic': self.topic_labels[idx],
                'confidence': round(float(predictions[idx]), 4)
            })
        
        return {
            'text': text,
            'predictions': top_predictions,
            'top_topic': self.topic_labels[top_indices[0]],
            'top_confidence': round(float(predictions[top_indices[0]]), 4)
        }

