from django.contrib.auth.decorators import login_required
import os
import numpy as np
import pandas as pd
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.http import HttpResponse
import logging
import re
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine_similarity
from django.shortcuts import render

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

trained_texts = None
vectorizer = None
trained_vectors = None
stop_words = set(stopwords.words('english'))
stemmer = PorterStemmer()

def load_dataset():
    logger.info("Test Case: Dataset Loading - Starting")

    preprocessed_file_path = settings.BASE_DIR / 'data' / 'preprocessed' / 'all_preprocessed_texts.txt'

    if os.path.exists(preprocessed_file_path):
        logger.info("Preprocessed file found, loading data from file.")
        try:
            with open(preprocessed_file_path, 'r', encoding='utf-8') as f:
                preprocessed_texts = f.readlines()
                logger.info("Preprocessed file loaded successfully.")
            return [text.strip() for text in preprocessed_texts]
        except Exception as e:
            logger.error(f"Error loading preprocessed file: {e}")
            return []
    else:
        logger.info("Preprocessed file not found, proceeding with dataset loading and preprocessing.")
        dataset_path = settings.BASE_DIR / 'data' / 'raw' / 'pds_dataset.txt'
        try:
            data = pd.read_csv(dataset_path, sep='\t', header=None, names=['text1', 'text2', 'label'])
            logger.info("Dataset loaded successfully.")
            return data['text1'].tolist() + data['text2'].tolist()
        except Exception as e:
            logger.error(f"Error loading dataset: {e}")
            return []

def preprocess_text(text):
    if isinstance(text, str):
        logger.info("Test Case: Text Preprocessing - Starting")
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        text = ' '.join(word for word in text.split() if word not in stop_words)
        text = ' '.join(stemmer.stem(word) for word in text.split())
        logger.info("Test Case: Text Preprocessing - Successfully processed text.")
        return text

    logger.warning("Test Case: Text Preprocessing - Input is not a string")
    return ""

def save_all_preprocessed_texts(preprocessed_texts):
    output_file_path = settings.BASE_DIR / 'data' / 'preprocessed' / 'all_preprocessed_texts.txt'

    try:
        with open(output_file_path, 'w', encoding='utf-8') as f:
            for text in preprocessed_texts:
                f.write(text + '\n')
        logger.info(f"All preprocessed texts saved to {output_file_path}")
    except Exception as e:
        logger.error(f"Error saving preprocessed texts: {e}")

def initialize_system():
    global trained_texts, vectorizer, trained_vectors
    logger.info("Test Case: System Initialization - Starting")

    trained_texts = load_dataset()
    if not trained_texts:
        logger.error("Failed to load dataset. trained_texts is empty.")
        return False

    logger.info(f"Loaded {len(trained_texts)} texts.")

    if not os.path.exists(settings.BASE_DIR / 'data' / 'preprocessed' / 'all_preprocessed_texts.txt'):
        logger.info("Preprocessing texts...")
        preprocessed_texts = [preprocess_text(text) for text in trained_texts]
        save_all_preprocessed_texts(preprocessed_texts)
    else:
        logger.info("Using already preprocessed texts.")

    logger.info("Initializing TfidfVectorizer...")
    vectorizer = TfidfVectorizer(ngram_range=(1, 3))

    logger.info("Fitting and transforming texts...")
    trained_vectors = vectorizer.fit_transform(trained_texts)

    logger.info("System initialized successfully.")
    return True

@login_required(login_url='login')
def home(request):
    global trained_texts, vectorizer, trained_vectors
    logger.info("Home view accessed")
    if trained_texts is None or vectorizer is None or trained_vectors is None:
        logger.info("System not initialized. Initializing now...")
        if not initialize_system():
            logger.error("Failed to initialize the system")
            return HttpResponse("Error: Failed to initialize the system. Please check the logs.")

    similarity_score_message = None
    similarity_percentage = None
    possible_sources = []

    if request.method == 'POST':
        logger.info("POST request received")

        submitted_text = request.POST.get('submitted_text', '')
        uploaded_file = request.FILES.get('uploaded_file')

        if submitted_text:
            logger.info("Processing submitted text")
            processed_text = preprocess_text(submitted_text)
            submitted_vector = vectorizer.transform([processed_text])
            similarity_scores = sklearn_cosine_similarity(submitted_vector, trained_vectors)
            max_similarity = np.max(similarity_scores)

            if max_similarity > 0.3:
                logger.info("Plagiarism detected for submitted text.")
            else:
                logger.info("No significant plagiarism detected for submitted text.")

        elif uploaded_file:
            logger.info("Processing uploaded file")

            if isinstance(uploaded_file, UploadedFile):
                text_to_analyze = uploaded_file.read().decode('utf-8')

                processed_text = preprocess_text(text_to_analyze)
                submitted_vector = vectorizer.transform([processed_text])
                similarity_scores = sklearn_cosine_similarity(submitted_vector, trained_vectors)
                max_similarity = np.max(similarity_scores)

                if max_similarity > 0.3:
                    logger.info("Plagiarism detected for uploaded file.")
                else:
                    logger.info("No significant plagiarism detected for uploaded file.")
            else:
                logger.error("Invalid file upload")
                return HttpResponse("Error: Invalid file upload")

        else:
            logger.warning("No input provided")
            return HttpResponse("Error: Please provide either text input or upload a file")

        try:
            max_similarity_index = np.argmax(similarity_scores)
            similarity_percentage = max_similarity * 100

            if max_similarity > 0.3:
                similarity_score_message = "Plagiarism detected!"
                possible_sources.append(f"Similar to text at index {max_similarity_index} in the dataset")
            elif max_similarity > 0.1:
                similarity_score_message = "Caution: Some similarities detected!"
            else:
                similarity_score_message = "No plagiarism detected."

            logger.info(f"Similarity score message: {similarity_score_message}")
            logger.info(f"Similarity percentage: {similarity_percentage}")
            logger.info(f"Possible sources: {possible_sources}")

        except Exception as e:
            logger.error(f"Error during similarity calculation: {str(e)}")
            return HttpResponse(f"An error occurred: {str(e)}")

    logger.info("Rendering template")

    return render(request, 'plagiarism/home.html', {
        'similarity_score': similarity_score_message,
        'similarity_percentage': similarity_percentage,
        'possible_sources': possible_sources,
    })
