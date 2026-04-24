"""
Training Module — feeds example CVs into the vector knowledge base.
Agents retrieve relevant training examples at runtime via RAG
(Retrieval-Augmented Generation) from ChromaDB.

Usage:
    trainer = CVTrainer()
    trainer.ingest_cv("training/data/cv_software_eng_good.pdf",
                      label="good", job_role="Software Engineer")
    trainer.ingest_cv("training/data/cv_bad_example.docx",
                      label="bad", job_role="General")
"""

from __future__ import annotations
import json
import uuid
from pathlib import Path
from datetime import datetime

from langchain_chroma import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from tools.file_handler import read_cv_file
from config import CHROMA_DB_PATH, TRAINING_DATA_PATH


EMBEDDING_MODEL = "all-MiniLM-L6-v2"


class CVTrainer:
    """
    Manages a ChromaDB vector store of training CV examples.
    Agents query this store during analysis to ground their reasoning
    in real-world good/bad CV examples.
    """

    def __init__(self) -> None:
        self.embeddings = SentenceTransformerEmbeddings(
            model_name=EMBEDDING_MODEL
        )
        self.vector_store = Chroma(
            collection_name    = "cv_training_examples",
            embedding_function = self.embeddings,
            persist_directory  = CHROMA_DB_PATH,
        )
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size    = 800,
            chunk_overlap = 100,
        )
        Path(TRAINING_DATA_PATH).mkdir(parents=True, exist_ok=True)

    def ingest_cv(
        self,
        file_path: str,
        label: str,            # "good" | "bad" | "mediocre"
        job_role: str,
        industry: str = "General",
        notes: str    = "",
    ) -> str:
        """
        Reads a CV file and stores chunked embeddings in ChromaDB.
        Returns the document ID for reference.
        """
        doc_id = str(uuid.uuid4())
        text, fmt = read_cv_file(file_path)
        chunks = self.splitter.split_text(text)

        metadata_base = {
            "doc_id":   doc_id,
            "label":    label,
            "job_role": job_role,
            "industry": industry,
            "format":   fmt,
            "notes":    notes,
            "source":   file_path,
            "ingested_at": datetime.utcnow().isoformat(),
        }

        documents = []
        metadatas = []
        ids       = []

        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_chunk_{i}"
            # Prefix each chunk with structured context
            enriched_chunk = (
                f"[TRAINING EXAMPLE]\n"
                f"Label: {label.upper()}\n"
                f"Job Role: {job_role}\n"
                f"Industry: {industry}\n"
                f"Notes: {notes}\n\n"
                f"{chunk}"
            )
            documents.append(enriched_chunk)
            metadatas.append({**metadata_base, "chunk_index": i})
            ids.append(chunk_id)

        self.vector_store.add_texts(
            texts     = documents,
            metadatas = metadatas,
            ids       = ids,
        )

        print(
            f"[Trainer] Ingested '{file_path}' as '{label}' CV "
            f"for role '{job_role}'. "
            f"Chunks stored: {len(chunks)}. Doc ID: {doc_id}"
        )
        return doc_id

    def retrieve_examples(
        self,
        query: str,
        job_role: str  = "",
        label: str     = "",
        top_k: int     = 5,
    ) -> list[str]:
        """
        Retrieves the most relevant training examples for a given query.
        Used by agents to ground their reasoning in training data.
        """
        filter_dict = {}
        if job_role:
            filter_dict["job_role"] = job_role
        if label:
            filter_dict["label"] = label

        results = self.vector_store.similarity_search(
            query     = query,
            k         = top_k,
            filter    = filter_dict if filter_dict else None,
        )

        return [doc.page_content for doc in results]

    def get_good_cv_examples(self, job_role: str, top_k: int = 3) -> str:
        """Shorthand: fetch top good CV examples for a role."""
        examples = self.retrieve_examples(
            query    = f"professional high-standard CV for {job_role}",
            job_role = job_role,
            label    = "good",
            top_k    = top_k,
        )
        return "\n\n---\n\n".join(examples)

    def get_bad_cv_examples(self, job_role: str, top_k: int = 3) -> str:
        """Shorthand: fetch top bad CV examples for a role."""
        examples = self.retrieve_examples(
            query    = f"poorly written CV common mistakes {job_role}",
            job_role = job_role,
            label    = "bad",
            top_k    = top_k,
        )
        return "\n\n---\n\n".join(examples)

    def list_ingested_cvs(self) -> list[dict]:
        """Returns metadata of all ingested training CVs."""
        results = self.vector_store.get(include=["metadatas"])
        seen_docs: dict = {}
        for meta in results.get("metadatas", []):
            doc_id = meta.get("doc_id", "")
            if doc_id and doc_id not in seen_docs:
                seen_docs[doc_id] = meta
        return list(seen_docs.values())
