import { useState, useEffect } from 'react';
import { X, Save, Loader2, Hash, Variable, Eye, EyeOff } from 'lucide-react';
import { Button } from '@/components/common';
import { cn } from '@/utils/cn';
import { Prompt } from '@/api/types';
import {
  useFolders,
  useCreatePrompt,
  useUpdatePrompt,
} from '@/hooks/usePrompts';
import { extractVariables } from '@/api/prompts';
import { VariableChips } from './VariableChips';

interface PromptEditorProps {
  isOpen: boolean;
  onClose: () => void;
  prompt?: Prompt; // If provided, we're editing; otherwise creating
  folderId?: string; // Default folder for new prompts
}

interface FormData {
  name: string;
  description: string;
  content: string;
  tags: string[];
  folder_id?: string;
  visibility: string;
}

export function PromptEditor({
  isOpen,
  onClose,
  prompt,
  folderId,
}: PromptEditorProps) {
  const [formData, setFormData] = useState<FormData>({
    name: '',
    description: '',
    content: '',
    tags: [],
    folder_id: folderId,
    visibility: 'private',
  });
  const [tagInput, setTagInput] = useState('');
  const [showPreview, setShowPreview] = useState(false);
  const [errors, setErrors] = useState<Partial<FormData>>({});

  const { data: folders } = useFolders();
  const createPrompt = useCreatePrompt();
  const updatePrompt = useUpdatePrompt();

  const isEditing = !!prompt;
  const isLoading = createPrompt.isPending || updatePrompt.isPending;

  // Extract variables from content
  const extractedVariables = extractVariables(formData.content);

  // Initialize form when prompt changes
  useEffect(() => {
    if (isOpen) {
      if (prompt) {
        setFormData({
          name: prompt.name,
          description: prompt.description || '',
          content: prompt.content,
          tags: prompt.tags,
          folder_id: prompt.folder_id,
          visibility: prompt.visibility,
        });
      } else {
        setFormData({
          name: '',
          description: '',
          content: '',
          tags: [],
          folder_id: folderId,
          visibility: 'private',
        });
      }
      setTagInput('');
      setErrors({});
      setShowPreview(false);
    }
  }, [isOpen, prompt, folderId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate form
    const newErrors: Partial<FormData> = {};
    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }
    if (!formData.content.trim()) {
      newErrors.content = 'Content is required';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    try {
      if (isEditing && prompt) {
        await updatePrompt.mutateAsync({
          promptId: prompt._id,
          promptData: {
            name: formData.name.trim(),
            description: formData.description.trim() || undefined,
            content: formData.content.trim(),
            tags: formData.tags,
            folder_id: formData.folder_id || undefined,
            visibility: formData.visibility,
          },
        });
      } else {
        await createPrompt.mutateAsync({
          name: formData.name.trim(),
          description: formData.description.trim() || undefined,
          content: formData.content.trim(),
          tags: formData.tags,
          folder_id: formData.folder_id || undefined,
          visibility: formData.visibility,
        });
      }
      onClose();
    } catch (error) {
      console.error('Failed to save prompt:', error);
    }
  };

  const handleAddTag = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && tagInput.trim()) {
      e.preventDefault();
      const newTag = tagInput.trim().toLowerCase();
      if (!formData.tags.includes(newTag)) {
        setFormData((prev) => ({
          ...prev,
          tags: [...prev.tags, newTag],
        }));
      }
      setTagInput('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setFormData((prev) => ({
      ...prev,
      tags: prev.tags.filter((tag) => tag !== tagToRemove),
    }));
  };

  const handleContentChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setFormData((prev) => ({ ...prev, content: e.target.value }));
    if (errors.content) {
      setErrors((prev) => ({ ...prev, content: undefined }));
    }
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Panel */}
      <div className="relative ml-auto w-full max-w-2xl bg-background border-l shadow-xl flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-2xl font-bold">
            {isEditing ? 'Edit Prompt' : 'Create Prompt'}
          </h2>
          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setShowPreview(!showPreview)}
            >
              {showPreview ? (
                <>
                  <EyeOff className="h-4 w-4 mr-2" />
                  Edit
                </>
              ) : (
                <>
                  <Eye className="h-4 w-4 mr-2" />
                  Preview
                </>
              )}
            </Button>
            <button
              onClick={onClose}
              className="p-2 hover:bg-accent rounded-md"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden">
          {showPreview ? (
            <PreviewMode formData={formData} variables={extractedVariables} />
          ) : (
            <form onSubmit={handleSubmit} className="h-full flex flex-col">
              <div className="flex-1 overflow-y-auto p-6 space-y-6">
                {/* Name */}
                <div className="space-y-2">
                  <label htmlFor="name" className="text-sm font-medium">
                    Name *
                  </label>
                  <input
                    id="name"
                    type="text"
                    value={formData.name}
                    onChange={(e) => {
                      setFormData((prev) => ({
                        ...prev,
                        name: e.target.value,
                      }));
                      if (errors.name) {
                        setErrors((prev) => ({ ...prev, name: undefined }));
                      }
                    }}
                    placeholder="Enter prompt name"
                    className={cn(
                      'w-full px-3 py-2 border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                      errors.name && 'border-destructive'
                    )}
                  />
                  {errors.name && (
                    <p className="text-sm text-destructive">{errors.name}</p>
                  )}
                </div>

                {/* Description */}
                <div className="space-y-2">
                  <label htmlFor="description" className="text-sm font-medium">
                    Description
                  </label>
                  <input
                    id="description"
                    type="text"
                    value={formData.description}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        description: e.target.value,
                      }))
                    }
                    placeholder="Optional description"
                    className="w-full px-3 py-2 border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                  />
                </div>

                {/* Folder */}
                <div className="space-y-2">
                  <label htmlFor="folder" className="text-sm font-medium">
                    Folder
                  </label>
                  <select
                    id="folder"
                    value={formData.folder_id || ''}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        folder_id: e.target.value || undefined,
                      }))
                    }
                    className="w-full px-3 py-2 border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                  >
                    <option value="">Root (No folder)</option>
                    {folders?.map((folder) => (
                      <option key={folder._id} value={folder._id}>
                        {folder.name}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Content */}
                <div className="space-y-2">
                  <label htmlFor="content" className="text-sm font-medium">
                    Content *
                  </label>
                  <textarea
                    id="content"
                    value={formData.content}
                    onChange={handleContentChange}
                    placeholder="Enter your prompt content here. Use {{variable}} for dynamic values."
                    rows={12}
                    className={cn(
                      'w-full px-3 py-2 border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent resize-none font-mono text-sm',
                      errors.content && 'border-destructive'
                    )}
                  />
                  {errors.content && (
                    <p className="text-sm text-destructive">{errors.content}</p>
                  )}
                </div>

                {/* Variables */}
                {extractedVariables.length > 0 && (
                  <div className="space-y-2">
                    <label className="text-sm font-medium flex items-center gap-2">
                      <Variable className="h-4 w-4" />
                      Variables Found
                    </label>
                    <VariableChips variables={extractedVariables} />
                  </div>
                )}

                {/* Tags */}
                <div className="space-y-2">
                  <label htmlFor="tags" className="text-sm font-medium">
                    Tags
                  </label>
                  <input
                    id="tags"
                    type="text"
                    value={tagInput}
                    onChange={(e) => setTagInput(e.target.value)}
                    onKeyDown={handleAddTag}
                    placeholder="Type a tag and press Enter"
                    className="w-full px-3 py-2 border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                  />
                  {formData.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                      {formData.tags.map((tag, index) => (
                        <span
                          key={index}
                          className="inline-flex items-center gap-1 px-2 py-1 bg-secondary text-secondary-foreground rounded-md text-sm"
                        >
                          <Hash className="h-3 w-3" />
                          {tag}
                          <button
                            type="button"
                            onClick={() => handleRemoveTag(tag)}
                            className="hover:text-destructive"
                          >
                            <X className="h-3 w-3" />
                          </button>
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Visibility */}
                <div className="space-y-2">
                  <label htmlFor="visibility" className="text-sm font-medium">
                    Visibility
                  </label>
                  <select
                    id="visibility"
                    value={formData.visibility}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        visibility: e.target.value,
                      }))
                    }
                    className="w-full px-3 py-2 border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                  >
                    <option value="private">Private</option>
                    <option value="team">Team</option>
                    <option value="public">Public</option>
                  </select>
                </div>
              </div>

              {/* Footer */}
              <div className="flex items-center justify-end gap-3 p-6 border-t">
                <Button
                  type="button"
                  variant="outline"
                  onClick={onClose}
                  disabled={isLoading}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={isLoading}>
                  {isLoading ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      {isEditing ? 'Updating...' : 'Creating...'}
                    </>
                  ) : (
                    <>
                      <Save className="h-4 w-4 mr-2" />
                      {isEditing ? 'Update Prompt' : 'Create Prompt'}
                    </>
                  )}
                </Button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}

