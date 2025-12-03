import unittest
from unittest.mock import patch
from main import (
    ResumeParser,
    cosine_similarity,
    JobCSVHandler,
    rank_jobs,
)
from mock_embedding_service import MockEmbeddingService


# -----------------------------
# ResumeParser Tests
# -----------------------------
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

    def test_parse_no_sections(self):
        """Resume with no recognizable section headings should return empty dict."""
        text = "Just some random text with no section headers at all."
        parser = ResumeParser(text)
        sections = parser.parse()
        self.assertEqual(sections, {})

    def test_parse_mixed_case_and_spacing(self):
        """Headings with weird case / spacing should still be recognized."""
        text = """
        work history
        Did stuff

          Education
        School Name

          skills
        Python, C++
        """
        parser = ResumeParser(text)
        sections = parser.parse()

        self.assertIn("experience", sections)
        self.assertIn("education", sections)
        self.assertIn("skills", sections)

        self.assertIn("Did stuff", sections["experience"])
        self.assertIn("School Name", sections["education"])
        self.assertIn("Python, C++", sections["skills"])

    def test_parse_multi_line_section(self):
        """Multiple lines in a section should be joined with newlines."""
        text = """
        EXPERIENCE
        Line one at job
        Line two at job
        """
        parser = ResumeParser(text)
        sections = parser.parse()

        self.assertIn("experience", sections)
        self.assertEqual(
            sections["experience"],
            "Line one at job\nLine two at job"
        )


# -----------------------------
# Cosine Similarity Tests
# -----------------------------
class TestCosineSimilarity(unittest.TestCase):

    def test_similarity_identical(self):
        v1 = [1, 0]
        v2 = [1, 0]
        self.assertAlmostEqual(cosine_similarity(v1, v2), 1.0)

    def test_similarity_orthogonal(self):
        v1 = [1, 0]
        v2 = [0, 1]
        self.assertAlmostEqual(cosine_similarity(v1, v2), 0.0)

    def test_similarity_opposite(self):
        """Opposite vectors should give -1.0 cosine similarity."""
        v1 = [1, 0]
        v2 = [-1, 0]
        self.assertAlmostEqual(cosine_similarity(v1, v2), -1.0)


# -----------------------------
# Rank Jobs Using MockEmbeddingService
# Demonstrates DIP & Mocking!
# -----------------------------
class TestRankJobs(unittest.TestCase):

    def test_rank_jobs_with_mock(self):
        """Basic happy path: 2 jobs, top_n=2, all scores == 1.0."""
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
        self.assertAlmostEqual(ranked[1]["similarity_score"], 1.0)

    def test_rank_jobs_no_jobs(self):
        """If jobs list is empty, rank_jobs should return empty list."""
        mock_service = MockEmbeddingService()
        ranked = rank_jobs(
            resume_embedding=[1, 0, 0],
            jobs=[],
            top_n=5,
            embedding_service=mock_service,
            output_csv="test_ranked_jobs_empty.csv"
        )
        self.assertEqual(ranked, [])

    def test_rank_jobs_top_n_smaller_than_jobs(self):
        """When top_n < number of jobs, only top_n jobs are returned."""
        class OrderedMockEmbeddingService(MockEmbeddingService):
            # Return slightly different embeddings per job to force ordering
            def get_embeddings_batch(self, texts):
                # Make the first job "best", others slightly worse
                embs = []
                for i, _ in enumerate(texts):
                    embs.append([1.0 - 0.1 * i, 0.0, 0.0])
                return embs

        mock_service = OrderedMockEmbeddingService()

        resume_emb = [1, 0, 0]

        jobs = [
            {"title": "BestJob", "company": "A", "description": "desc1"},
            {"title": "OkayJob", "company": "B", "description": "desc2"},
            {"title": "WorseJob", "company": "C", "description": "desc3"},
        ]

        ranked = rank_jobs(
            resume_embedding=resume_emb,
            jobs=jobs,
            top_n=2,
            embedding_service=mock_service,
            output_csv="test_ranked_jobs_top2.csv"
        )

        # Only top 2 jobs should be returned
        self.assertEqual(len(ranked), 2)
        # First job should be BestJob based on mocked scores
        self.assertEqual(ranked[0]["title"], "BestJob")


# -----------------------------
# CSV Handler Tests
# -----------------------------
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

    @patch("os.path.exists", return_value=False)
    def test_load_jobs_missing_file(self, _):
        """If file does not exist, should return empty list and empty DataFrame."""
        jobs, df = JobCSVHandler.load_jobs("missing.csv")
        self.assertEqual(jobs, [])
        self.assertTrue(df.empty)

    @patch("os.path.exists", return_value=True)
    @patch("os.path.getsize", return_value=0)
    def test_load_jobs_empty_file(self, *_):
        """If file is empty, should return empty list and empty DataFrame."""
        jobs, df = JobCSVHandler.load_jobs("empty.csv")
        self.assertEqual(jobs, [])
        self.assertTrue(df.empty)

    @patch("os.path.exists", return_value=True)
    @patch("os.path.getsize", return_value=100)
    @patch("pandas.read_csv", side_effect=Exception("boom"))
    def test_load_jobs_read_error(self, *_):
        """If pandas.read_csv raises, we should handle it and return empty results."""
        jobs, df = JobCSVHandler.load_jobs("bad.csv")
        self.assertEqual(jobs, [])
        self.assertTrue(df.empty)


if __name__ == "__main__":
    unittest.main()
