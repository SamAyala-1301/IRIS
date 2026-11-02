"""
Similarity matching for incidents using TF-IDF
"""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from .db.manager import IncidentDatabase


class SimilarityMatcher:
    """Find similar incidents using TF-IDF + cosine similarity"""
    
    def __init__(self, config_path='config/config.yaml'):
        self.db = IncidentDatabase(config_path)
        self.vectorizer = TfidfVectorizer(max_features=100)
        self.incident_vectors = {}
        self.incident_ids = []
        self._build_index()
    
    def _build_index(self):
        """Build TF-IDF index from all incidents"""
        incidents = self.db.get_recent_incidents(limit=1000)
        
        if not incidents:
            return
        
        messages = [inc.message_template for inc in incidents]
        self.incident_ids = [inc.id for inc in incidents]
        
        # Build TF-IDF matrix
        self.tfidf_matrix = self.vectorizer.fit_transform(messages)
        
        print(f"✓ Indexed {len(incidents)} incidents for similarity search")
    
    def find_similar(self, message, top_k=5, threshold=0.3):
        """
        Find similar incidents
        
        Args:
            message: Current incident message
            top_k: Number of results
            threshold: Minimum similarity score (0-1)
            
        Returns:
            List of (incident_id, similarity_score)
        """
        if len(self.incident_ids) == 0:
            return []
        
        # Vectorize query
        query_vec = self.vectorizer.transform([message])
        
        # Calculate similarities
        similarities = cosine_similarity(query_vec, self.tfidf_matrix)[0]
        
        # Get top K above threshold
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            score = similarities[idx]
            if score >= threshold:
                results.append((self.incident_ids[idx], float(score)))
        
        return results
    
    def get_similar_with_context(self, message, top_k=3):
        """
        Find similar incidents with full context
        
        Returns:
            List of dicts with incident details and resolutions
        """
        similar_ids = self.find_similar(message, top_k=top_k)
        
        results = []
        for incident_id, score in similar_ids:
            incident = self.db.get_incident_by_id(incident_id)
            if not incident:
                continue
            
            # Get last occurrence to check resolution
            occurrences = self.db.get_incident_occurrences(incident_id, limit=1)
            resolution = None
            if occurrences and occurrences[0].resolved:
                resolution = {
                    'notes': occurrences[0].resolution_notes,
                    'resolved_by': occurrences[0].resolved_by,
                    'resolved_at': occurrences[0].resolved_at
                }
            
            results.append({
                'incident': incident.to_dict(),
                'similarity': score,
                'resolution': resolution
            })
        
        return results