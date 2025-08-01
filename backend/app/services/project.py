"""Project service layer."""
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectWithStats
from app.models.project import ProjectInDB


class ProjectService:
    """Service for project operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def list_projects(
        self,
        filter_dict: Dict[str, Any],
        skip: int,
        limit: int,
        sort_by: str,
        sort_order: str
    ) -> Tuple[List[ProjectWithStats], int]:
        """List projects with pagination."""
        # Count total
        total = await self.db.projects.count_documents(filter_dict)
        
        # Build sort
        sort_direction = -1 if sort_order == "desc" else 1
        
        # Special handling for nested fields
        if sort_by == "message_count":
            sort_field = "stats.message_count"
        else:
            sort_field = sort_by
        
        # Get projects
        cursor = self.db.projects.find(filter_dict).sort(
            sort_field, sort_direction
        ).skip(skip).limit(limit)
        
        projects = []
        async for doc in cursor:
            # Enrich with real-time stats
            stats = await self._get_project_stats(doc["_id"])
            doc["stats"] = stats
            projects.append(ProjectWithStats(**doc))
        
        return projects, total
    
    async def get_project(self, project_id: ObjectId) -> Optional[ProjectWithStats]:
        """Get a single project."""
        doc = await self.db.projects.find_one({"_id": project_id})
        if not doc:
            return None
        
        # Enrich with stats
        stats = await self._get_project_stats(project_id)
        doc["stats"] = stats
        
        return ProjectWithStats(**doc)
    
    async def get_project_by_path(self, path: str) -> Optional[ProjectInDB]:
        """Get project by path."""
        doc = await self.db.projects.find_one({"path": path})
        return ProjectInDB(**doc) if doc else None
    
    async def create_project(self, project: ProjectCreate) -> ProjectInDB:
        """Create a new project."""
        doc = {
            "_id": ObjectId(),
            "name": project.name,
            "path": project.path,
            "description": project.description,
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }
        
        await self.db.projects.insert_one(doc)
        return ProjectInDB(**doc)
    
    async def update_project(
        self,
        project_id: ObjectId,
        update: ProjectUpdate
    ) -> Optional[ProjectInDB]:
        """Update a project."""
        update_dict = update.dict(exclude_unset=True)
        if update_dict:
            update_dict["updatedAt"] = datetime.utcnow()
            
            result = await self.db.projects.find_one_and_update(
                {"_id": project_id},
                {"$set": update_dict},
                return_document=True
            )
            
            return ProjectInDB(**result) if result else None
        
        return await self.get_project(project_id)
    
    async def delete_project(
        self,
        project_id: ObjectId,
        cascade: bool = False
    ) -> bool:
        """Delete a project."""
        if cascade:
            # Delete all associated data
            # Get all session IDs
            session_ids = await self.db.sessions.distinct(
                "sessionId",
                {"projectId": project_id}
            )
            
            # Delete messages
            await self.db.messages.delete_many(
                {"sessionId": {"$in": session_ids}}
            )
            
            # Delete sessions
            await self.db.sessions.delete_many({"projectId": project_id})
        
        # Delete project
        result = await self.db.projects.delete_one({"_id": project_id})
        return result.deleted_count > 0
    
    async def get_project_statistics(self, project_id: ObjectId) -> Optional[dict]:
        """Get detailed project statistics."""
        # Check project exists
        project = await self.db.projects.find_one({"_id": project_id})
        if not project:
            return None
        
        # Get session IDs
        session_ids = await self.db.sessions.distinct(
            "sessionId",
            {"projectId": project_id}
        )
        
        # Aggregate statistics
        pipeline = [
            {"$match": {"sessionId": {"$in": session_ids}}},
            {"$group": {
                "_id": None,
                "total_messages": {"$sum": 1},
                "user_messages": {
                    "$sum": {"$cond": [{"$eq": ["$type", "user"]}, 1, 0]}
                },
                "assistant_messages": {
                    "$sum": {"$cond": [{"$eq": ["$type", "assistant"]}, 1, 0]}
                },
                "total_cost": {"$sum": {"$ifNull": ["$costUsd", 0]}},
                "models_used": {"$addToSet": "$model"},
                "first_message": {"$min": "$timestamp"},
                "last_message": {"$max": "$timestamp"}
            }}
        ]
        
        result = await self.db.messages.aggregate(pipeline).to_list(1)
        
        if result:
            stats = result[0]
            stats["session_count"] = len(session_ids)
            stats["project_id"] = str(project_id)
            return stats
        
        return {
            "project_id": str(project_id),
            "session_count": 0,
            "total_messages": 0,
            "user_messages": 0,
            "assistant_messages": 0,
            "total_cost": 0,
            "models_used": []
        }
    
    async def _get_project_stats(self, project_id: ObjectId) -> dict:
        """Get basic project statistics."""
        # Count sessions
        session_count = await self.db.sessions.count_documents(
            {"projectId": project_id}
        )
        
        # Count messages (through sessions)
        session_ids = await self.db.sessions.distinct(
            "sessionId",
            {"projectId": project_id}
        )
        
        message_count = await self.db.messages.count_documents(
            {"sessionId": {"$in": session_ids}}
        )
        
        return {
            "session_count": session_count,
            "message_count": message_count
        }