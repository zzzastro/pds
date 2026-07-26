# CiteCat — Plagiarism Detection System

A Django web application that detects plagiarism in text submissions using TF-IDF vectorization and cosine similarity. Includes a TinyBERT-based training pipeline for ML model experimentation.

---

## How It Works

### Detection Engine (TF-IDF + Cosine Similarity)

The core detection logic lives in `apps/plagiarism/views.py`:

1. **Dataset Loading**
   - On first request, `initialize_system()` loads text from `data/raw/pds_dataset.txt` (a TSV of text pairs) or a preprocessed cache at `data/preprocessed/all_preprocessed_texts.txt`.
   - The texts form the reference corpus against which user submissions are compared.

2. **Text Preprocessing**
   - Lowercasing, punctuation removal, stopword filtering (NLTK), and Porter stemming.
   - Preprocessed texts are cached to disk so this runs only once.

3. **TF-IDF Vectorization**
   - A `TfidfVectorizer` with `ngram_range=(1, 3)` (unigrams, bigrams, trigrams) is fitted on the reference corpus.
   - Both the reference corpus and user submissions are transformed into TF-IDF vectors.

4. **Similarity Scoring**
   - Cosine similarity is computed between the user's vector and every reference vector.
   - The highest similarity score is taken as the result.
   - **Thresholds:**
     - `> 0.3` → "Plagiarism detected!"
     - `0.1 – 0.3` → "Caution: Some similarities detected!"
     - `< 0.1` → "No plagiarism detected."

5. **User Flow**
   - User pastes text or uploads a `.txt` file via the web form.
   - Results display the verdict, similarity percentage, and the index of the closest matching source text.

### ML Training Pipeline (TinyBERT)

`ml/train.py` provides a separate training script (not loaded by the Django app):

1. Loads the same `data/raw/pds_dataset.txt` dataset.
2. Combines `text1` and `text2` columns into a single input.
3. Splits into train/test sets.
4. Uses a local `ml/tinybert_model/` (pretrained TinyBERT checkpoint) with a sequence classification head (2 labels: plagiarized / not plagiarized).
5. Tokenizes at `max_length=256` with padding/truncation.
6. Trains via Hugging Face `Trainer` with FP16 mixed precision (when GPU available).
7. Saves the fine-tuned model + tokenizer to `ml/tinybert_plagiarism_model/`.

**Note:** The Django app does NOT load TinyBERT at runtime — only TF-IDF. The training pipeline is independent for experimentation.

---

## Project Structure

```
├── config/                          # Django project configuration
│   ├── settings/
│   │   ├── base.py                  # Shared settings (DB, apps, middleware)
│   │   ├── development.py           # Dev overrides (DEBUG=True)
│   │   └── production.py            # Prod overrides (DEBUG=False)
│   ├── urls.py                      # Root URL config
│   ├── wsgi.py                      # WSGI entry point
│   └── asgi.py                      # ASGI entry point
├── apps/
│   ├── accounts/                    # Auth app (signup, login, logout, profile)
│   │   ├── forms.py                 # SignupForm, LoginForm
│   │   ├── views.py                 # Auth view functions
│   │   ├── urls.py                  # /signup/, /login/, /logout/, /profile/, /delete_account/
│   │   └── templates/accounts/      # signup.html, login.html, userprofile.html
│   └── plagiarism/                  # Plagiarism detection app
│       ├── views.py                 # home() — detection logic + request handling
│       ├── models.py                # UserProfile model
│       ├── urls.py                  # / (root)
│       ├── static/                  # CSS, JS, images, fonts
│       └── templates/plagiarism/    # home.html
├── data/
│   ├── raw/pds_dataset.txt          # Training/evaluation dataset (TSV)
│   ├── preprocessed/                # Cached preprocessed texts
│   └── test_samples/                # Sample text files for manual testing
├── ml/
│   ├── train.py                     # TinyBERT training script
│   ├── tinybert_model/              # Base TinyBERT pretrained model
│   └── tinybert_plagiarism_model/   # Fine-tuned TinyBERT output
├── requirements/
│   ├── base.txt                     # Runtime dependencies (Django, sklearn, nltk, etc.)
│   ├── dev.txt                      # Dev dependencies (includes base)
│   └── train.txt                    # Training dependencies (includes base + torch, transformers)
├── nltk_data/                       # NLTK corpora (stopwords, etc.)
├── run.sh                           # Single entry point — setup + run
├── Makefile                         # Convenience commands (setup, run, check, test, clean)
├── manage.py                        # Django management script
└── .env                             # Environment variables (SECRET_KEY, DEBUG)
```

---

## Setup & Running

### Prerequisites

- Python 3.10+
- pip

### Quick Start

```bash
./run.sh
```

This single command:
1. Creates a virtual environment at `/tmp/pds_venv` (avoids NTFS filesystem issues on WSL)
2. Symlinks `venv/` → `/tmp/pds_venv`
3. Installs runtime dependencies
4. Symlinks NLTK data into the venv
5. Runs database migrations
6. Starts the dev server at `http://0.0.0.0:8000`

### Manual Steps

```bash
make setup    # or: ./run.sh (runs setup + server)
make run      # start the dev server
make check    # verify configuration
make test     # run Django tests
make clean    # remove venv + cache files
```

### Environment Variables (`.env`)

```
SECRET_KEY=django-insecure-dev-key-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

---

## Usage

1. Open `http://localhost:8000` in your browser.
2. Sign up with a username, email, password, and profession (Student/Teacher/Researcher).
3. Log in.
4. Paste text or upload a `.txt` file and click **Submit**.
5. View the plagiarism verdict, similarity percentage, and source match.

---

## Running TinyBERT Training

```bash
pip install -r requirements/train.txt
python ml/train.py
```

Requires PyTorch + Transformers. GPU recommended for reasonable training times. The fine-tuned model is saved to `ml/tinybert_plagiarism_model/`.
