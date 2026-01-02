import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Optional
from datetime import datetime
from config import settings
from .embeddings import EmbeddingGenerator


class VectorStore:
    """
    Vector store for RAG using ChromaDB.
    Stores calendar events and user patterns for semantic search.
    """

    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.chromadb_path,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.embedding_generator = EmbeddingGenerator()

        # Collections for different types of data
        self.events_collection = self.client.get_or_create_collection(
            name="calendar_events",
            metadata={"description": "Historical calendar events"}
        )
        self.patterns_collection = self.client.get_or_create_collection(
            name="user_patterns",
            metadata={"description": "Learned user behavior patterns"}
        )

    def add_event(self, event: Dict) -> None:
        """
        Add a calendar event to the vector store.

        Args:
            event: Calendar event dictionary from Google Calendar API
        """
        event_id = event.get('id')
        summary = event.get('summary', 'Untitled Event')
        description = event.get('description', '')
        start = event.get('start', {}).get('dateTime', '')
        end = event.get('end', {}).get('dateTime', '')

        # Create searchable text from event
        text = f"{summary}. {description}"

        # Generate embedding
        embedding = self.embedding_generator.generate_embedding(text)

        # Store in ChromaDB
        self.events_collection.add(
            ids=[event_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[{
                "summary": summary,
                "description": description,
                "start": start,
                "end": end,
                "created_at": datetime.utcnow().isoformat()
            }]
        )

    def add_events_batch(self, events: List[Dict]) -> None:
        """
        Add multiple calendar events in batch.

        Args:
            events: List of calendar event dictionaries
        """
        if not events:
            return

        ids = []
        embeddings = []
        documents = []
        metadatas = []

        for event in events:
            event_id = event.get('id')
            summary = event.get('summary', 'Untitled Event')
            description = event.get('description', '')
            start = event.get('start', {}).get('dateTime', '')
            end = event.get('end', {}).get('dateTime', '')

            text = f"{summary}. {description}"

            ids.append(event_id)
            documents.append(text)
            metadatas.append({
                "summary": summary,
                "description": description,
                "start": start,
                "end": end,
                "created_at": datetime.utcnow().isoformat()
            })

        # Generate embeddings in batch
        embeddings = self.embedding_generator.generate_embeddings(documents)

        # Store in ChromaDB
        self.events_collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

    def search_similar_events(self, query: str, n_results: int = 5) -> List[Dict]:
        """
        Search for similar events using semantic search.

        Args:
            query: Search query text
            n_results: Number of results to return

        Returns:
            List of similar events with metadata
        """
        query_embedding = self.embedding_generator.generate_embedding(query)

        results = self.events_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

        # Format results
        similar_events = []
        if results['ids'] and results['ids'][0]:
            for i in range(len(results['ids'][0])):
                similar_events.append({
                    'id': results['ids'][0][i],
                    'document': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None
                })

        return similar_events

    def add_pattern(self, pattern_id: str, pattern_text: str, metadata: Dict) -> None:
        """
        Add a learned user pattern to the vector store.

        Args:
            pattern_id: Unique identifier for the pattern
            pattern_text: Description of the pattern
            metadata: Additional metadata about the pattern
        """
        embedding = self.embedding_generator.generate_embedding(pattern_text)

        metadata["created_at"] = datetime.utcnow().isoformat()

        self.patterns_collection.add(
            ids=[pattern_id],
            embeddings=[embedding],
            documents=[pattern_text],
            metadatas=[metadata]
        )

    def search_patterns(self, query: str, n_results: int = 3) -> List[Dict]:
        """
        Search for relevant user patterns.

        Args:
            query: Search query text
            n_results: Number of results to return

        Returns:
            List of relevant patterns with metadata
        """
        query_embedding = self.embedding_generator.generate_embedding(query)

        results = self.patterns_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

        # Format results
        patterns = []
        if results['ids'] and results['ids'][0]:
            for i in range(len(results['ids'][0])):
                patterns.append({
                    'id': results['ids'][0][i],
                    'document': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None
                })

        return patterns

    def get_event_count(self) -> int:
        """Get the total number of stored events."""
        return self.events_collection.count()

    def get_pattern_count(self) -> int:
        """Get the total number of stored patterns."""
        return self.patterns_collection.count()
