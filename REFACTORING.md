`REFACTORING.md`

# REFACTORING.md

This document explains which SOLID principles I focused on, what problems they solved in the original design, and how I implemented the refactorings.

I explicitly focused on:

1. **Dependency Inversion Principle (DIP)**
2. **Single Responsibility Principle (SRP)**

---

## 1. Dependency Inversion Principle (DIP)

### Problem in Original Code

In the original design (before refactoring), the ranking logic depended directly on a specific embedding implementation (e.g., a `SentenceTransformer` model from Hugging Face), usually instantiated inside the function itself. This caused several issues:

- The ranking code was tightly coupled to a concrete external library.
- It was difficult to unit test because loading a real model is slow and requires network access.
- It was hard to swap out the embedding provider (different model, API, or a mock implementation).

### Goal

Make the high-level ranking logic depend on an **abstraction**, not a specific embedding implementation. This allows:

- Injecting a real embedding service in production.
- Injecting a mock embedding service in tests.
- Swapping underlying implementations with minimal code changes.

### Refactoring: `IEmbeddingService` + concrete implementations

#### After: Extraction of an interface

```python
from abc import ABC, abstractmethod

class IEmbeddingService(ABC):
    """Interface for any embedding service."""

    @abstractmethod
    def get_embedding(self, text: str):
        pass

    @abstractmethod
    def get_embeddings_batch(self, texts: list):
        pass

After: Concrete HF implementation

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

After: rank_jobs depends on the abstraction

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
After: Mock embedding service for tests


from main import IEmbeddingService

class MockEmbeddingService(IEmbeddingService):
    """Mock version of the embedding service for unit testing."""

    def get_embedding(self, text: str):
        # Return deterministic fake vector
        return [1.0, 0.0, 0.0]

    def get_embeddings_batch(self, texts: list):
        # Return one fake vector per text
        return [[1.0, 0.0, 0.0] for _ in texts]
After: Unit test using the mock implementation


class TestRankJobs(unittest.TestCase):

    def test_rank_jobs_with_mock(self):
        mock_service = MockEmbeddingService()

        resume_emb = [1, 0, 0]

        jobs = [
            {"title": "Job1", "company": "A", "description": "desc1"},
            {"title": "Job2", "company": "B", "description": "desc2"},
        ]

        ranked = rank_jobs(
            resume_embedding=resume_emb,
            jobs=jobs,
            top_n=2,
            embedding_service=mock_service,
            output_csv="test_ranked_jobs.csv"
        )

        # All embeddings are identical → scores must match
        self.assertEqual(len(ranked), 2)
        self.assertIn("similarity_score", ranked[0])
        self.assertAlmostEqual(ranked[0]["similarity_score"], 1.0)

Result
High-level logic (rank_jobs) no longer depends on a concrete embedding model.

I can fully test the ranking logic using a fast mock, without downloading or running a heavy model.

The design follows DIP: depend on abstractions (IEmbeddingService), not concretions.

2. Single Responsibility Principle (SRP)
Problem in Original Code
The initial script (before refactoring) tended to mix multiple responsibilities together:

Parsing resume text.

Handling CSV file I/O.

Calling an external API (JSearch).

Performing embedding and ranking logic.

Handling printing to the console.

Having all this in a single place makes the code harder to:

Understand and maintain.

Reuse individual parts in other contexts.

Test each responsibility in isolation.

Goal
Split the code into classes/functions where each has a clear, single responsibility.

Refactoring: separation into focused classes
a) ResumeParser – responsible for parsing resumes

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

        self.parsed_sections = {k: "\n".join(v).strip() for k, v in sections.items() if v}
        return self.parsed_sections

    def save_to_txt(self, filename="parsed_resume.txt"):
        with open(filename, "w", encoding="utf-8") as txtfile:
            for section, content in self.parsed_sections.items():
                txtfile.write(f"\n===== {section.upper()} =====\n")
                txtfile.write(content + "\n")
        print(f"✅ Saved parsed resume to {filename}")
Unit test focused only on parsing:


class TestResumeParser(unittest.TestCase):

    def test_parse_sections(self):
        text = """
        EXPERIENCE
        Worked at Google

        EDUCATION
        SIUE

        SKILLS
        Python, C++
        """

        parser = ResumeParser(text)
        sections = parser.parse()

        self.assertIn("experience", sections)
        self.assertIn("education", sections)
        self.assertIn("skills", sections)

        self.assertEqual(sections["experience"], "Worked at Google")
        self.assertEqual(sections["skills"], "Python, C++")
b) JobCSVHandler – responsible for CSV I/O

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
Unit test with mocks (no real files needed):


class TestCSVHandler(unittest.TestCase):

    @patch("os.path.exists", return_value=True)
    @patch("os.path.getsize", return_value=100)
    @patch("pandas.read_csv")
    def test_load_jobs(self, mock_read_csv, *_):
        df_mock = mock_read_csv.return_value
        df_mock.to_dict.return_value = [{"title": "Data Scientist"}]

        jobs, df = JobCSVHandler.load_jobs("fake.csv")
        self.assertEqual(len(jobs), 1)
        self.assertIsNotNone(df)

c) JobFetcher – responsible for external API interaction

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
Result
ResumeParser handles only parsing/saving resume sections.

JobCSVHandler handles only CSV read/write.

JobFetcher handles only API calls and job object creation.

HFEmbeddingService handles only embeddings.

rank_jobs handles only similarity scoring and ranking.

This follows SRP and makes the codebase easier to maintain, reason about, and test in isolation.

Summary
DIP: Introduced IEmbeddingService and used dependency injection so that rank_jobs depends on an abstraction. This decouples the ranking logic from the specific embedding model and enables fast, deterministic unit tests using MockEmbeddingService.

SRP: Split the code into focused classes (ResumeParser, JobCSVHandler, JobFetcher, etc.), each with a single well-defined responsibility, improving maintainability and testability of the system.
```
