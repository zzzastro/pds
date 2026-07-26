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
from sklearn.exceptions import NotFittedError
from django.shortcuts import render, redirect
from django.http import JsonResponse
from plagiarism.models import Submission
import io
import joblib
from pathlib import Path

CACHE_DIR = settings.BASE_DIR / 'data' / 'cache'

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

def initialize_system(force=False):
    global trained_texts, vectorizer, trained_vectors
    logger.info("Test Case: System Initialization - Starting")

    if not force:
        vec_path = CACHE_DIR / 'vectorizer.joblib'
        vecs_path = CACHE_DIR / 'vectors.joblib'
        if vec_path.exists() and vecs_path.exists():
            logger.info("Cache found, loading from disk...")
            trained_texts = load_dataset()
            vectorizer = joblib.load(vec_path)
            trained_vectors = joblib.load(vecs_path)
            logger.info(f"Loaded {len(trained_texts)} texts.")
            logger.info("System initialized successfully (from cache).")
            logger.info("Cache was loaded from disk successfully. Initialization speed increased.")
            return True

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

    os.makedirs(CACHE_DIR, exist_ok=True)
    joblib.dump(vectorizer, CACHE_DIR / 'vectorizer.joblib')
    joblib.dump(trained_vectors, CACHE_DIR / 'vectors.joblib')
    logger.info("Saved vectorizer and vectors to cache.")

    logger.info("System initialized successfully.")
    return True

@login_required(login_url='login')
def initialize_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)

    global trained_texts, vectorizer, trained_vectors
    force = request.POST.get('force') == '1'

    if force:
        for f in ['vectorizer.joblib', 'vectors.joblib']:
            p = CACHE_DIR / f
            if p.exists():
                p.unlink()
        trained_texts = None
        vectorizer = None
        trained_vectors = None

    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)

    try:
        success = initialize_system(force=force)
        logs = log_stream.getvalue()
        request.session['init_method'] = 'manual'
        return JsonResponse({
            'success': success,
            'initialized': trained_texts is not None,
            'logs': logs,
        })
    except Exception as e:
        return JsonResponse({'success': False, 'logs': log_stream.getvalue(), 'error': str(e)})
    finally:
        logger.removeHandler(handler)
        handler.close()

@login_required(login_url='login')
def home(request):
    global trained_texts, vectorizer, trained_vectors
    logger.info("Home view accessed")

    if request.method == 'POST':
        logger.info("POST request received")

        if trained_texts is None or vectorizer is None or trained_vectors is None:
            if not initialize_system():
                logger.error("Failed to initialize the system")
                return HttpResponse("Error: Failed to initialize the system. Please check the logs.")
            request.session['init_method'] = 'auto'

        try:
            vectorizer.transform(['test'])
        except NotFittedError:
            logger.info("Vectorizer not fitted. Re-initializing...")
            initialize_system(force=True)

        submitted_text = request.POST.get('submitted_text', '')
        uploaded_file = request.FILES.get('uploaded_file')

        if submitted_text:
            logger.info("Processing submitted text")
            processed_text = preprocess_text(submitted_text)
            submitted_vector = vectorizer.transform([processed_text])
            similarity_scores = sklearn_cosine_similarity(submitted_vector, trained_vectors)
            max_similarity = np.max(similarity_scores)

        elif uploaded_file:
            logger.info("Processing uploaded file")
            if not isinstance(uploaded_file, UploadedFile):
                return HttpResponse("Error: Invalid file upload")
            text_to_analyze = uploaded_file.read().decode('utf-8')
            processed_text = preprocess_text(text_to_analyze)
            submitted_vector = vectorizer.transform([processed_text])
            similarity_scores = sklearn_cosine_similarity(submitted_vector, trained_vectors)
            max_similarity = np.max(similarity_scores)

        else:
            return HttpResponse("Error: Please provide either text input or upload a file")

        try:
            max_similarity_index = np.argmax(similarity_scores)
            similarity_percentage = max_similarity * 100

            if max_similarity > 0.3:
                similarity_score_message = "Plagiarism detected!"
                possible_sources = [f"Similar to text at index {max_similarity_index} in the dataset"]
            elif max_similarity > 0.1:
                similarity_score_message = "Caution: Some similarities detected!"
                possible_sources = []
            else:
                similarity_score_message = "No plagiarism detected."
                possible_sources = []

            Submission.objects.create(
                user=request.user,
                input_text=submitted_text,
                uploaded_file_name=uploaded_file.name if uploaded_file else '',
                result=similarity_score_message,
                similarity_percentage=similarity_percentage,
                possible_sources=', '.join(possible_sources),
            )

            request.session['result_score'] = similarity_score_message
            request.session['result_pct'] = similarity_percentage
            request.session['result_sources'] = possible_sources

        except Exception as e:
            logger.error(f"Error during similarity calculation: {str(e)}")
            return HttpResponse(f"An error occurred: {str(e)}")

        return redirect('home')

    similarity_score_message = request.session.pop('result_score', None)
    similarity_percentage = request.session.pop('result_pct', None)
    possible_sources = request.session.pop('result_sources', None)

    cache_exists = (CACHE_DIR / 'vectorizer.joblib').exists() and (CACHE_DIR / 'vectors.joblib').exists()

    init_method = request.session.get('init_method')
    if cache_exists and init_method is None:
        init_method = 'cached'

    logger.info("Rendering template")

    return render(request, 'plagiarism/home.html', {
        'similarity_score': similarity_score_message,
        'similarity_percentage': similarity_percentage,
        'possible_sources': possible_sources,
        'cache_exists': cache_exists,
        'init_method': init_method,
    })

@login_required(login_url='login')
def download_dataset(request):
    dataset_path = settings.BASE_DIR / 'data' / 'raw' / 'pds_dataset.txt'
    if not dataset_path.exists():
        return HttpResponse('File not found', status=404)
    with open(dataset_path, 'r', encoding='utf-8') as f:
        content = f.read()
    response = HttpResponse(content, content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename="pds_dataset.txt"'
    return response
