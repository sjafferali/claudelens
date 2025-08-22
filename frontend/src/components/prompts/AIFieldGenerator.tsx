import { useState, useRef, useEffect } from 'react';
import { Sparkles, Check, X, Loader2 } from 'lucide-react';
import { cn } from '@/utils/cn';
import { toast } from 'react-hot-toast';

interface AIFieldGeneratorProps {
  fieldName: 'name' | 'description' | 'content';
  currentValue: string;
  onGenerate: (value: string) => void;
  context?: {
    name?: string;
    description?: string;
    content?: string;
  };
  className?: string;
}

export function AIFieldGenerator({
  fieldName,
  currentValue,
  onGenerate,
  context = {},
  className,
}: AIFieldGeneratorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [instruction, setInstruction] = useState('');
  const [generatedValue, setGeneratedValue] = useState('');
  const [showPreview, setShowPreview] = useState(false);
  const [popupPosition, setPopupPosition] = useState<{
    top: number;
    left: number;
  } | null>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const popupRef = useRef<HTMLDivElement>(null);

  // Calculate popup position to keep it within viewport
  useEffect(() => {
    const calculatePosition = () => {
      if (isOpen && buttonRef.current) {
        const buttonRect = buttonRef.current.getBoundingClientRect();
        const popupWidth = 384; // w-96 = 24rem = 384px
        const popupHeight = 400; // Approximate height
        const padding = 8;

        let left = buttonRect.left;
        let top = buttonRect.bottom + 8;

        // Check if popup would overflow right edge
        if (left + popupWidth > window.innerWidth - padding) {
          // Align to right edge of button or viewport
          left = Math.max(
            padding,
            Math.min(
              buttonRect.right - popupWidth,
              window.innerWidth - popupWidth - padding
            )
          );
        }

        // Check if popup would overflow left edge
        if (left < padding) {
          left = padding;
        }

        // Check if popup would overflow bottom edge
        if (top + popupHeight > window.innerHeight - padding) {
          // Show above button if there's more space there
          const spaceAbove = buttonRect.top;
          const spaceBelow = window.innerHeight - buttonRect.bottom;

          if (spaceAbove > spaceBelow && spaceAbove > popupHeight) {
            top = buttonRect.top - popupHeight - 8;
          } else {
            // Keep below but adjust height if needed
            top = Math.min(top, window.innerHeight - popupHeight - padding);
          }
        }

        setPopupPosition({ top, left });
      }
    };

    calculatePosition();

    // Recalculate on window resize
    if (isOpen) {
      window.addEventListener('resize', calculatePosition);
      window.addEventListener('scroll', calculatePosition);
      return () => {
        window.removeEventListener('resize', calculatePosition);
        window.removeEventListener('scroll', calculatePosition);
      };
    }
  }, [isOpen]);

  // Close popup when clicking outside
  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (event: MouseEvent) => {
      if (
        buttonRef.current &&
        popupRef.current &&
        !buttonRef.current.contains(event.target as Node) &&
        !popupRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
        setInstruction('');
        setGeneratedValue('');
        setShowPreview(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const handleGenerate = async () => {
    if (!instruction.trim()) {
      toast.error('Please provide instructions for the AI');
      return;
    }

    setIsGenerating(true);

    try {
      // Build the context to send to AI
      const contextData = {
        current_value: currentValue,
        ...context,
      };

      const response = await fetch('/api/v1/ai/generate-field', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          field: fieldName,
          instruction: instruction,
          context: contextData,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to generate content');
      }

      const data = await response.json();
      setGeneratedValue(data.value);
      setShowPreview(true);
    } catch (error) {
      console.error('Generation failed:', error);
      toast.error('Failed to generate content. Please try again.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleAccept = () => {
    // Apply generated value with animation effect
    onGenerate(generatedValue);

    // Add visual feedback to the field that was updated
    setTimeout(() => {
      const element = document.querySelector(`[data-field="${fieldName}"]`);
      if (element) {
        element.classList.add('field-updated');
        setTimeout(() => {
          element.classList.remove('field-updated');
        }, 1500);
      }
    }, 100);

    setIsOpen(false);
    setInstruction('');
    setGeneratedValue('');
    setShowPreview(false);
    toast.success(
      `${fieldName.charAt(0).toUpperCase() + fieldName.slice(1)} updated successfully`
    );
  };

  const handleCancel = () => {
    setIsOpen(false);
    setInstruction('');
    setGeneratedValue('');
    setShowPreview(false);
  };

  const getPlaceholder = () => {
    switch (fieldName) {
      case 'name':
        return 'e.g., Make it more descriptive, Add context about..., Shorten to 5 words';
      case 'description':
        return 'e.g., Explain what this prompt does, Add details about use cases, Make it concise';
      case 'content':
        return 'e.g., Make it more detailed, Add examples, Convert to step-by-step format';
      default:
        return 'Describe what you want the AI to do...';
    }
  };

  return (
    <>
      {/* Sparkle Button */}
      <button
        ref={buttonRef}
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          'p-1.5 rounded-md transition-all hover:bg-accent/10 group',
          isOpen && 'bg-accent/10',
          className
        )}
        title={`Generate ${fieldName} with AI`}
      >
        <Sparkles
          className={cn(
            'h-4 w-4 transition-colors',
            'text-muted-foreground group-hover:text-purple-500',
            isOpen && 'text-purple-500'
          )}
        />
      </button>

      {/* AI Generation Popup */}
      {isOpen && popupPosition && (
        <div
          ref={popupRef}
          className="fixed z-50 p-4 bg-background border border-border rounded-lg shadow-lg w-96 max-h-[400px] overflow-y-auto"
          style={{
            top: `${popupPosition.top}px`,
            left: `${popupPosition.left}px`,
          }}
        >
          <div className="space-y-3">
            {/* Header */}
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-medium flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-purple-500" />
                Generate {fieldName}
              </h4>
              <button
                onClick={handleCancel}
                className="p-1 hover:bg-accent rounded"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Instruction Input */}
            <div className="space-y-2">
              <label className="text-xs text-muted-foreground">
                What should the AI do with this {fieldName}?
              </label>
              <textarea
                value={instruction}
                onChange={(e) => setInstruction(e.target.value)}
                placeholder={getPlaceholder()}
                className={cn(
                  'w-full px-3 py-2 text-sm rounded-md resize-none',
                  'bg-background text-foreground',
                  'border border-border',
                  'focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent',
                  'placeholder:text-muted-foreground'
                )}
                rows={3}
                disabled={isGenerating}
              />
            </div>

            {/* Preview of Generated Content */}
            {showPreview && generatedValue && (
              <div className="space-y-2">
                <label className="text-xs text-muted-foreground">
                  Preview:
                </label>
                <div
                  className={cn(
                    'p-3 rounded-md',
                    'bg-accent/10 border border-accent/20',
                    'text-sm text-foreground',
                    fieldName === 'content' && 'font-mono',
                    'max-h-32 overflow-y-auto'
                  )}
                >
                  {generatedValue}
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex justify-end gap-2">
              {showPreview ? (
                <>
                  <button
                    onClick={() => {
                      setShowPreview(false);
                      setGeneratedValue('');
                    }}
                    className="px-3 py-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
                  >
                    Regenerate
                  </button>
                  <button
                    onClick={handleAccept}
                    className="px-3 py-1.5 text-sm bg-purple-600 text-white rounded-md hover:bg-purple-700 flex items-center gap-1.5"
                  >
                    <Check className="h-3.5 w-3.5" />
                    Apply
                  </button>
                </>
              ) : (
                <button
                  onClick={handleGenerate}
                  disabled={!instruction.trim() || isGenerating}
                  className={cn(
                    'px-3 py-1.5 text-sm rounded-md flex items-center gap-1.5',
                    'bg-gradient-to-r from-purple-500 to-blue-500 text-white',
                    'hover:from-purple-600 hover:to-blue-600',
                    'disabled:opacity-50 disabled:cursor-not-allowed',
                    'transition-all duration-200'
                  )}
                >
                  {isGenerating ? (
                    <>
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Sparkles className="h-3.5 w-3.5" />
                      Generate
                    </>
                  )}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
