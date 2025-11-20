from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from ..config import settings as app_settings
from loguru import logger
import uuid


class VectorService:
    """Service for managing vector embeddings and semantic search using ChromaDB"""

    def __init__(self):
        # Lazy initialization - client will be created on first use
        self._client = None
        self.default_collection_name = "coaching_sessions"

    @property
    def client(self):
        """Lazy initialization of ChromaDB client"""
        if self._client is None:
            self._client = chromadb.HttpClient(
                host=app_settings.CHROMA_HOST,
                port=app_settings.CHROMA_PORT,
                settings=Settings(
                    chroma_client_auth_provider="chromadb.auth.token.TokenAuthClientProvider",
                    chroma_client_auth_credentials="",
                    allow_reset=True
                )
            )
        return self._client

    def get_or_create_collection(self, collection_name: str = None):
        """Get or create a collection"""
        name = collection_name or self.default_collection_name
        try:
            return self.client.get_or_create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            logger.error(f"Error creating collection {name}: {str(e)}")
            raise

    def get_user_collection(self, user_id: int):
        """Get or create a user-specific collection"""
        collection_name = f"user_{user_id}_sessions"
        return self.get_or_create_collection(collection_name)

    async def store_message(
        self,
        user_id: int,
        session_id: int,
        message_id: int,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store a message with its embedding

        Args:
            user_id: User ID
            session_id: Chat session ID
            message_id: Message ID
            role: Message role (user/assistant/system)
            content: Message content
            metadata: Additional metadata

        Returns:
            Document ID in ChromaDB
        """
        try:
            collection = self.get_user_collection(user_id)

            doc_id = f"msg_{message_id}_{uuid.uuid4().hex[:8]}"

            message_metadata = {
                "session_id": session_id,
                "message_id": message_id,
                "role": role,
                **(metadata or {})
            }

            collection.add(
                documents=[content],
                metadatas=[message_metadata],
                ids=[doc_id]
            )

            logger.info(f"Stored message {message_id} in vector DB with ID {doc_id}")
            return doc_id

        except Exception as e:
            logger.error(f"Error storing message in vector DB: {str(e)}")
            raise

    async def search_similar_messages(
        self,
        user_id: int,
        query: str,
        n_results: int = 5,
        session_filter: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar messages in user's history

        Args:
            user_id: User ID
            query: Search query
            n_results: Number of results to return
            session_filter: Optional session ID to filter by

        Returns:
            List of similar messages with metadata
        """
        try:
            collection = self.get_user_collection(user_id)

            where_filter = None
            if session_filter:
                where_filter = {"session_id": session_filter}

            results = collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter
            )

            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    formatted_results.append({
                        "content": doc,
                        "metadata": results['metadatas'][0][i],
                        "distance": results['distances'][0][i] if 'distances' in results else None
                    })

            return formatted_results

        except Exception as e:
            logger.error(f"Error searching vector DB: {str(e)}")
            return []

    async def get_session_messages(
        self,
        user_id: int,
        session_id: int
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all messages from a specific session

        Args:
            user_id: User ID
            session_id: Session ID

        Returns:
            List of messages from the session
        """
        try:
            collection = self.get_user_collection(user_id)

            results = collection.get(
                where={"session_id": session_id}
            )

            formatted_results = []
            if results['documents']:
                for i, doc in enumerate(results['documents']):
                    formatted_results.append({
                        "content": doc,
                        "metadata": results['metadatas'][i],
                        "id": results['ids'][i]
                    })

            return formatted_results

        except Exception as e:
            logger.error(f"Error retrieving session messages: {str(e)}")
            return []

    async def analyze_user_patterns(
        self,
        user_id: int,
        time_window_days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze patterns in user's conversations for progress reporting

        Args:
            user_id: User ID
            time_window_days: Time window for analysis

        Returns:
            Analysis results with patterns and insights
        """
        try:
            collection = self.get_user_collection(user_id)

            # Get all user messages (role='user')
            results = collection.get(
                where={"role": "user"}
            )

            if not results['documents']:
                return {
                    "message_count": 0,
                    "insights": "Not enough data for analysis"
                }

            # Basic analysis
            message_count = len(results['documents'])
            messages = results['documents']

            # Calculate average message length
            avg_length = sum(len(msg) for msg in messages) / message_count if message_count > 0 else 0

            # Identify common themes using simple keyword analysis
            # In production, this would use more sophisticated NLP
            business_keywords = ['client', 'customer', 'sale', 'business', 'meeting', 'negotiation']
            leadership_keywords = ['team', 'leader', 'manage', 'decision', 'strategy']

            business_count = sum(
                1 for msg in messages
                if any(keyword in msg.lower() for keyword in business_keywords)
            )
            leadership_count = sum(
                1 for msg in messages
                if any(keyword in msg.lower() for keyword in leadership_keywords)
            )

            return {
                "message_count": message_count,
                "avg_message_length": avg_length,
                "business_focus": business_count / message_count if message_count > 0 else 0,
                "leadership_focus": leadership_count / message_count if message_count > 0 else 0,
                "insights": f"Analyzed {message_count} messages"
            }

        except Exception as e:
            logger.error(f"Error analyzing user patterns: {str(e)}")
            return {"error": str(e)}

    async def delete_session_data(
        self,
        user_id: int,
        session_id: int
    ):
        """Delete all messages from a session"""
        try:
            collection = self.get_user_collection(user_id)

            # Get all IDs for the session
            results = collection.get(
                where={"session_id": session_id}
            )

            if results['ids']:
                collection.delete(ids=results['ids'])
                logger.info(f"Deleted {len(results['ids'])} messages from session {session_id}")

        except Exception as e:
            logger.error(f"Error deleting session data: {str(e)}")
            raise


# Singleton instance
vector_service = VectorService()
