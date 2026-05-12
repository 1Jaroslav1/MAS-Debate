from typing import List
from datetime import datetime
import hashlib

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue, Range
from langchain_openai import OpenAIEmbeddings

from .model import RetrievedDocument


class VectorDBManager:
    """Manages vector database operations with Qdrant and team context support"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        collection_name: str = "knowledge_base",
    ):
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = collection_name
        self.embeddings = OpenAIEmbeddings()

        # Create collection if it doesn't exist
        try:
            self.client.get_collection(collection_name)
        except:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
            )

    def add_document(self, doc: RetrievedDocument) -> str:
        """Add document to vector database with team context metadata"""
        # Generate embedding
        embedding = self.embeddings.embed_query(doc.content)

        # Generate unique ID
        doc_id = hashlib.md5(f"{doc.source}_{doc.timestamp}".encode()).hexdigest()

        # Prepare payload with team context
        payload = {
            "content": doc.content,
            "title": doc.title,
            "source": doc.source,
            "timestamp": doc.timestamp.isoformat(),
            "domain": doc.domain,
            "goal": doc.goal,
            # NEW: Team-specific metadata
            "member_expertise_score": doc.member_expertise_score,
            "team_perspective_score": doc.team_perspective_score,
            "evidence_type_match": doc.evidence_type_match,
        }

        # Store in Qdrant
        self.client.upsert(
            collection_name=self.collection_name,
            points=[PointStruct(id=doc_id, vector=embedding, payload=payload)],
        )

        return doc_id

    def search(
        self,
        query: str,
        limit: int = 10,
        filter_domains: List[str] = None,
        filter_goals: List[str] = None,
        exclude_sources: List[str] = None,
        filter_evidence_types: List[str] = None,
        member_expertise: str = None,
        min_team_perspective_score: float = None,
        min_member_expertise_score: float = None,
    ) -> List[RetrievedDocument]:
        """Search vector database with team-aware filtering"""
        query_embedding = self.embeddings.embed_query(query)

        # Build Qdrant filter with team context
        must_conditions = []
        must_not_conditions = []

        # Domain filtering
        if filter_domains:
            must_conditions.append(
                {
                    "should": [
                        {"key": "domain", "match": {"value": domain}}
                        for domain in filter_domains
                    ]
                }
            )

        # Goal filtering
        if filter_goals:
            must_conditions.append(
                {
                    "should": [
                        {"key": "goal", "match": {"value": goal}}
                        for goal in filter_goals
                    ]
                }
            )

        # NEW: Evidence type filtering
        if filter_evidence_types:
            # Search for evidence types in content
            evidence_conditions = []
            for evidence_type in filter_evidence_types:
                evidence_conditions.append(
                    {"key": "content", "match": {"text": evidence_type}}
                )
                evidence_conditions.append(
                    {"key": "title", "match": {"text": evidence_type}}
                )

            if evidence_conditions:
                must_conditions.append({"should": evidence_conditions})

        # NEW: Member expertise filtering
        if member_expertise:
            expertise_conditions = [
                {"key": "content", "match": {"text": member_expertise}},
                {"key": "title", "match": {"text": member_expertise}},
            ]
            must_conditions.append({"should": expertise_conditions})

        # NEW: Team perspective score filtering
        if min_team_perspective_score is not None:
            must_conditions.append(
                {
                    "key": "team_perspective_score",
                    "range": {"gte": min_team_perspective_score},
                }
            )

        # NEW: Member expertise score filtering
        if min_member_expertise_score is not None:
            must_conditions.append(
                {
                    "key": "member_expertise_score",
                    "range": {"gte": min_member_expertise_score},
                }
            )

        # Source exclusion
        if exclude_sources:
            for source in exclude_sources:
                must_not_conditions.append(
                    {"key": "source", "match": {"value": source}}
                )

        # Combine conditions
        filter_conditions = None
        if must_conditions or must_not_conditions:
            filter_conditions = {}
            if must_conditions:
                if len(must_conditions) == 1:
                    filter_conditions["must"] = must_conditions[0]
                else:
                    filter_conditions["must"] = must_conditions
            if must_not_conditions:
                filter_conditions["must_not"] = must_not_conditions

        try:
            results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_embedding,
                limit=limit if not exclude_sources else limit * 2,
                query_filter=filter_conditions,
            ).points
        except Exception as e:
            print(f"Search error with team-aware filter: {e}")
            # Fallback to basic search without filter
            results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_embedding,
                limit=limit * 2 if exclude_sources else limit,
            ).points

        documents = []
        for result in results:
            payload = result.payload

            # Manual filtering as backup
            if exclude_sources and payload.get("source") in exclude_sources:
                continue

            if filter_goals and payload.get("goal") not in filter_goals:
                continue

            # NEW: Manual team-specific filtering as backup
            if filter_evidence_types:
                content_text = (
                    f"{payload.get('content', '')} {payload.get('title', '')}".lower()
                )
                if not any(
                    evidence_type.lower() in content_text
                    for evidence_type in filter_evidence_types
                ):
                    continue

            if member_expertise:
                content_text = (
                    f"{payload.get('content', '')} {payload.get('title', '')}".lower()
                )
                if member_expertise.lower() not in content_text:
                    continue

            if min_team_perspective_score is not None:
                if (
                    payload.get("team_perspective_score", 0)
                    < min_team_perspective_score
                ):
                    continue

            if min_member_expertise_score is not None:
                if (
                    payload.get("member_expertise_score", 0)
                    < min_member_expertise_score
                ):
                    continue

            doc = RetrievedDocument(
                content=payload["content"],
                title=payload["title"],
                source=payload["source"],
                relevance_score=result.score,
                timestamp=datetime.fromisoformat(payload["timestamp"]),
                domain=payload.get("domain", ""),
                goal=payload.get("goal", ""),
                embedding_id=str(result.id),
                # NEW: Restore team-specific scores
                member_expertise_score=payload.get("member_expertise_score", 0.0),
                team_perspective_score=payload.get("team_perspective_score", 0.0),
                evidence_type_match=payload.get("evidence_type_match", False),
            )
            documents.append(doc)

            if len(documents) >= limit:
                break

        return documents

    def get_team_statistics(
        self, team_type: str = None, member_name: str = None
    ) -> dict:
        """Get statistics about documents relevant to specific team or member"""
        try:
            # Count total documents
            total_results = self.client.count(collection_name=self.collection_name)
            total_docs = total_results.count if hasattr(total_results, "count") else 0

            stats = {
                "total_documents": total_docs,
                "team_relevant_documents": 0,
                "member_relevant_documents": 0,
                "high_quality_matches": 0,
            }

            # If we have team or member context, get more specific stats
            if team_type or member_name:
                # This would require more complex querying - simplified for now
                sample_results = self.client.query_points(
                    collection_name=self.collection_name,
                    query=[0.0] * 1536,  # Dummy vector
                    limit=1000,
                ).points

                for result in sample_results:
                    payload = result.payload

                    if team_type and payload.get("team_perspective_score", 0) > 0.5:
                        stats["team_relevant_documents"] += 1

                    if member_name and payload.get("member_expertise_score", 0) > 0.5:
                        stats["member_relevant_documents"] += 1

                    if (
                        payload.get("team_perspective_score", 0) > 0.7
                        and payload.get("member_expertise_score", 0) > 0.7
                    ):
                        stats["high_quality_matches"] += 1

            return stats

        except Exception as e:
            print(f"Error getting team statistics: {e}")
            return {"error": str(e)}

    def optimize_for_team(
        self, team_type: str, member_expertise_areas: List[str]
    ) -> None:
        """Optimize database indexing for specific team and member combinations"""
        # This could involve creating specialized indexes or pre-computing team relevance scores
        # For now, this is a placeholder for future optimization
        print(
            f"Optimizing database for team: {team_type}, expertise: {member_expertise_areas}"
        )

        # Future implementations could:
        # 1. Create team-specific vector indexes
        # 2. Pre-compute relevance scores for common team/member combinations
        # 3. Cache frequently accessed team-specific queries
        pass


async def preprocess_documents_with_team_context(
    documents: List[str],
    vector_db: VectorDBManager,
    team_contexts: List[dict] = None,
    batch_size: int = 10,
):
    """Pre-process documents into vector database with team context awareness"""
    import asyncio
    from pathlib import Path

    async def process_document(doc_path: str, team_context: dict = None):
        """Process a single document with optional team context"""
        # Read document
        with open(doc_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Create document object
        doc = RetrievedDocument(
            content=content,
            title=Path(doc_path).name,
            source=doc_path,
            relevance_score=1.0,
            domain=(
                team_context.get("domain", "local_documents")
                if team_context
                else "local_documents"
            ),
            goal=team_context.get("goal", "") if team_context else "",
            # Pre-set team scores if context provided
            member_expertise_score=(
                team_context.get("member_expertise_score", 0.0) if team_context else 0.0
            ),
            team_perspective_score=(
                team_context.get("team_perspective_score", 0.0) if team_context else 0.0
            ),
            evidence_type_match=(
                team_context.get("evidence_type_match", False)
                if team_context
                else False
            ),
        )

        # Store in vector DB
        return vector_db.add_document(doc)

    # Process in batches with team context
    for i in range(0, len(documents), batch_size):
        batch = documents[i : i + batch_size]
        tasks = []

        for j, doc in enumerate(batch):
            team_context = None
            if team_contexts and j < len(team_contexts):
                team_context = team_contexts[j]
            tasks.append(process_document(doc, team_context))

        await asyncio.gather(*tasks)
