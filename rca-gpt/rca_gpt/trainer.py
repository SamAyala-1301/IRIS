"""
ML Model Training Module
"""
import pandas as pd
import pickle
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
import yaml


class IncidentClassifier:
    """Trains and saves incident classification model"""
    
    def __init__(self, config_path='config/config.yaml'):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.model = None
        self.vectorizer = None
        self.classes = None
    
    def load_training_data(self, data_path=None):
        """
        Load labeled training data
        
        Args:
            data_path: Path to training CSV (uses config if None)
            
        Returns:
            X (messages), y (labels)
        """
        if data_path is None:
            data_path = self.config['data']['training_data_csv']
        
        data_path = Path(data_path)
        
        if not data_path.exists():
            raise FileNotFoundError(
                f"Training data not found: {data_path}\n"
                "Please create training data with labeled incidents."
            )
        
        df = pd.read_csv(data_path)
        
        # Filter only labeled rows
        df = df[df['incident_type'].notna()]
        
        if len(df) == 0:
            raise ValueError("No labeled data found in training file")
        
        print(f"Loaded {len(df)} labeled examples")
        print(f"Incident types: {df['incident_type'].unique().tolist()}")
        
        return df['message'], df['incident_type']
    
    def train(self, X=None, y=None, test_size=None, random_state=None):
        """
        Train the classification model
        
        Args:
            X: Messages (loads from config if None)
            y: Labels (loads from config if None)
            test_size: Train/test split ratio
            random_state: Random seed for reproducibility
            
        Returns:
            dict with training metrics
        """
        # Load data if not provided
        if X is None or y is None:
            X, y = self.load_training_data()
        
        # Get config values
        if test_size is None:
            test_size = self.config['ml']['test_size']
        if random_state is None:
            random_state = self.config['ml']['random_state']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        
        print(f"\nTraining set: {len(X_train)} samples")
        print(f"Test set: {len(X_test)} samples")
        
        # Vectorize
        print("\nVectorizing text...")
        self.vectorizer = TfidfVectorizer()
        X_train_vec = self.vectorizer.fit_transform(X_train)
        X_test_vec = self.vectorizer.transform(X_test)
        
        # Train
        print("Training model...")
        self.model = LogisticRegression(max_iter=1000)
        self.model.fit(X_train_vec, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test_vec)
        
        print("\n" + "="*60)
        print("📊 MODEL EVALUATION")
        print("="*60)
        print(classification_report(y_test, y_pred))
        
        # Store classes
        self.classes = self.model.classes_.tolist()
        
        return {
            'train_size': len(X_train),
            'test_size': len(X_test),
            'classes': self.classes,
            'accuracy': self.model.score(X_test_vec, y_test)
        }
    
    def save_model(self, model_path=None, vectorizer_path=None):
        """
        Save trained model and vectorizer to disk
        
        Args:
            model_path: Where to save model (uses config if None)
            vectorizer_path: Where to save vectorizer (uses config if None)
        """
        if self.model is None or self.vectorizer is None:
            raise ValueError("No trained model to save. Call train() first.")
        
        # Get paths from config
        if model_path is None:
            model_path = self.config['ml']['model_path']
        if vectorizer_path is None:
            vectorizer_path = self.config['ml']['vectorizer_path']
        
        model_path = Path(model_path)
        vectorizer_path = Path(vectorizer_path)
        
        # Create directories
        model_path.parent.mkdir(parents=True, exist_ok=True)
        vectorizer_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save
        with open(model_path, 'wb') as f:
            pickle.dump(self.model, f)
        
        with open(vectorizer_path, 'wb') as f:
            pickle.dump(self.vectorizer, f)
        
        print(f"\n✅ Model saved to: {model_path}")
        print(f"✅ Vectorizer saved to: {vectorizer_path}")
        
        return model_path, vectorizer_path
    
    def train_and_save(self):
        """Convenience method: train and save in one call"""
        self.train()
        return self.save_model()


if __name__ == "__main__":
    classifier = IncidentClassifier()
    classifier.train_and_save()