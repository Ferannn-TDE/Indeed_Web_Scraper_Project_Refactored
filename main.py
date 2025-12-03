import os
import re
import pdfplumber
import pandas as pd
import requests
from abc import ABC, abstractmethod
from scipy.spatial.distance import cosine
from sentence_transformers import SentenceTransformer

# -----------------------------
# Interface for Embedding Service (DIP)
# -----------------------------
class IEmbeddingService(ABC):
    """Interface for any embedding service."""

    @abstractmethod
    def get_embedding(self, text: str):
        pass

    @abstractmethod
    def get_embeddings_batch(self, texts: list):
        pass

# -----------------------------
# Concrete Hugging Face Embedding Service
# -----------------------------
class HFEmbeddingService(IEmbeddingService):
    """Implements IEmbeddingService using SentenceTransformer from Hugging Face."""

    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def get_embedding(self, text: str):
        if not text.strip():
            return None
        return self.model.encode(text).tolist()

    def get_embeddings_batch(self, texts: list):
        return self.model.encode(texts).tolist()

# -----------------------------
# Resume Parser (SRP)
# -----------------------------
class ResumeParser:
    """Parses a resume PDF into structured sections."""

    SECTION_PATTERNS = {
        "experience": r"(experience|work history|employment)",
        "education": r"(education|academic background)",
        "skills": r"(skills|technical skills|abilities)",
        "projects": r"(projects|personal projects|academic projects)",
        "leadership & awards": r"(leadership|awards|honors|scholarship)"
    }

    def __init__(self, resume_text: str):
        self.resume_text = resume_text
        self.parsed_sections = {}

    def parse(self):
        sections = {key: [] for key in self.SECTION_PATTERNS.keys()}
        current_section = None

        for line in self.resume_text.splitlines():
            clean_line = line.strip()
            if not clean_line:
                continue
            for key, pat in self.SECTION_PATTERNS.items():
                if re.search(pat, clean_line.lower()):
                    current_section = key
                    break
            else:
                if current_section:
                    sections[current_section].append(clean_line)

        self.parsed_sections = {
            k: "\n".join(v).strip()
            for k, v in sections.items()
            if v
        }
        return self.parsed_sections

    def save_to_txt(self, filename="parsed_resume.txt"):
        with open(filename, "w", encoding="utf-8") as txtfile:
            for section, content in self.parsed_sections.items():
                txtfile.write(f"\n===== {section.upper()} =====\n")
                txtfile.write(content + "\n")
        print(f"✅ Saved parsed resume to {filename}")

# -----------------------------
# Cosine Similarity Utility
# -----------------------------
def cosine_similarity(vec1, vec2):
    """Compute cosine similarity between two vectors."""
    return 1 - cosine(vec1, vec2)

# -----------------------------
# Job CSV Handler (SRP)
# -----------------------------
class JobCSVHandler:
    """Handles reading and writing job CSV files."""

    @staticmethod
    def load_jobs(filename="jsearch_jobs_data.csv"):
        if not os.path.exists(filename) or os.path.getsize(filename) == 0:
            print(f"⚠️ {filename} missing or empty.")
            return [], pd.DataFrame()
        try:
            df = pd.read_csv(filename)
            return df.to_dict(orient="records"), df
        except Exception as e:
            print(f"❌ Error reading {filename}: {e}")
            return [], pd.DataFrame()

    @staticmethod
    def save_jobs(jobs, filename="jsearch_jobs_data.csv"):
        if not jobs:
            print(f"⚠️ No jobs to save to {filename}.")
            return
        df = pd.DataFrame(jobs)
        df.to_csv(filename, index=False)
        print(f"✅ Saved {len(jobs)} jobs to {filename}")

# -----------------------------
# Job Fetcher (SRP)
# -----------------------------
class JobFetcher:
    """Fetch jobs from the JSearch API."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_host = "jsearch.p.rapidapi.com"
        self.url = f"https://{self.api_host}/search"

    def fetch_jobs(self, query="data scientist", location="New York", max_jobs=50):
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.api_host
        }

        jobs = []
        page = 1
        while len(jobs) < max_jobs:
            params = {"query": query, "location": location, "num_pages": 1, "page": page}
            try:
                response = requests.get(self.url, headers=headers, params=params)
                if response.status_code != 200:
                    print(f"❌ API request failed with status code {response.status_code}")
                    break

                data = response.json().get("data", [])
                if not data:
                    print("⚠️ No more jobs returned from API.")
                    break

                for job in data:
                    jobs.append({
                        "title": job.get("job_title", ""),
                        "company": job.get("employer_name", ""),
                        "publisher": job.get("job_publisher", ""),
                        "employment_type": job.get("job_employment_type", ""),
                        "description": job.get("job_description", ""),
                        "location": job.get("job_city", "") + ", " + job.get("job_country", "")
                    })

                page += 1
                if len(jobs) >= max_jobs:
                    break

            except Exception as e:
                print(f"❌ API request error: {e}")
                break

        jobs = jobs[:max_jobs]
        if jobs:
            JobCSVHandler.save_jobs(jobs)
        else:
            print("⚠️ No jobs fetched from API.")
        return jobs

# -----------------------------
# Rank Jobs (SRP)
# -----------------------------
def rank_jobs(resume_embedding, jobs, top_n=50, embedding_service=None, output_csv="ranked_jobs.csv"):
    """Rank jobs based on cosine similarity to resume embedding."""
    if not jobs:
        print("⚠️ No jobs to rank.")
        return []

    if embedding_service is None:
        embedding_service = HFEmbeddingService()

    job_texts = [f"{job['title']} {job['company']} {job['description']}" for job in jobs]
    job_embeddings = embedding_service.get_embeddings_batch(job_texts)
    for job, emb in zip(jobs, job_embeddings):
        job["similarity_score"] = cosine_similarity(resume_embedding, emb)

    ranked_jobs = sorted(jobs, key=lambda x: x["similarity_score"], reverse=True)
    JobCSVHandler.save_jobs(ranked_jobs[:top_n], output_csv)
    return ranked_jobs[:top_n]

# -----------------------------
# PDF Text Extraction Utility
# -----------------------------
def extract_text_from_pdf(file_path):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()

# -----------------------------
# MAIN SCRIPT
# -----------------------------
if __name__ == "__main__":
    # Step 1: Extract text from resume PDF
    resume_text = extract_text_from_pdf("Oluwaferanmi Resume_3Sep.pdf")

    # Step 2: Parse resume
    parser = ResumeParser(resume_text)
    parser.parse()
    parser.save_to_txt()

    # Step 3: Create embedding
    embedding_service = HFEmbeddingService()
    resume_embedding = embedding_service.get_embedding(resume_text)
    print("✅ Resume embedding created.")

    # Step 4: Fetch jobs from API (use env var instead of hard-coded key)
    API_KEY = os.getenv("JSEARCH_API_KEY")
    if not API_KEY:
        raise RuntimeError("❌ Environment variable JSEARCH_API_KEY is not set.")

    job_fetcher = JobFetcher(api_key=API_KEY)
    jobs = job_fetcher.fetch_jobs(query="data scientist", location="New York", max_jobs=50)

    # Step 5: Rank jobs and save top 10
    top_jobs = rank_jobs(
        resume_embedding=resume_embedding,
        jobs=jobs,
        top_n=50,
        embedding_service=embedding_service,
        output_csv="ranked_jobs.csv"
    )

    # Step 6: Print top matching jobs
    print("\n🎯 Top Matching Jobs:")
    for job in top_jobs:
        print(f"{job['title']} at {job['company']} ({job['location']}) -> Similarity: {job['similarity_score']:.4f}")
