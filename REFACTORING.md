# REFACTORING.md

This document explains the SOLID principles I applied during the refactoring of the Resume Job Matcher project, the problems they solved in the original code, how I implemented them, and other design considerations.

I explicitly focused on:

1. **Dependency Inversion Principle (DIP)**
2. **Single Responsibility Principle (SRP)**

I also considered Open/Closed Principle (OCP), Liskov Substitution (LSP), and Interface Segregation (ISP) in smaller ways.

---

## 0. Original Code Snapshot (Before Refactoring)

Before refactoring, the `rank_jobs` function instantiated a concrete `SentenceTransformer` embedding model directly:

```python
def rank_jobs(resume_text, jobs):
    model = SentenceTransformer("all-MiniLM-L6-v2")
    resume_emb = model.encode(resume_text)
    ...
```

**Problems:**

* Tight coupling to Hugging Face SentenceTransformer
* Slow unit tests requiring network access
* Difficult to swap embedding providers
* Mixed responsibilities in one function: embeddings, ranking, CSV I/O

---

## 1. Dependency Inversion Principle (DIP)

### Goal

Make high-level ranking logic depend on an **abstraction**, not a concrete embedding implementation, to allow:

* Injecting real embeddings in production
* Injecting mocks in tests
* Swapping implementations easily

### Refactoring

#### Interface Extraction

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
```

#### Concrete HFEmbeddingService

```python
class HFEmbeddingService(IEmbeddingService):
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def get_embedding(self, text: str):
        if not text.strip(): return None
        return self.model.encode(text).tolist()

    def get_embeddings_batch(self, texts: list):
        return self.model.encode(texts).tolist()
```

#### Updated `rank_jobs` Function

```python
def rank_jobs(resume_embedding, jobs, top_n=50, embedding_service=None, output_csv="ranked_jobs.csv"):
    if embedding_service is None:
        embedding_service = HFEmbeddingService()
    job_texts = [f"{job['title']} {job['company']} {job['description']}" for job in jobs]
    job_embeddings = embedding_service.get_embeddings_batch(job_texts)
    for job, emb in zip(jobs, job_embeddings):
        job["similarity_score"] = cosine_similarity(resume_embedding, emb)
    ranked_jobs = sorted(jobs, key=lambda x: x["similarity_score"], reverse=True)
    JobCSVHandler.save_jobs(ranked_jobs[:top_n], output_csv)
    return ranked_jobs[:top_n]
```

#### Mock for Unit Testing

```python
class MockEmbeddingService(IEmbeddingService):
    def get_embedding(self, text: str):
        return [1.0, 0.0, 0.0]

    def get_embeddings_batch(self, texts: list):
        return [[1.0, 0.0, 0.0] for _ in texts]
```

**Result:**
High-level logic depends on an abstraction, allowing deterministic, fast unit tests without real model/API calls.

---

## 2. Single Responsibility Principle (SRP)

### Problem

Original code mixed:

* Parsing resume text
* Handling CSV I/O
* Calling external API (JSearch)
* Embeddings + ranking
* Printing/logging

### Goal

Split code into focused classes/functions, each handling one responsibility.

### Refactoring: Focused Classes

**a) ResumeParser – parsing only**

```python
class ResumeParser:
    SECTION_PATTERNS = {...}

    def __init__(self, resume_text: str):
        self.resume_text = resume_text
        self.parsed_sections = {}

    def parse(self):
        ...

    def save_to_txt(self, filename="parsed_resume.txt"):
        ...
```

**b) JobCSVHandler – CSV I/O only**

```python
class JobCSVHandler:
    @staticmethod
    def load_jobs(filename="jsearch_jobs_data.csv"):
        ...

    @staticmethod
    def save_jobs(jobs, filename="jsearch_jobs_data.csv"):
        ...
```

**c) JobFetcher – API interaction only**

```python
class JobFetcher:
    def __init__(self, api_key: str):
        ...

    def fetch_jobs(self, query="data scientist", location="New York", max_jobs=50):
        ...
```

**Result:** Each class is easier to maintain, test, and reason about.

---

## 3. Testing Strategy

* **MockEmbeddingService** for deterministic vector embeddings
* **Mock filesystem** for CSV tests (no real file dependency)
* **Unit tests grouped by responsibility:**

  * Resume parsing
  * Embedding service behavior
  * CSV load/save
  * Ranking logic
* Allows rapid, reliable CI execution

---

## 4. Alternative Designs Considered

* **Strategy pattern for embeddings:** rejected; DI via interface simpler for our scope
* **All-in-one class for JobMatcher:** rejected; violated SRP, hard to test
* **Async API fetch:** postponed to future refactor; synchronous sufficient for POC

---

## 5. Remaining Technical Debt

* Resume parsing uses regex → may misclassify sections; ML/layout-based parser could improve accuracy
* JobFetcher synchronous → async could improve performance on large queries
* CSVHandler could validate schema against a predefined structure

---

## 6. Lessons Learned

* SOLID principles significantly improve maintainability and testability
* DI + abstractions decouple logic from libraries
* Mocking external dependencies is essential for fast unit tests
* Clear separation of responsibilities enables incremental feature additions

---

**Summary**

* **DIP:** `rank_jobs` depends on `IEmbeddingService` abstraction → decoupled, testable, flexible
* **SRP:** Split into `ResumeParser`, `JobCSVHandler`, `JobFetcher`, `HFEmbeddingService` → focused, maintainable
* Minor adherence to **OCP**, **LSP**, **ISP** strengthens modularity and extensibility

This refactoring provides a solid, testable foundation for future enhancements.