interface PreviewModeProps {
  formData: FormData;
  variables: string[];
}

function PreviewMode({ formData, variables }: PreviewModeProps) {
  return (
    <div className="h-full overflow-y-auto p-6 space-y-6">
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-semibold">
            {formData.name || 'Untitled Prompt'}
          </h3>
          {formData.description && (
            <p className="text-muted-foreground mt-1">{formData.description}</p>
          )}
        </div>

        {formData.tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {formData.tags.map((tag, index) => (
              <span
                key={index}
                className="inline-flex items-center gap-1 px-2 py-1 bg-secondary text-secondary-foreground rounded-md text-sm"
              >
                <Hash className="h-3 w-3" />
                {tag}
              </span>
            ))}
          </div>
        )}

        {variables.length > 0 && (
          <div>
            <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
              <Variable className="h-4 w-4" />
              Variables ({variables.length})
            </h4>
            <VariableChips variables={variables} />
          </div>
        )}

        <div className="space-y-2">
          <h4 className="text-sm font-medium">Content</h4>
          <div className="p-4 bg-accent/50 rounded-md">
            <pre className="whitespace-pre-wrap font-mono text-sm">
              {formData.content || 'No content yet...'}
            </pre>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-muted-foreground">Visibility:</span>
            <span className="ml-2 capitalize">{formData.visibility}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Folder:</span>
            <span className="ml-2">
              {formData.folder_id ? 'Selected folder' : 'Root'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
