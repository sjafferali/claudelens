"""Ingestion service for processing messages."""
import asyncio
from typing import List, Dict, Any, Set, Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import hashlib
import json
import logging

from app.schemas.ingest import MessageIngest, IngestStats
from app.models.message import MessageInDB
from app.models.session import SessionInDB
from app.models.project import ProjectInDB

logger = logging.getLogger(__name__)


class IngestService:
    """Service for ingesting Claude messages."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self._project_cache: Dict[str, ObjectId] = {}
        self._session_cache: Dict[str, ObjectId] = {}
    
    async def ingest_messages(self, messages: List[MessageIngest]) -> IngestStats:
        """Ingest a batch of messages."""
        start_time = datetime.utcnow()
        stats = IngestStats(messages_received=len(messages))
        
        # Group messages by session
        sessions_map: Dict[str, List[MessageIngest]] = {}
        for message in messages:
            session_id = message.sessionId
            if session_id not in sessions_map:
                sessions_map[session_id] = []
            sessions_map[session_id].append(message)
        
        # Process each session
        tasks = []
        for session_id, session_messages in sessions_map.items():
            task = self._process_session_messages(session_id, session_messages, stats)
            tasks.append(task)
        
        # Run all sessions in parallel
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Calculate duration
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        stats.duration_ms = int(duration)
        
        # Log ingestion
        await self._log_ingestion(stats)
        
        return stats
    
    async def _process_session_messages(
        self,
        session_id: str,
        messages: List[MessageIngest],
        stats: IngestStats
    ):
        """Process messages for a single session."""
        try:
            # Ensure session exists
            session_obj_id = await self._ensure_session(session_id, messages[0])
            if session_obj_id:
                stats.sessions_created += 1
            else:
                stats.sessions_updated += 1
            
            # Get existing message hashes for deduplication
            existing_hashes = await self._get_existing_hashes(session_id)
            
            # Process each message
            new_messages = []
            for message in messages:
                # Generate hash for deduplication
                message_hash = self._hash_message(message)
                
                if message_hash in existing_hashes:
                    stats.messages_skipped += 1
                    continue
                
                # Convert to database model
                try:
                    message_doc = self._message_to_doc(message, session_id)
                    new_messages.append(message_doc)
                    existing_hashes.add(message_hash)
                except Exception as e:
                    logger.error(f"Error processing message {message.uuid}: {e}")
                    stats.messages_failed += 1
            
            # Bulk insert new messages
            if new_messages:
                result = await self.db.messages.insert_many(new_messages)
                stats.messages_processed += len(result.inserted_ids)
                
                # Update session statistics
                await self._update_session_stats(session_id)
            
        except Exception as e:
            logger.error(f"Error processing session {session_id}: {e}")
            stats.messages_failed += len(messages)
    
    async def _ensure_session(
        self,
        session_id: str,
        first_message: MessageIngest
    ) -> Optional[ObjectId]:
        """Ensure session exists, create if needed."""
        # Check cache first
        if session_id in self._session_cache:
            return None
        
        # Check database
        existing = await self.db.sessions.find_one({"sessionId": session_id})
        if existing:
            self._session_cache[session_id] = existing["_id"]
            return None
        
        # Extract project info from path
        project_path = None
        project_name = "Unknown Project"
        
        if first_message.cwd:
            # Extract project from Claude path format
            # e.g., /Users/user/projects/my-project -> my-project
            parts = first_message.cwd.split('/')
            if 'projects' in parts:
                idx = parts.index('projects')
                if idx + 1 < len(parts):
                    project_name = parts[idx + 1]
                    project_path = '/'.join(parts[:idx + 2])
        
        # Ensure project exists
        project_id = await self._ensure_project(project_path or first_message.cwd, project_name)
        
        # Create session
        session_doc = {
            "_id": ObjectId(),
            "sessionId": session_id,
            "projectId": project_id,
            "startedAt": first_message.timestamp,
            "endedAt": first_message.timestamp,
            "messageCount": 0,
            "totalCost": 0.0,
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }
        
        await self.db.sessions.insert_one(session_doc)
        self._session_cache[session_id] = session_doc["_id"]
        
        return session_doc["_id"]
    
    async def _ensure_project(self, project_path: str, project_name: str) -> ObjectId:
        """Ensure project exists, create if needed."""
        # Check cache first
        if project_path in self._project_cache:
            return self._project_cache[project_path]
        
        # Check database
        existing = await self.db.projects.find_one({"path": project_path})
        if existing:
            self._project_cache[project_path] = existing["_id"]
            return existing["_id"]
        
        # Create project
        project_doc = {
            "_id": ObjectId(),
            "name": project_name,
            "path": project_path,
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow(),
            "stats": {
                "message_count": 0,
                "session_count": 0
            }
        }
        
        await self.db.projects.insert_one(project_doc)
        self._project_cache[project_path] = project_doc["_id"]
        
        return project_doc["_id"]
    
    async def _get_existing_hashes(self, session_id: str) -> Set[str]:
        """Get existing message hashes for a session."""
        cursor = self.db.messages.find(
            {"sessionId": session_id},
            {"contentHash": 1}
        )
        
        hashes = set()
        async for doc in cursor:
            if "contentHash" in doc:
                hashes.add(doc["contentHash"])
        
        return hashes
    
    def _hash_message(self, message: MessageIngest) -> str:
        """Generate hash for message deduplication."""
        # Create deterministic string representation
        hash_data = {
            "uuid": message.uuid,
            "type": message.type,
            "timestamp": message.timestamp.isoformat(),
            "content": message.message
        }
        
        content = json.dumps(hash_data, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _message_to_doc(self, message: MessageIngest, session_id: str) -> dict:
        """Convert message to database document."""
        doc = {
            "_id": ObjectId(),
            "uuid": message.uuid,
            "sessionId": session_id,
            "type": message.type,
            "timestamp": message.timestamp,
            "parentUuid": message.parentUuid,
            "contentHash": self._hash_message(message),
            "createdAt": datetime.utcnow()
        }
        
        # Add message content
        if message.message:
            doc["message"] = message.message
        
        # Add optional fields
        optional_fields = [
            "userType", "cwd", "model", "costUsd", "durationMs",
            "requestId", "version", "gitBranch", "isSidechain",
            "toolUseResult", "summary", "leafUuid"
        ]
        for field in optional_fields:
            value = getattr(message, field, None)
            if value is not None:
                doc[field] = value
        
        # Add any extra fields
        if message.extra_fields:
            doc["metadata"] = message.extra_fields
        
        return doc
    
    async def _update_session_stats(self, session_id: str):
        """Update session statistics."""
        # Aggregate statistics
        pipeline = [
            {"$match": {"sessionId": session_id}},
            {"$group": {
                "_id": None,
                "messageCount": {"$sum": 1},
                "totalCost": {"$sum": {"$ifNull": ["$costUsd", 0]}},
                "startTime": {"$min": "$timestamp"},
                "endTime": {"$max": "$timestamp"}
            }}
        ]
        
        result = await self.db.messages.aggregate(pipeline).to_list(1)
        
        if result:
            stats = result[0]
            await self.db.sessions.update_one(
                {"sessionId": session_id},
                {
                    "$set": {
                        "messageCount": stats["messageCount"],
                        "totalCost": stats["totalCost"],
                        "startedAt": stats["startTime"],
                        "endedAt": stats["endTime"],
                        "updatedAt": datetime.utcnow()
                    }
                }
            )
    
    async def _log_ingestion(self, stats: IngestStats):
        """Log ingestion statistics."""
        log_entry = {
            "timestamp": datetime.utcnow(),
            "messages_processed": stats.messages_processed,
            "messages_skipped": stats.messages_skipped,
            "messages_failed": stats.messages_failed,
            "duration_ms": stats.duration_ms
        }
        
        await self.db.ingestion_logs.insert_one(log_entry)