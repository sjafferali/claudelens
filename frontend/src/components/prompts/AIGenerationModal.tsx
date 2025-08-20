import { useState, useEffect } from 'react';
import { Sparkles, Check, Copy, RefreshCw } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useGenerateMetadata, useGenerateContent } from '@/hooks/useAI';
import { cn } from '@/utils/cn';
import { copyToClipboard } from '@/utils/clipboard';

interface AIGenerationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAccept: (result: GenerationResult) => void;
  initialContent?: string;
  mode?: 'metadata' | 'content';
}

interface GenerationResult {
  type: 'metadata' | 'content';
  data: {
    name?: string;
    description?: string;
    tags?: string[];
    content?: string;
    variables?: string[];
  };
}

type TabType = 'metadata' | 'content';

export function AIGenerationModal({
  isOpen,
  onClose,
  onAccept,
  initialContent = '',
  mode = 'metadata',
}: AIGenerationModalProps) {
  const [activeTab, setActiveTab] = useState<TabType>(mode);
  const [requirements, setRequirements] = useState('');
  const [context, setContext] = useState(initialContent);
  const [contentType, setContentType] = useState<
    'prompt' | 'description' | 'tags'
  >('prompt');
  const [generatedResult, setGeneratedResult] = useState<{
    name?: string;
    description?: string;
    tags?: string[];
    content?: string;
  } | null>(null);
  const [copiedField, setCopiedField] = useState<string | null>(null);

  const generateMetadata = useGenerateMetadata();
  const generateContent = useGenerateContent();

  // Reset form when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      setActiveTab(mode);
      setRequirements('');
      setContext(initialContent);
      setGeneratedResult(null);
      setCopiedField(null);
    }
  }, [isOpen, mode, initialContent]);

  const handleGenerate = async () => {
    if (!requirements.trim()) return;

    try {
      if (activeTab === 'metadata') {
        const result = await generateMetadata.mutateAsync({
          content: context,
          context: context
            ? 'Existing prompt content provided for analysis'
            : undefined,
          requirements: requirements,
        });
        setGeneratedResult(result);
      } else {
        const result = await generateContent.mutateAsync({
          type: contentType,
          requirements: requirements,
          context: context || undefined,
          existing_content: context || undefined,
        });
        setGeneratedResult(result);
      }
    } catch (error) {
      console.error('Generation failed:', error);
    }
  };

  const handleAccept = () => {
    if (!generatedResult) return;

    const result: GenerationResult = {
      type: activeTab,
      data:
        activeTab === 'metadata'
          ? generatedResult
          : { content: generatedResult.content },
    };

    onAccept(result);
    onClose();
  };

  const handleCopyField = async (field: string, value: string) => {
    const success = await copyToClipboard(value);
    if (success) {
      setCopiedField(field);
      setTimeout(() => setCopiedField(null), 2000);
    }
  };

  const isGenerating = generateMetadata.isPending || generateContent.isPending;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-purple-500" />
            AI Generation Assistant
          </DialogTitle>
        </DialogHeader>

        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Tabs */}
          <div className="flex border-b border-gray-200">
            <button
              onClick={() => setActiveTab('metadata')}
              className={cn(
                'flex-1 px-4 py-2 text-sm font-medium border-b-2 transition-colors',
                activeTab === 'metadata'
                  ? 'border-purple-500 text-purple-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              )}
            >
              Generate Metadata
            </button>
            <button
              onClick={() => setActiveTab('content')}
              className={cn(
                'flex-1 px-4 py-2 text-sm font-medium border-b-2 transition-colors',
                activeTab === 'content'
                  ? 'border-purple-500 text-purple-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              )}
            >
              Generate Content
            </button>
          </div>

          <div className="flex-1 overflow-auto p-4 space-y-4">
            {/* Form Section */}
            <div className="space-y-4">
              {activeTab === 'content' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Content Type
                  </label>
                  <select
                    value={contentType}
                    onChange={(e) =>
                      setContentType(
                        e.target.value as 'prompt' | 'description' | 'tags'
                      )
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500"
                  >
                    <option value="prompt">Prompt Content</option>
                    <option value="description">Description</option>
                    <option value="tags">Tags</option>
                  </select>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Requirements *
                </label>
                <textarea
                  value={requirements}
                  onChange={(e) => setRequirements(e.target.value)}
                  placeholder={
                    activeTab === 'metadata'
                      ? 'Describe what this prompt does and what metadata should be generated...'
                      : 'Describe what content you want to generate...'
                  }
                  className="w-full h-24 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 resize-none"
                />
              </div>

              {(context || activeTab === 'content') && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Context{' '}
                    {activeTab === 'metadata'
                      ? '(Existing Content)'
                      : '(Optional)'}
                  </label>
                  <textarea
                    value={context}
                    onChange={(e) => setContext(e.target.value)}
                    placeholder="Provide additional context or existing content..."
                    className="w-full h-20 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 resize-none"
                  />
                </div>
              )}

              <button
                onClick={handleGenerate}
                disabled={!requirements.trim() || isGenerating}
                className={cn(
                  'w-full flex items-center justify-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-500 to-blue-500 text-white rounded-md font-medium transition-all duration-200 hover:from-purple-600 hover:to-blue-600 disabled:opacity-50 disabled:cursor-not-allowed',
                  isGenerating && 'animate-pulse'
                )}
              >
                {isGenerating ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4" />
                    Generate
                  </>
                )}
              </button>
            </div>

            {/* Results Section */}
            {generatedResult && (
              <div className="border-t pt-4 space-y-4">
                <h3 className="text-lg font-medium text-gray-900">
                  Generated Result
                </h3>

                {activeTab === 'metadata' ? (
                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Name
                      </label>
                      <div className="flex items-center gap-2">
                        <input
                          type="text"
                          value={generatedResult.name || ''}
                          readOnly
                          className="flex-1 px-3 py-2 bg-gray-50 border border-gray-300 rounded-md text-sm"
                        />
                        <button
                          onClick={() =>
                            handleCopyField('name', generatedResult.name ?? '')
                          }
                          className="p-2 text-gray-500 hover:text-gray-700"
                        >
                          {copiedField === 'name' ? (
                            <Check className="h-4 w-4 text-green-500" />
                          ) : (
                            <Copy className="h-4 w-4" />
                          )}
                        </button>
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Description
                      </label>
                      <div className="flex items-start gap-2">
                        <textarea
                          value={generatedResult.description || ''}
                          readOnly
                          className="flex-1 px-3 py-2 bg-gray-50 border border-gray-300 rounded-md text-sm resize-none"
                          rows={3}
                        />
                        <button
                          onClick={() =>
                            handleCopyField(
                              'description',
                              generatedResult.description ?? ''
                            )
                          }
                          className="p-2 text-gray-500 hover:text-gray-700"
                        >
                          {copiedField === 'description' ? (
                            <Check className="h-4 w-4 text-green-500" />
                          ) : (
                            <Copy className="h-4 w-4" />
                          )}
                        </button>
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Tags
                      </label>
                      <div className="flex flex-wrap gap-2">
                        {generatedResult.tags?.map(
                          (tag: string, index: number) => (
                            <span
                              key={index}
                              className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800"
                            >
                              {tag}
                            </span>
                          )
                        )}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Content
                    </label>
                    <div className="flex flex-col gap-2">
                      <textarea
                        value={generatedResult.content || ''}
                        readOnly
                        className="w-full h-40 px-3 py-2 bg-gray-50 border border-gray-300 rounded-md text-sm resize-none"
                      />
                      <button
                        onClick={() =>
                          handleCopyField(
                            'content',
                            generatedResult.content ?? ''
                          )
                        }
                        className="self-end p-2 text-gray-500 hover:text-gray-700"
                      >
                        {copiedField === 'content' ? (
                          <Check className="h-4 w-4 text-green-500" />
                        ) : (
                          <Copy className="h-4 w-4" />
                        )}
                      </button>
                    </div>
                  </div>
                )}

                <div className="flex justify-end gap-3 pt-4 border-t">
                  <button
                    onClick={onClose}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleAccept}
                    className="px-4 py-2 text-sm font-medium text-white bg-purple-600 rounded-md hover:bg-purple-700 transition-colors"
                  >
                    Accept & Apply
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
