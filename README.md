# Resume Job Matcher (Refactored P2)

This project parses a resume, generates an embedding for it, fetches job postings from the JSearch API, and ranks those jobs by semantic similarity to the resume using cosine similarity.

The codebase has been refactored to follow SOLID principles and is covered by unit tests.

---

## Features

- Extract text from a resume PDF.
- Parse the resume into structured sections (Experience, Education, Skills, etc.).
- Generate embeddings for the resume and job descriptions using a Hugging Face `SentenceTransformer` model.
- Fetch job postings from the JSearch API and save them to CSV.
- Rank jobs by cosine similarity between the resume embedding and job embeddings.
- Save ranked jobs to a separate CSV.
- Run unit tests using a mock embedding service (no real model/API calls during tests).

---

## Project Structure

```text
Refactored_P2/
├── main.py                    # Main application logic
├── test_app.py                # Unit tests
├── mock_embedding_service.py  # Mock implementation of IEmbeddingService for tests
├── requirements.txt           # Python dependencies
├── jsearch_jobs_data.csv      # Raw jobs CSV (created by the app)
├── ranked_jobs.csv            # Ranked jobs CSV (created by the app)
├── parsed_resume.txt          # Parsed resume sections (created by the app)
├── Oluwaferanmi Resume_3Sep.pdf  # Example resume PDF (input)
├── README.md
└── REFACTORING.md
Requirements
Python 3.10+

Dependencies are listed in requirements.txt:

pdfplumber
sentence-transformers
scipy
pandas
requests
Install them with:

pip install -r requirements.txt


A resume PDF named Oluwaferanmi Resume_3Sep.pdf is in the project root.

You have a valid JSearch API key.

In main.py, you’ll see:

python main.py

This will:

Extract text from Oluwaferanmi Resume_3Sep.pdf.

Parse the resume into sections and save them into parsed_resume.txt.

Create an embedding for the full resume text using HFEmbeddingService.

Fetch up to 50 jobs from the JSearch API with:

query="data scientist"

location="New York"

Generate embeddings for all job descriptions.

Compute cosine similarity between the resume embedding and each job embedding.

Sort jobs by similarity score and save the top 10 to ranked_jobs.csv.

Print the top matching jobs in the terminal, e.g.:

🎯 Top Matching Jobs:
Data Scientist at Example Corp (New York, United States) -> Similarity: 0.8734
...
How to Run the Test Suite
All tests are in test_app.py and use MockEmbeddingService from mock_embedding_service.py, so they do not call the real embedding model or external API.

From the project root, run:

python -m unittest test_app.py
or use test discovery:

python -m unittest discover
If everything is set up correctly, you should see something like:

....
----------------------------------------------------------------------
Ran 4 tests in 0.0s

OK
The tests cover:

ResumeParser.parse – verifies sections like EXPERIENCE, EDUCATION, SKILLS are parsed correctly.

cosine_similarity – verifies similarity between simple vectors.

rank_jobs – uses a mock embedding service to ensure ranking and CSV writing behavior is correct.

JobCSVHandler.load_jobs – uses mocks for filesystem and pandas.read_csv to test CSV loading logic.


🐳 Docker Usage

This project includes a Dockerfile so you can run the app in a container.

1. Build the Docker Image

From the project root (Refactored_P2), run:

docker build -t resume-job-matcher .


-t resume-job-matcher gives the image a name.

. tells Docker to use the current directory as the build context.

2. Run the Container
Simple run (API key hardcoded in main.py)

If your main.py still has the API key hardcoded, you can just run:

docker run --rm resume-job-matcher

Better: pass API key via environment variable

If you change main.py to read from an environment variable:

import os
API_KEY = os.getenv("JSEARCH_API_KEY")


Then run the container like this:

docker run --rm -e JSEARCH_API_KEY="your_real_key_here" resume-job-matcher

3. Using a Local Resume File (Optional)

If you don’t bake the resume PDF into the image and want to mount it instead:

Remove the PDF from the image build (or just ignore it).

In main.py, make sure you refer to a path like ./Oluwaferanmi Resume_3Sep.pdf.

Run:

docker run --rm \
  -v "$(pwd)/Oluwaferanmi Resume_3Sep.pdf:/app/Oluwaferanmi Resume_3Sep.pdf" \
  -e JSEARCH_API_KEY="your_real_key_here" \
  resume-job-matcher


This mounts the local PDF into /app inside the container (which is your working directory from the Dockerfile).
```
# Indeed_Web_Scraper_Project_Refactored
