Project 2 — AI-Powered Job Ranking System

This project processes a user’s résumé, fetches current job postings, generates semantic embeddings, and ranks jobs by similarity to the résumé. It uses SOLID principles, dependency inversion, unit tests, Docker, and a CI workflow to create a scalable and testable architecture.

🚀 Features

Extract text and structured sections from any PDF résumé

Fetch real-time job listings from the JSearch API

Generate sentence embeddings using the SentenceTransformer model

Rank job descriptions by cosine similarity

Export results to ranked_jobs.csv

Modular OOP architecture following SOLID

Complete unit test suite with mocks

Dockerized application

GitHub Actions CI for automatic test execution on every push

🧱 Architecture Overview

The app is divided into five cleanly separated components:

1. ResumeParser

Extracts résumé text, detects core sections, and returns structured data.

2. HFEmbeddingService (implements IEmbeddingService)

Generates embeddings using a pluggable model.
Mock version used for testing.

3. JobFetcher

Communicates with the JSearch API and returns normalized job listings.

4. JobCSVHandler

Loads, validates, and exports job data.

5. rank_jobs()

Consumes embeddings + job list → outputs ranked jobs CSV.

🔗 Class Interaction Diagram
resume.pdf
   │
   ▼
ResumeParser ─────────────► parsed_resume.txt
   │
   ▼
EmbeddingService (via IEmbeddingService)
   │
   ▼
JobFetcher ───────────────► jobs_raw.json
   │
   ▼
JobCSVHandler ────────────► jobs.csv
   │
   ▼
rank_jobs() ──────────────► ranked_jobs.csv

🧠 SOLID Principles Applied
S — Single Responsibility

Each class handles exactly one responsibility:

ResumeParser → text extraction only

JobFetcher → API calls only

EmbeddingService → embeddings only

CSVHandler → CSV I/O only

O — Open/Closed Principle

IEmbeddingService allows adding new models (OpenAI, Cohere, LLaMA)
without modifying rank_jobs().

L — Liskov Substitution

MockEmbeddingService and HFEmbeddingService can be swapped freely in tests:

service: IEmbeddingService = MockEmbeddingService()

I — Interface Segregation

IEmbeddingService exposes only:

get_embedding(text)
get_embeddings_batch(list)


No unnecessary methods.

D — Dependency Inversion

High-level ranking logic depends on interfaces, not concrete classes.

🧪 Testing Strategy

Full unit test suite under tests/

MockEmbeddingService provides deterministic vectors

Sample CSVs used for repeatable file-based tests

Tests cover:

Resume parsing

Embedding interface behavior

Job CSV loading/export

Ranking logic

CI workflow runs tests on every push to main

📦 Docker Support
Build:
docker build -t job-ranker .

Run:
docker run --rm -v $(pwd)/output:/app/output job-ranker


This ensures consistent execution and eliminates environment differences.

🧪 Continuous Integration (CI)

A GitHub Actions workflow automatically:

Installs dependencies

Runs the entire test suite

Blocks PRs if tests fail

Ensures refactors never break functionality

Every push triggers the pipeline.

📁 Example Outputs
ranked_jobs.csv (excerpt)
title,company,similarity,location
Data Scientist,IBM,0.873,New York, NY
Machine Learning Engineer,Google,0.841,Remote
Software Engineer,Amazon,0.802,Seattle, WA

parsed_resume.txt (excerpt)
===== EXPERIENCE =====
Software Developer Intern – Polaris Software
• Built scalable data pipelines...

===== SKILLS =====
Python, C++, SQL, AWS, Data Analysis...

⚠️ Error Handling & Edge Cases

The system gracefully manages:

Missing or unreadable PDF

Empty résumé sections

API returning zero job posts

Embedding model errors

CSV schema mismatches

Rate limits from JSearch

All major failures log readable error messages.

🔍 Limitations

Résumé parsing is regex-based (no layout-aware ML yet)

Embedding quality depends on the chosen model

API results depend on JSearch availability

Ranking does not yet consider job seniority or salary