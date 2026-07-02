"""
=============================================================
EMBEDDINGS SERVICE
=============================================================
Handles generating vector embeddings for menu item documents
and search queries using Google Gemini's embedding models.

NOTE: Uses google.generativeai directly (instead of
langchain_google_genai) because langchain-google-genai<=2.0.6
calls the v1beta endpoint which does NOT support
text-embedding-004. The google.generativeai SDK always uses
the stable v1 endpoint.
=============================================================
"""

import logging
from typing import List
import google.generativeai as genai
import config

logger = logging.getLogger(__name__)


class EmbeddingsService:
    """Service to generate embeddings using Google GenAI / Gemini."""

    def __init__(self):
        self.enabled = False
        self.model = config.EMBEDDING_MODEL

        if not config.GEMINI_API_KEY:
            logger.error("[ERROR] GEMINI_API_KEY is not set in environment. Embeddings will fail.")
            return

        try:
            genai.configure(api_key=config.GEMINI_API_KEY)
            self.enabled = True
            logger.info(f"[OK] google.generativeai embeddings initialised with model: {self.model}")
        except Exception as e:
            logger.error(f"[ERROR] Failed to initialise embeddings (model={self.model}): {str(e)}")

    # ------------------------------------------------------------------
    # Internal helper
    # ------------------------------------------------------------------
    def _mock_vector(self, text: str) -> List[float]:
        """Deterministic pseudo-random vector used when API is unavailable."""
        import hashlib, random
        h = hashlib.sha256(text.encode("utf-8")).digest()
        random.seed(int.from_bytes(h[:4], "big"))
        return [random.uniform(-0.1, 0.1) for _ in range(768)]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def embed_query(self, text: str) -> List[float]:
        """
        Generate an embedding vector for a search query.

        Args:
            text: Query string

        Returns:
            List[float]: 768-dimensional vector (text-embedding-004)
        """
        if not self.enabled:
            logger.warning(f"⚠️ Embeddings not available — using mock vector for query: '{text}'")
            return self._mock_vector(text)

        try:
            result = genai.embed_content(
                model=self.model,
                content=text,
                task_type="retrieval_query"
            )
            return result["embedding"]
        except Exception as e:
            logger.error(f"Error embedding query '{text}': {str(e)}")
            raise

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embedding vectors for a batch of documents.

        Args:
            texts: List of document strings

        Returns:
            List[List[float]]: One 768-dim vector per document
        """
        if not self.enabled:
            logger.warning(f"⚠️ Embeddings not available — using mock vectors for {len(texts)} documents.")
            return [self._mock_vector(t) for t in texts]

        try:
            vectors = []
            for text in texts:
                result = genai.embed_content(
                    model=self.model,
                    content=text,
                    task_type="retrieval_document"
                )
                vectors.append(result["embedding"])
            return vectors
        except Exception as e:
            logger.error(f"Error embedding batch of {len(texts)} documents: {str(e)}")
            raise

