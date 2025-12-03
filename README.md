# README.md

This document explains the purpose, structure, and design of the **Resume Job Matcher** project, including its system architecture, features, ranking logic, testing setup, Docker support, CI pipeline, and known limitations.

It follows the same formatting style as **REFACTORING.md** for consistency and clarity.

I explicitly focused on describing:

1. **System Features**
2. **Architecture Overview**
3. **Class Interaction Flow**
4. **Design Principles**
5. **Testing Strategy**
6. **Execution Instructions**
7. **Error Handling & Limitations**

---

## 0. Project Summary

The **Resume Job Matcher** processes a user’s resume (PDF or text), generates semantic embeddings, fetches job postings from the JSearch API, and ranks those jobs by cosine similarity to the résumé content.

The system includes:

* A modular, SOLID-based architecture
* Dependency inversion for embedding services
* A pluggable embedding model interface
* A complete unit test suite
* Docker support for reproducibility
* GitHub Actions CI for automated testing

---

## 1. Features

### Core Capabilities

* Extract text and high-level sections from résumé PDFs
* Fetch real-time job postings from the JSearch API
* Generate semantic embeddings via `SentenceTransformer`
* Compute cosine similarity between résumé and job descriptions
* Export results to `ranked_jobs.csv`

### Engineering Features

* Strict SOLID, modular architecture
* High-level logic decoupled from any specific embedding model
* Mockable embedding services for deterministic tests
* Docker container for stable, reproducible execution
* GitHub Actions CI for automated testing on every push

---

## 2. Architecture Overview

The system consists of **five primary components**, each with a single responsibility:

### a) `ResumeParser`

Extracts and structures résumé text.

### b) `HFEmbeddingService` (implements `IEmbeddingService`)

Produces embeddings for résumé text and job descriptions.
A mock implementation is used during testing.

### c) `JobFetcher`

Handles all communication with the **JSearch API**.

### d) `JobCSVHandler`

Loads raw CSV data, validates fields, and exports ranked output.

### e) `rank_jobs()`

Coordinates the end-to-end process: embeddings → similarity → ranking → CSV output.

---

## 3. Class Interaction Flow

```
resume.pdf
    │
    ▼
ResumeParser
    │
    ▼
parsed_resume.txt
    │
    ▼
EmbeddingService (via IEmbeddingService)
    │
    ▼
JobFetcher
    │
    ▼
jobs_raw.json
    │
    ▼
JobCSVHandler
    │
    ▼
jobs.csv
    │
    ▼
rank_jobs()
    │
    ▼
ranked_jobs.csv
```

This diagram shows the **full data pipeline** from user input to final ranked results.

---

## 4. Design Principles (SOLID)

### **Single Responsibility Principle (SRP)**

Each component handles exactly one job:

* **ResumeParser** → parsing
* **JobFetcher** → API calls
* **EmbeddingService** → embeddings
* **JobCSVHandler** → file I/O
* **rank_jobs()** → ranking logic

---

### **Open/Closed Principle (OCP)**

By depending on `IEmbeddingService`, the system is **extensible**:

You can add:

* OpenAI embeddings
* Cohere embeddings
* LLaMA embeddings
* Custom local embeddings

without modifying ranking logic.

---

### **Liskov Substitution Principle (LSP)**

`MockEmbeddingService` can replace `HFEmbeddingService` in any test:

```python
service: IEmbeddingService = MockEmbeddingService()
```

Everything still works.

---

### **Interface Segregation Principle (ISP)**

The embedding interface includes **only what the system needs**:

```python
get_embedding(text)
get_embeddings_batch(list)
```

No extra unused methods.

---

### **Dependency Inversion Principle (DIP)**

High-level logic depends on **abstractions**, not implementations:

```
rank_jobs() → IEmbeddingService
```

This enables swapping or mocking embedding providers easily.

---

## 5. Testing Strategy

All tests are located under `tests/`.

### Coverage Includes:

* Résumé parsing behavior
* Embedding interface behavior
* Ranking + similarity computation
* CSV load and export correctness

### Tools and Techniques

* `MockEmbeddingService` for deterministic vectors
* Sample CSVs for file-based tests
* Mocked I/O where helpful
* Automatic execution via GitHub Actions CI

Result: **fast, stable, deterministic tests**.

---

## 6. Docker Support

### Build Image

```
docker build -t job-ranker .
```

### Run Container

```
docker run --rm -v $(pwd)/output:/app/output job-ranker
```

This ensures consistent behavior across machines and environments.

---

## 7. Continuous Integration (CI)

The GitHub Actions workflow:

* Installs dependencies
* Runs the full test suite
* Blocks PRs if tests fail
* Ensures refactors cannot silently break logic

Every push to `main` automatically triggers the pipeline.

---

## 8. Example Outputs

### `ranked_jobs.csv` (excerpt)

```
title,company,similarity,location
Data Scientist,IBM,0.873,New York NY
Machine Learning Engineer,Google,0.841,Remote
Software Engineer,Amazon,0.802,Seattle WA
```

### `parsed_resume.txt` (excerpt)

```
===== EXPERIENCE =====

Software Developer Intern – Polaris Software
• Built scalable data pipelines...

===== SKILLS =====

Python, C++, SQL, AWS, Data Analysis...
```

---

## 9. Error Handling & Edge Cases

The system gracefully manages:

* Missing/unreadable PDFs
* Incomplete résumé sections
* Empty or poor-quality job results
* Embedding model runtime errors
* CSV schema mismatches
* API rate limiting

All errors include **clear, actionable** messages.

---

## 10. Limitations

* Résumé parsing is regex-based (no layout-aware ML parser yet)
* Embedding quality depends entirely on model chosen
* JSearch API stability affects ranking accuracy
* Ranking currently ignores job level, seniority, and salary

These may be improved in future versions.

---

This README provides a complete, clear overview of the system’s responsibilities, workflows, and engineering constraints.
