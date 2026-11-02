"""
Prediction module - uses trained model to classify new incidents
"""
import pickle
from pathlib import Path
import yaml


class IncidentPredictor:
    """Loads trained model and predicts incident types"""
    
    def __init__(self, config_path='config/config.yaml'):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.model = None
        self.vectorizer = None
        self._load_model()
    
    def _load_model(self):
        """Load trained model and vectorizer from disk"""
        model_path = Path(self.config['ml']['model_path'])
        vectorizer_path = Path(self.config['ml']['vectorizer_path'])
        
        if not model_path.exists():
            raise FileNotFoundError(
                f"Model not found: {model_path}\n"
                "Please train the model first using: rca-gpt train"
            )
        
        if not vectorizer_path.exists():
            raise FileNotFoundError(f"Vectorizer not found: {vectorizer_path}")
        
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
        
        with open(vectorizer_path, 'rb') as f:
            self.vectorizer = pickle.load(f)
        
        print(f"✅ Model loaded from: {model_path}")
    
    def predict(self, message):
        """
        Predict incident type for a single message
        
        Args:
            message: Log message string
            
        Returns:
            Predicted incident type
        """
        if self.model is None:
            raise ValueError("Model not loaded")
        
        # Vectorize
        message_vec = self.vectorizer.transform([message])
        
        # Predict
        prediction = self.model.predict(message_vec)[0]
        
        # Get probability
        proba = self.model.predict_proba(message_vec)[0]
        confidence = max(proba)
        
        return {
            'incident_type': prediction,
            'confidence': confidence,
            'message': message
        }
    
    def predict_batch(self, messages):
        """
        Predict incident types for multiple messages
        
        Args:
            messages: List of log message strings
            
        Returns:
            List of predictions
        """
        if self.model is None:
            raise ValueError("Model not loaded")
        
        # Vectorize
        messages_vec = self.vectorizer.transform(messages)
        
        # Predict
        predictions = self.model.predict(messages_vec)
        probas = self.model.predict_proba(messages_vec)
        
        results = []
        for msg, pred, proba in zip(messages, predictions, probas):
            results.append({
                'incident_type': pred,
                'confidence': max(proba),
                'message': msg
            })
        
        return results


if __name__ == "__main__":
    # Example usage
    predictor = IncidentPredictor()
    
    test_messages = [
        "Invalid token",
        "Connection refused",
        "Timeout error",
        "Login success"
    ]
    
    for msg in test_messages:
        result = predictor.predict(msg)
        print(f"{msg:30} → {result['incident_type']:15} ({result['confidence']:.2%})")