from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
import os
import numpy as np
import pandas as pd
from django.core.files.uploadedfile import UploadedFile
from django.http import HttpResponse
import logging
import re
import time
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine_similarity
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import SignupForm, LoginForm
from .models import UserProfile




def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            # Create UserProfile instance after saving User
            profession = form.cleaned_data['profession']  # Use cleaned_data for profession
            UserProfile.objects.create(user=user, profession=profession)
            
            messages.success(request, "Signup successful! You can now log in.")
            return redirect('login')
    else:
        form = SignupForm()
    
    return render(request, 'plagiarism/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            # Authenticate the user
            username_or_email = form.cleaned_data['username_or_email']
            password = form.cleaned_data['password']

            # Try to find user by username or email
            user = None
            if '@' in username_or_email:
                try:
                    user = User.objects.get(email=username_or_email)
                except User.DoesNotExist:
                    pass
            else:
                try:
                    user = User.objects.get(username=username_or_email)
                except User.DoesNotExist:
                    pass

            # Check the password and log the user in
            if user and user.check_password(password):
                login(request, user)  # Use the correct login function
                return redirect('home')  # Redirect to the home page or dashboard
            else:
                form.add_error(None, "Invalid username/email or password.")
    else:
        form = LoginForm()

    return render(request, 'plagiarism/login.html', {'form': form})

@login_required(login_url='login')
def delete_account(request):
    user = request.user
    user_profile = user.userprofile
    user.delete()  # Delete the user
    user_profile.delete()  # Optionally, delete the associated user profile
    return redirect('login')  # Redirect to the login page after account deletion

@login_required(login_url='login')
def userprofile(request):
    user_profile = request.user.userprofile
    return render(request, 'plagiarism/userprofile.html', {
        'user_profile': user_profile,
    }) 

def logout_view(request):
    logout(request)  # Log out the user
    return redirect('login')  # Redirect to the login page after logging out










""""-------------------------------------------------------------------------------------------------------------------------"""
# Import Firestore integration functions
from .firestore_integration import initialize_firestore, upload_submission, retrieve_submissions

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

trained_texts = None
vectorizer = None
trained_vectors = None
stop_words = set(stopwords.words('english'))
stemmer = PorterStemmer()
submission_count = 0  # Global counter for submissions

def load_dataset():
    logger.info("Test Case: Dataset Loading - Starting")

    # Path to the preprocessed text file
    preprocessed_file_path = r'C:\Users\hp\Desktop\Code Projects\pds\plagiarism_detection_system\preprocessed\all_preprocessed_texts.txt'
    
    # Check if the preprocessed text file exists
    if os.path.exists(preprocessed_file_path):
        logger.info("Preprocessed file found, loading data from file.")
        try:
            with open(preprocessed_file_path, 'r', encoding='utf-8') as f:
                preprocessed_texts = f.readlines()
                logger.info("Preprocessed file loaded successfully.")
            return [text.strip() for text in preprocessed_texts]  # Clean newlines and return
        except Exception as e:
            logger.error(f"Error loading preprocessed file: {e}")
            return []  # Return empty list in case of error

    # If preprocessed file doesn't exist, process the dataset and create the file
    else:
        logger.info("Preprocessed file not found, proceeding with dataset loading and preprocessing.")
        # Proceed with the old method of loading and preprocessing if the file doesn't exist
        dataset_path = r'C:\Users\hp\Desktop\Code Projects\pds\pds_dataset.txt'
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
        text = re.sub(r'[^\w\s]', '', text)  # Keep alphanumeric characters
        text = ' '.join(word for word in text.split() if word not in stop_words)
        text = ' '.join(stemmer.stem(word) for word in text.split())
        logger.info("Test Case: Text Preprocessing - Successfully processed text.")
        return text
    
    logger.warning("Test Case: Text Preprocessing - Input is not a string")
    return ""

def save_all_preprocessed_texts(preprocessed_texts):
    # Save all preprocessed texts to a user-readable format file.
    output_file_path = r'C:\Users\hp\Desktop\Code Projects\pds\plagiarism_detection_system\preprocessed\all_preprocessed_texts.txt'
    
    try:
        with open(output_file_path, 'w', encoding='utf-8') as f:
            for text in preprocessed_texts:
                f.write(text + '\n')  # Write each preprocessed text on a new line
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
    
    if not os.path.exists(r'C:\Users\hp\Desktop\Code Projects\pds\plagiarism_detection_system\preprocessed\all_preprocessed_texts.txt'):
        logger.info("Preprocessing texts...")
    
        # Preprocess each text and collect them for saving later.
        preprocessed_texts = [preprocess_text(text) for text in trained_texts]
    
        # Save all preprocessed texts to a single file.
        save_all_preprocessed_texts(preprocessed_texts)
    else:
        logger.info("Using already preprocessed texts.")
    
    logger.info("Initializing TfidfVectorizer...")
    vectorizer = TfidfVectorizer(ngram_range=(1, 3))
    
    logger.info("Fitting and transforming texts...")
    trained_vectors = vectorizer.fit_transform(trained_texts) # Use the raw or preprocessed text
    
    logger.info("System initialized successfully.")
    return True

# Initialize Firestore once at the start of the view or application.
initialize_firestore()

def retrain_model():
    global trained_texts, vectorizer, trained_vectors
    logger.info("Retraining model...")
    
    original_data = load_dataset()
    
    new_submissions = retrieve_submissions('submissions')
    
    combined_data = original_data + [submission['text'] for submission in new_submissions.values()]
    
    processed_data = [preprocess_text(text) for text in combined_data]
    
    # Save all preprocessed texts to a single file.
    save_all_preprocessed_texts(processed_data)
    
    vectorizer.fit(processed_data)
    trained_vectors = vectorizer.transform(processed_data)

@login_required(login_url='login')
def home(request):
    global trained_texts, vectorizer, trained_vectors, submission_count
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

            if max_similarity > 0.3:  # Threshold percentage
                data = {'text': submitted_text}
                upload_submission('submissions', 'submission_' + str(int(time.time())), data)
                submission_count += 1
                
                if submission_count >= 50:
                    retrain_model()
                    submission_count = 0
            
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

                if max_similarity > 0.3:  # Threshold percentage
                    data = {'text': text_to_analyze}
                    upload_submission('submissions', uploaded_file.name, data)
                    submission_count += 1
                    
                    if submission_count >= 50:
                        retrain_model()
                        submission_count = 0
                
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