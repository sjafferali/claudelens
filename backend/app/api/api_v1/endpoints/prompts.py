"""API endpoints for prompt management."""

import csv
import io
import json
from typing import Any, Optional, cast

from bson import ObjectId
from fastapi import HTTPException, Query, Response

from app.api.dependencies import CommonDeps
from app.core.custom_router import APIRouter
from app.core.exceptions import NotFoundError
from app.schemas.common import PaginatedResponse
from app.schemas.prompt import (
    Folder,
    FolderCreate,
    FolderUpdate,
    Prompt,
    PromptCreate,
    PromptDetail,
    PromptExportRequest,
    PromptImportRequest,
    PromptShareRequest,
    PromptTestRequest,
    PromptTestResponse,
    PromptUpdate,
)
from app.services.prompt import PromptService, substitute_variables

router = APIRouter()


# Prompt endpoints
@router.get("/", response_model=PaginatedResponse[Prompt])
async def list_prompts(
    db: CommonDeps,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search in prompt names, content"),
    folder_id: Optional[str] = Query(None, description="Filter by folder ID"),
    starred_only: bool = Query(False, description="Show only starred prompts"),
    sort_by: str = Query(
        "updated_at", pattern="^(name|created_at|updated_at|use_count)$"
    ),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
) -> PaginatedResponse[Prompt]:
    """List all prompts with pagination and filtering."""
    service = PromptService(db)

    # Handle different filter scenarios
    if search:
        prompts, total = await service.search_prompts(search, skip, limit)
    elif starred_only:
        prompts, total = await service.get_starred_prompts(skip, limit)
    elif folder_id is not None:
        folder_obj_id = ObjectId(folder_id) if folder_id else None
        prompts, total = await service.get_prompts_by_folder(folder_obj_id, skip, limit)
    else:
        # Default: list all prompts
        filter_dict: dict[str, Any] = {}
        prompts, total = await service.list_prompts(
            filter_dict=filter_dict,
            skip=skip,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    return PaginatedResponse(
        items=prompts,
        total=total,
        skip=skip,
        limit=limit,
        has_more=skip + limit < total,
    )


@router.get("/{prompt_id}", response_model=PromptDetail)
async def get_prompt(prompt_id: str, db: CommonDeps) -> PromptDetail:
    """Get a specific prompt by ID."""
    if not ObjectId.is_valid(prompt_id):
        raise HTTPException(status_code=400, detail="Invalid prompt ID")

    service = PromptService(db)
    prompt = await service.get_prompt(ObjectId(prompt_id))

    if not prompt:
        raise NotFoundError("Prompt", prompt_id)

    return prompt


@router.post("/", response_model=Prompt, status_code=201)
async def create_prompt(prompt: PromptCreate, db: CommonDeps) -> Prompt:
    """Create a new prompt."""
    service = PromptService(db)

    # Validate folder_id if provided
    if prompt.folder_id and not ObjectId.is_valid(prompt.folder_id):
        raise HTTPException(status_code=400, detail="Invalid folder ID")

    created_prompt = await service.create_prompt(prompt)

    # Convert to response schema
    prompt_dict = created_prompt.model_dump(by_alias=True)
    prompt_dict["_id"] = str(prompt_dict["_id"])
    if prompt_dict.get("folderId"):
        prompt_dict["folderId"] = str(prompt_dict["folderId"])

    return Prompt(**prompt_dict)


@router.patch("/{prompt_id}", response_model=Prompt)
async def update_prompt(prompt_id: str, update: PromptUpdate, db: CommonDeps) -> Prompt:
    """Update a prompt."""
    if not ObjectId.is_valid(prompt_id):
        raise HTTPException(status_code=400, detail="Invalid prompt ID")

    # Validate folder_id if provided
    if update.folder_id and not ObjectId.is_valid(update.folder_id):
        raise HTTPException(status_code=400, detail="Invalid folder ID")

    service = PromptService(db)
    updated_prompt = await service.update_prompt(ObjectId(prompt_id), update)

    if not updated_prompt:
        raise NotFoundError("Prompt", prompt_id)

    # Convert to response schema
    prompt_dict = updated_prompt.model_dump(by_alias=True)
    prompt_dict["_id"] = str(prompt_dict["_id"])
    if prompt_dict.get("folderId"):
        prompt_dict["folderId"] = str(prompt_dict["folderId"])

    return Prompt(**prompt_dict)


@router.delete("/{prompt_id}", status_code=200)
async def delete_prompt(prompt_id: str, db: CommonDeps) -> dict:
    """Delete a prompt."""
    if not ObjectId.is_valid(prompt_id):
        raise HTTPException(status_code=400, detail="Invalid prompt ID")

    service = PromptService(db)
    deleted = await service.delete_prompt(ObjectId(prompt_id))

    if not deleted:
        raise NotFoundError("Prompt", prompt_id)

    return {"message": "Prompt deleted successfully"}


# Folder endpoints
@router.get("/folders/", response_model=list[Folder])
async def list_folders(db: CommonDeps) -> list[Folder]:
    """List all folders."""
    service = PromptService(db)
    folders = await service.list_folders()

    # Convert to response schema and add prompt counts
    folder_list = []
    for folder in folders:
        folder_dict = folder.model_dump(by_alias=True)
        folder_dict["_id"] = str(folder_dict["_id"])
        if folder_dict.get("parentId"):
            folder_dict["parentId"] = str(folder_dict["parentId"])

        # Get prompt count for this folder
        prompts, count = await service.get_prompts_by_folder(folder.id, 0, 1)
        folder_dict["prompt_count"] = count

        folder_list.append(Folder(**folder_dict))

    return folder_list


@router.post("/folders/", response_model=Folder, status_code=201)
async def create_folder(folder: FolderCreate, db: CommonDeps) -> Folder:
    """Create a new folder."""
    service = PromptService(db)

    # Validate parent_id if provided
    if folder.parent_id and not ObjectId.is_valid(folder.parent_id):
        raise HTTPException(status_code=400, detail="Invalid parent folder ID")

    created_folder = await service.create_folder(folder)

    # Convert to response schema
    folder_dict = created_folder.model_dump(by_alias=True)
    folder_dict["_id"] = str(folder_dict["_id"])
    if folder_dict.get("parentId"):
        folder_dict["parentId"] = str(folder_dict["parentId"])
    folder_dict["prompt_count"] = 0

    return Folder(**folder_dict)


@router.patch("/folders/{folder_id}", response_model=Folder)
async def update_folder(folder_id: str, update: FolderUpdate, db: CommonDeps) -> Folder:
    """Update a folder."""
    if not ObjectId.is_valid(folder_id):
        raise HTTPException(status_code=400, detail="Invalid folder ID")

    # Validate parent_id if provided
    if update.parent_id and not ObjectId.is_valid(update.parent_id):
        raise HTTPException(status_code=400, detail="Invalid parent folder ID")

    service = PromptService(db)
    updated_folder = await service.update_folder(ObjectId(folder_id), update)

    if not updated_folder:
        raise NotFoundError("Folder", folder_id)

    # Convert to response schema
    folder_dict = updated_folder.model_dump(by_alias=True)
    folder_dict["_id"] = str(folder_dict["_id"])
    if folder_dict.get("parentId"):
        folder_dict["parentId"] = str(folder_dict["parentId"])

    # Get prompt count for this folder
    prompts, count = await service.get_prompts_by_folder(updated_folder.id, 0, 1)
    folder_dict["prompt_count"] = count

    return Folder(**folder_dict)


@router.delete("/folders/{folder_id}", status_code=200)
async def delete_folder(folder_id: str, db: CommonDeps) -> dict:
    """Delete a folder (prompts are moved to root)."""
    if not ObjectId.is_valid(folder_id):
        raise HTTPException(status_code=400, detail="Invalid folder ID")

    service = PromptService(db)
    deleted = await service.delete_folder(ObjectId(folder_id))

    if not deleted:
        raise NotFoundError("Folder", folder_id)

    return {"message": "Folder deleted successfully"}


# Special operations
@router.post("/{prompt_id}/test", response_model=PromptTestResponse)
async def test_prompt(
    prompt_id: str, request: PromptTestRequest, db: CommonDeps
) -> PromptTestResponse:
    """Test a prompt with variable substitution."""
    if not ObjectId.is_valid(prompt_id):
        raise HTTPException(status_code=400, detail="Invalid prompt ID")

    service = PromptService(db)
    prompt = await service.get_prompt(ObjectId(prompt_id))

    if not prompt:
        raise NotFoundError("Prompt", prompt_id)

    # Substitute variables
    import time

    start_time = time.time()
    result = substitute_variables(prompt.content, request.variables)
    execution_time_ms = (time.time() - start_time) * 1000

    # Track usage
    await service.increment_use_count(ObjectId(prompt_id))

    return PromptTestResponse(
        result=result,
        variables_used=request.variables,
        execution_time_ms=execution_time_ms,
    )


@router.post("/{prompt_id}/share", response_model=dict)
async def share_prompt(
    prompt_id: str, request: PromptShareRequest, db: CommonDeps
) -> dict:
    """Share a prompt with other users."""
    if not ObjectId.is_valid(prompt_id):
        raise HTTPException(status_code=400, detail="Invalid prompt ID")

    service = PromptService(db)

    # Update prompt sharing settings
    update = PromptUpdate(visibility=request.visibility)
    updated_prompt = await service.update_prompt(ObjectId(prompt_id), update)

    if not updated_prompt:
        raise NotFoundError("Prompt", prompt_id)

    # Update shared_with list
    await db.prompts.update_one(
        {"_id": ObjectId(prompt_id)},
        {"$addToSet": {"sharedWith": {"$each": request.user_ids}}},
    )

    return {"message": "Prompt shared successfully"}


@router.post("/export", response_model=dict)
async def export_prompts(request: PromptExportRequest, db: CommonDeps) -> Response:
    """Export prompts in various formats."""
    service = PromptService(db)

    # Get prompts to export
    prompts: list[Prompt | PromptDetail]
    if request.prompt_ids:
        prompts = []
        for prompt_id in request.prompt_ids:
            if ObjectId.is_valid(prompt_id):
                prompt = await service.get_prompt(ObjectId(prompt_id))
                if prompt:
                    prompts.append(prompt)
    else:
        # Export all prompts
        prompts_result, _ = await service.list_prompts({}, 0, 1000, "name", "asc")
        prompts = prompts_result

    # Format based on request
    if request.format == "json":
        content = json.dumps(
            [p.model_dump(by_alias=True, mode="json") for p in prompts], indent=2
        )
        media_type = "application/json"
        filename = "prompts.json"
    elif request.format == "csv":
        output = io.StringIO()
        if prompts:
            fieldnames = ["name", "description", "content", "tags", "variables"]
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            for p in prompts:
                writer.writerow(
                    {
                        "name": p.name,
                        "description": p.description or "",
                        "content": p.content,
                        "tags": ",".join(p.tags),
                        "variables": ",".join(p.variables),
                    }
                )
        content = output.getvalue()
        media_type = "text/csv"
        filename = "prompts.csv"
    elif request.format == "markdown":
        lines = ["# Prompts Export\n"]
        for p in prompts:
            lines.append(f"\n## {p.name}\n")
            if p.description:
                lines.append(f"*{p.description}*\n")
            lines.append(f"\n```\n{p.content}\n```\n")
            if p.variables:
                lines.append(f"\n**Variables**: {', '.join(p.variables)}\n")
            if p.tags:
                lines.append(f"**Tags**: {', '.join(p.tags)}\n")
        content = "\n".join(lines)
        media_type = "text/markdown"
        filename = "prompts.md"
    else:
        raise HTTPException(status_code=400, detail="Invalid export format")

    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/import", response_model=dict)
async def import_prompts(request: PromptImportRequest, db: CommonDeps) -> dict:
    """Import prompts from various formats."""
    service = PromptService(db)

    prompts_to_create = []

    if request.format == "json":
        try:
            data = json.loads(request.content)
            if not isinstance(data, list):
                data = [data]
            for item in data:
                prompts_to_create.append(
                    PromptCreate(
                        name=item["name"],
                        description=item.get("description"),
                        content=item["content"],
                        tags=item.get("tags", []),
                        folder_id=request.folder_id,
                    )
                )
        except (json.JSONDecodeError, KeyError) as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON format: {e}")
    elif request.format == "csv":
        try:
            reader = csv.DictReader(io.StringIO(request.content))
            for row in reader:
                prompts_to_create.append(
                    PromptCreate(
                        name=row["name"],
                        description=row.get("description") or None,
                        content=row["content"],
                        tags=row.get("tags", "").split(",") if row.get("tags") else [],
                        folder_id=request.folder_id,
                    )
                )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid CSV format: {e}")
    elif request.format == "markdown":
        # Simple markdown parser
        lines = request.content.split("\n")
        current_prompt: Optional[dict[str, Any]] = None
        in_code_block = False
        content_lines: list[str] = []

        for line in lines:
            if line.startswith("## "):
                # Save previous prompt if exists
                if current_prompt and content_lines:
                    current_prompt["content"] = "\n".join(content_lines)
                    prompts_to_create.append(
                        PromptCreate(
                            name=current_prompt["name"],
                            description=current_prompt.get("description"),
                            content=current_prompt["content"],
                            tags=cast(list[str], current_prompt.get("tags", [])),
                            folder_id=request.folder_id,
                        )
                    )
                # Start new prompt
                current_prompt = {"name": line[3:].strip()}
                content_lines = []
                in_code_block = False
            elif current_prompt:
                if line.startswith("*") and line.endswith("*"):
                    current_prompt["description"] = line[1:-1].strip()
                elif line.startswith("**Tags**:"):
                    tags_str = line[9:].strip()
                    current_prompt["tags"] = [
                        t.strip() for t in tags_str.split(",") if t.strip()
                    ]
                elif line == "```":
                    in_code_block = not in_code_block
                elif in_code_block:
                    content_lines.append(line)

        # Save last prompt
        if current_prompt and content_lines:
            current_prompt["content"] = "\n".join(content_lines)
            prompts_to_create.append(
                PromptCreate(
                    name=current_prompt["name"],
                    description=current_prompt.get("description"),
                    content=current_prompt["content"],
                    tags=cast(list[str], current_prompt.get("tags", [])),
                    folder_id=request.folder_id,
                )
            )
    else:
        raise HTTPException(status_code=400, detail="Invalid import format")

    # Create all prompts
    created_count = 0
    for prompt_create in prompts_to_create:
        await service.create_prompt(prompt_create)
        created_count += 1

    return {"message": f"Successfully imported {created_count} prompts"}
