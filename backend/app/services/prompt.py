"""Service layer for prompt operations."""

import re
from datetime import UTC, datetime
from typing import Any, Optional, cast

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.prompt import FolderInDB, PromptInDB, PromptVersionInDB, PyObjectId
from app.schemas.prompt import (
    FolderCreate,
    FolderUpdate,
    Prompt,
    PromptCreate,
    PromptDetail,
    PromptUpdate,
)


def extract_variables(content: str) -> list[str]:
    """Extract {{variable}} names from prompt content."""
    pattern = r"\{\{(\w+)\}\}"
    matches = re.findall(pattern, content)
    return list(set(matches))  # Unique variables only


def substitute_variables(template: str, variables: dict[str, str]) -> str:
    """Replace {{variable}} with values in template."""

    def replacer(match: re.Match[str]) -> str:
        var_name = match.group(1)
        return variables.get(var_name, match.group(0))

    return re.sub(r"\{\{(\w+)\}\}", replacer, template)


class PromptService:
    """Service for prompt operations."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    # Prompt CRUD operations
    async def list_prompts(
        self,
        filter_dict: dict[str, Any],
        skip: int,
        limit: int,
        sort_by: str,
        sort_order: str,
    ) -> tuple[list[Prompt], int]:
        """List prompts with pagination."""
        # Count total
        total = await self.db.prompts.count_documents(filter_dict)

        # Build sort
        sort_direction = -1 if sort_order == "desc" else 1
        sort_field = {
            "name": "name",
            "created_at": "createdAt",
            "updated_at": "updatedAt",
            "use_count": "useCount",
        }.get(sort_by, "updatedAt")

        # Get prompts
        cursor = (
            self.db.prompts.find(filter_dict)
            .sort(sort_field, sort_direction)
            .skip(skip)
            .limit(limit)
        )

        prompts = []
        async for doc in cursor:
            # Convert ObjectId to string
            doc["_id"] = str(doc["_id"])
            if doc.get("folderId"):
                doc["folderId"] = str(doc["folderId"])
            prompts.append(Prompt(**doc))

        return prompts, total

    async def get_prompt(self, prompt_id: ObjectId) -> Optional[PromptDetail]:
        """Get a single prompt with full details."""
        doc = await self.db.prompts.find_one({"_id": prompt_id})
        if not doc:
            return None

        # Convert ObjectId to string
        doc["_id"] = str(doc["_id"])
        if doc.get("folderId"):
            doc["folderId"] = str(doc["folderId"])

        return PromptDetail(**doc)

    async def create_prompt(self, prompt: PromptCreate) -> PromptInDB:
        """Create a new prompt."""
        # Extract variables from content
        variables = extract_variables(prompt.content)

        doc = {
            "_id": ObjectId(),
            "name": prompt.name,
            "content": prompt.content,
            "description": prompt.description,
            "variables": variables,
            "tags": prompt.tags,
            "folderId": ObjectId(prompt.folder_id) if prompt.folder_id else None,
            "version": "1.0.0",
            "versions": [],
            "visibility": prompt.visibility,
            "sharedWith": [],
            "publicUrl": None,
            "useCount": 0,
            "lastUsedAt": None,
            "avgResponseTime": None,
            "successRate": None,
            "createdAt": datetime.now(UTC),
            "updatedAt": datetime.now(UTC),
            "createdBy": "system",  # TODO: Get from auth context
            "isStarred": False,
        }

        await self.db.prompts.insert_one(doc)
        return PromptInDB(
            _id=PyObjectId(cast(ObjectId, doc["_id"])),
            name=cast(str, doc["name"]),
            content=cast(str, doc["content"]),
            description=cast(Optional[str], doc.get("description")),
            variables=cast(list[str], doc["variables"]),
            tags=cast(list[str], doc["tags"]),
            folderId=PyObjectId(cast(ObjectId, doc["folderId"]))
            if doc["folderId"]
            else None,
            version=cast(str, doc["version"]),
            versions=cast(list[PromptVersionInDB], doc["versions"]),
            visibility=cast(str, doc["visibility"]),
            sharedWith=cast(list[str], doc["sharedWith"]),
            publicUrl=cast(Optional[str], doc.get("publicUrl")),
            useCount=cast(int, doc["useCount"]),
            lastUsedAt=cast(Optional[datetime], doc.get("lastUsedAt")),
            avgResponseTime=cast(Optional[float], doc.get("avgResponseTime")),
            successRate=cast(Optional[float], doc.get("successRate")),
            createdAt=cast(datetime, doc["createdAt"]),
            updatedAt=cast(datetime, doc["updatedAt"]),
            createdBy=cast(str, doc["createdBy"]),
            isStarred=cast(bool, doc["isStarred"]),
        )

    async def update_prompt(
        self, prompt_id: ObjectId, update: PromptUpdate
    ) -> Optional[PromptInDB]:
        """Update a prompt."""
        update_dict = update.model_dump(exclude_unset=True)

        if update_dict:
            # If content is being updated, extract new variables
            if "content" in update_dict:
                update_dict["variables"] = extract_variables(update_dict["content"])

            # Convert folder_id to ObjectId if provided
            if "folder_id" in update_dict:
                update_dict["folderId"] = (
                    ObjectId(update_dict.pop("folder_id"))
                    if update_dict["folder_id"]
                    else None
                )

            # Handle is_starred field alias
            if "is_starred" in update_dict:
                update_dict["isStarred"] = update_dict.pop("is_starred")

            update_dict["updatedAt"] = datetime.now(UTC)

            # Save current version if content changed
            if "content" in update_dict:
                current = await self.db.prompts.find_one({"_id": prompt_id})
                if current:
                    # Increment version
                    version_parts = current["version"].split(".")
                    version_parts[2] = str(int(version_parts[2]) + 1)
                    new_version = ".".join(version_parts)

                    version_entry = {
                        "version": current["version"],
                        "content": current["content"],
                        "variables": current.get("variables", []),
                        "change_log": "Content updated",
                        "createdAt": datetime.now(UTC),
                        "createdBy": "system",  # TODO: Get from auth context
                    }

                    # Keep only last 10 versions
                    result = await self.db.prompts.find_one_and_update(
                        {"_id": prompt_id},
                        {
                            "$set": {**update_dict, "version": new_version},
                            "$push": {
                                "versions": {
                                    "$each": [version_entry],
                                    "$slice": -10,  # Keep last 10 versions
                                }
                            },
                        },
                        return_document=True,
                    )
                else:
                    result = None
            else:
                result = await self.db.prompts.find_one_and_update(
                    {"_id": prompt_id}, {"$set": update_dict}, return_document=True
                )

            if result:
                result["_id"] = str(result["_id"])
                if result.get("folderId"):
                    result["folderId"] = str(result["folderId"])
                return PromptInDB(**result)
            return None

        # If no update provided, return existing prompt
        existing = await self.db.prompts.find_one({"_id": prompt_id})
        if existing:
            existing["_id"] = str(existing["_id"])
            if existing.get("folderId"):
                existing["folderId"] = str(existing["folderId"])
            return PromptInDB(**existing)
        return None

    async def delete_prompt(self, prompt_id: ObjectId) -> bool:
        """Delete a prompt."""
        result = await self.db.prompts.delete_one({"_id": prompt_id})
        return result.deleted_count > 0

    async def increment_use_count(self, prompt_id: ObjectId) -> None:
        """Increment the use count for a prompt."""
        await self.db.prompts.update_one(
            {"_id": prompt_id},
            {
                "$inc": {"useCount": 1},
                "$set": {"lastUsedAt": datetime.now(UTC)},
            },
        )

    async def get_unique_tags(self) -> list[dict[str, Any]]:
        """Get all unique tags with their usage counts."""
        pipeline: list[dict[str, Any]] = [
            {"$unwind": "$tags"},
            {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
            {"$sort": {"count": -1, "_id": 1}},
            {"$project": {"name": "$_id", "count": 1, "_id": 0}},
        ]

        cursor = self.db.prompts.aggregate(pipeline)
        tags = await cursor.to_list(None)
        return tags

    # Folder CRUD operations
    async def list_folders(self) -> list[FolderInDB]:
        """List all folders."""
        cursor = self.db.prompt_folders.find().sort("name", 1)
        folders = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            if doc.get("parentId"):
                doc["parentId"] = str(doc["parentId"])
            folders.append(FolderInDB(**doc))
        return folders

    async def create_folder(self, folder: FolderCreate) -> FolderInDB:
        """Create a new folder."""
        doc = {
            "_id": ObjectId(),
            "name": folder.name,
            "parentId": ObjectId(folder.parent_id) if folder.parent_id else None,
            "createdAt": datetime.now(UTC),
            "updatedAt": datetime.now(UTC),
            "createdBy": "system",  # TODO: Get from auth context
        }

        await self.db.prompt_folders.insert_one(doc)
        return FolderInDB(
            _id=PyObjectId(cast(ObjectId, doc["_id"])),
            name=cast(str, doc["name"]),
            parentId=PyObjectId(cast(ObjectId, doc["parentId"]))
            if doc["parentId"]
            else None,
            createdAt=cast(datetime, doc["createdAt"]),
            updatedAt=cast(datetime, doc["updatedAt"]),
            createdBy=cast(str, doc["createdBy"]),
        )

    async def update_folder(
        self, folder_id: ObjectId, update: FolderUpdate
    ) -> Optional[FolderInDB]:
        """Update a folder."""
        update_dict = update.model_dump(exclude_unset=True)

        if update_dict:
            if "parent_id" in update_dict:
                update_dict["parentId"] = (
                    ObjectId(update_dict.pop("parent_id"))
                    if update_dict["parent_id"]
                    else None
                )

            update_dict["updatedAt"] = datetime.now(UTC)

            result = await self.db.prompt_folders.find_one_and_update(
                {"_id": folder_id}, {"$set": update_dict}, return_document=True
            )

            if result:
                result["_id"] = str(result["_id"])
                if result.get("parentId"):
                    result["parentId"] = str(result["parentId"])
                return FolderInDB(**result)
            return None

        # If no update provided, return existing folder
        existing = await self.db.prompt_folders.find_one({"_id": folder_id})
        if existing:
            existing["_id"] = str(existing["_id"])
            if existing.get("parentId"):
                existing["parentId"] = str(existing["parentId"])
            return FolderInDB(**existing)
        return None

    async def delete_folder(self, folder_id: ObjectId) -> bool:
        """Delete a folder and move prompts to root."""
        # Move all prompts in this folder to root
        await self.db.prompts.update_many(
            {"folderId": folder_id}, {"$set": {"folderId": None}}
        )

        # Move all child folders to root
        await self.db.prompt_folders.update_many(
            {"parentId": folder_id}, {"$set": {"parentId": None}}
        )

        # Delete the folder
        result = await self.db.prompt_folders.delete_one({"_id": folder_id})
        return result.deleted_count > 0

    # Search and filtering
    async def search_prompts(
        self, query: str, skip: int = 0, limit: int = 20
    ) -> tuple[list[Prompt], int]:
        """Search prompts by name, description, content, or tags."""
        filter_dict = {
            "$or": [
                {"name": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}},
                {"content": {"$regex": query, "$options": "i"}},
                {"tags": {"$in": [query]}},
            ]
        }

        return await self.list_prompts(filter_dict, skip, limit, "updatedAt", "desc")

    async def get_prompts_by_folder(
        self, folder_id: Optional[ObjectId], skip: int = 0, limit: int = 20
    ) -> tuple[list[Prompt], int]:
        """Get prompts in a specific folder."""
        filter_dict = {"folderId": folder_id}
        return await self.list_prompts(filter_dict, skip, limit, "name", "asc")

    async def get_starred_prompts(
        self, skip: int = 0, limit: int = 20
    ) -> tuple[list[Prompt], int]:
        """Get starred prompts."""
        filter_dict = {"isStarred": True}
        return await self.list_prompts(filter_dict, skip, limit, "updatedAt", "desc")
