from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

def cosine_similarity(text1, text2, vectorizer):
    # Transform the texts into TF-IDF vectors using the provided fitted vectorizer
    text_matrix = vectorizer.transform([text1, text2])
    
    # Convert sparse matrix to dense format for easier manipulation
    text_matrix_dense = text_matrix.toarray()
    
    # Extract the vectors for text1 and text2
    vec1 = text_matrix_dense[0]
    vec2 = text_matrix_dense[1]
    
    # Calculate the dot product of the two vectors
    dot_product = np.dot(vec1, vec2)
    
    # Calculate the magnitude of each vector
    magnitude_vec1 = np.sqrt(np.dot(vec1, vec1))
    magnitude_vec2 = np.sqrt(np.dot(vec2, vec2))
    
    # Calculate cosine similarity
    if magnitude_vec1 == 0 or magnitude_vec2 == 0:
        similarity_score = 0.0  # Avoid division by zero
    else:
        similarity_score = dot_product / (magnitude_vec1 * magnitude_vec2)
    
    # Convert similarity score to percentage
    similarity_percentage = similarity_score * 100
    
    possible_sources = []
    if similarity_score > 0.3:
        possible_sources.append("SourceName")  # Example source name
    
    return similarity_score, similarity_percentage, possible_sources    


