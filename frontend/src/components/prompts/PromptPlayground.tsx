import { useState, useEffect } from 'react';
import {
  X,
  Play,
  Loader2,
  Copy,
  RotateCcw,
  AlertCircle,
  CheckCircle2,
  Clock,
  Info,
  Lightbulb,
  Zap,
  DollarSign,
  Bot,
  Settings2,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { Button } from '@/components/common';
import { Prompt, PromptTestResponse } from '@/api/types';
import { useTestPrompt } from '@/hooks/usePrompts';
import { useAIAvailable } from '@/hooks/useAI';
import { substituteVariables, extractVariables } from '@/api/prompts';
import { VariableHelper } from './VariableHelper';
import { toast } from 'react-hot-toast';
import { Link } from 'react-router-dom';

interface PromptPlaygroundProps {
  isOpen: boolean;
  onClose: () => void;
  prompt: Prompt;
}

interface VariableInputs {
  [key: string]: string;
}

export function PromptPlayground({
  isOpen,
  onClose,
  prompt,
}: PromptPlaygroundProps) {
  const [variableInputs, setVariableInputs] = useState<VariableInputs>({});
  const [testResult, setTestResult] = useState<PromptTestResponse | null>(null);
  const [testError, setTestError] = useState<string | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(2048);
  const [systemPrompt, setSystemPrompt] = useState('');

  const testPrompt = useTestPrompt();
  const { isAvailable: isAIAvailable, settings: aiSettings } = useAIAvailable();
  const variables = extractVariables(prompt.content);
  const previewContent = substituteVariables(prompt.content, variableInputs);
  const isLoading = testPrompt.isPending;

  // Initialize variable inputs when prompt changes
  useEffect(() => {
    if (isOpen) {
      const initialInputs: VariableInputs = {};
      variables.forEach((variable) => {
        initialInputs[variable] = '';
      });
      setVariableInputs(initialInputs);
      setTestResult(null);
      setTestError(null);
    }
  }, [isOpen, variables]);

  const handleVariableChange = (variable: string, value: string) => {
    setVariableInputs((prev) => ({
      ...prev,
      [variable]: value,
    }));
  };

  const handleTest = async () => {
    // Check if AI is available
    if (!isAIAvailable) {
      toast.error(
        <div>
          <p>AI features are not enabled.</p>
          <Link
            to="/settings"
            className="underline text-blue-500 hover:text-blue-600"
            onClick={() => onClose()}
          >
            Configure AI settings →
          </Link>
        </div>,
        { duration: 5000 }
      );
      return;
    }

    // Check if all variables have values
    const missingVariables = variables.filter(
      (v) => !variableInputs[v]?.trim()
    );
    if (missingVariables.length > 0) {
      toast.error(`Please provide values for: ${missingVariables.join(', ')}`);
      return;
    }

    try {
      setTestError(null);
      const result = await testPrompt.mutateAsync({
        promptId: prompt._id,
        variables: variableInputs,
        temperature: temperature,
        max_tokens: maxTokens,
        system_prompt: systemPrompt || undefined,
      });
      setTestResult(result);

      // Show error from API if present
      if (result.error) {
        setTestError(result.error);
      }
    } catch (error) {
      console.error('Test failed:', error);
      const errorMessage =
        (error as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || 'Failed to test prompt';
      setTestError(errorMessage);
      setTestResult(null);
    }
  };

  const getVariablePlaceholder = (variable: string): string => {
    const lowerVar = variable.toLowerCase();

    if (lowerVar.includes('code')) {
      return 'Enter code snippet or file content...';
    }
    if (lowerVar.includes('text') || lowerVar.includes('content')) {
      return 'Enter text content...';
    }
    if (lowerVar.includes('language') || lowerVar.includes('lang')) {
      return 'e.g., javascript, python, java...';
    }
    if (lowerVar.includes('url') || lowerVar.includes('link')) {
      return 'e.g., https://example.com...';
    }
    if (lowerVar.includes('name')) {
      return 'Enter name...';
    }
    if (lowerVar.includes('description')) {
      return 'Enter description...';
    }
    if (lowerVar.includes('requirement')) {
      return 'Enter requirements or constraints...';
    }
    if (lowerVar.includes('format')) {
      return 'e.g., json, markdown, plain text...';
    }
    if (lowerVar.includes('count') || lowerVar.includes('number')) {
      return 'Enter a number...';
    }
    if (lowerVar.includes('date') || lowerVar.includes('time')) {
      return 'e.g., 2024-01-15 or January 15, 2024...';
    }

    return `Enter value for ${variable}...`;
  };

  const handleReset = () => {
    const resetInputs: VariableInputs = {};
    variables.forEach((variable) => {
      resetInputs[variable] = '';
    });
    setVariableInputs(resetInputs);
    setTestResult(null);
    setTestError(null);
    setTemperature(0.7);
    setMaxTokens(2048);
    setSystemPrompt('');
  };

  const handleCopyResult = () => {
    if (testResult) {
      navigator.clipboard.writeText(testResult.result);
      toast.success('Result copied to clipboard');
    }
  };

  const handleCopyPreview = () => {
    navigator.clipboard.writeText(previewContent);
    toast.success('Preview copied to clipboard');
  };

  const canTest = variables.every((v) => variableInputs[v]?.trim());

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
      <div className="relative ml-auto w-full max-w-4xl bg-background border-l shadow-xl flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h2 className="text-2xl font-bold">Test Prompt</h2>
            <p className="text-muted-foreground mt-1">{prompt.name}</p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleReset}
              disabled={isLoading}
            >
              <RotateCcw className="h-4 w-4 mr-2" />
              Reset
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
        <div className="flex-1 overflow-hidden grid grid-cols-1 lg:grid-cols-2 gap-6 p-6">
          {/* Left Panel: Input */}
          <div className="space-y-6 overflow-y-auto">
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Variables</h3>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Lightbulb className="h-3 w-3" />
                  <span>Fill in all variables to test</span>
                </div>
              </div>
              {variables.length > 0 ? (
                <div className="space-y-4">
                  {/* Variable Helper */}
                  <VariableHelper
                    variables={variables}
                    showExamples={true}
                    className="mb-4"
                  />

                  {/* Variable Inputs */}
                  <div className="space-y-4">
                    {variables.map((variable) => {
                      const hasValue = variableInputs[variable]?.trim();
                      return (
                        <div key={variable} className="space-y-2">
                          <label
                            htmlFor={`var-${variable}`}
                            className="text-sm font-medium flex items-center justify-between"
                          >
                            <span className="font-mono text-primary">{`{{${variable}}}`}</span>
                            {hasValue ? (
                              <span className="flex items-center gap-1 text-xs text-green-600">
                                <CheckCircle2 className="h-3 w-3" />
                                Filled
                              </span>
                            ) : (
                              <span className="flex items-center gap-1 text-xs text-muted-foreground">
                                <AlertCircle className="h-3 w-3" />
                                Required
                              </span>
                            )}
                          </label>
                          <textarea
                            id={`var-${variable}`}
                            value={variableInputs[variable] || ''}
                            onChange={(e) =>
                              handleVariableChange(variable, e.target.value)
                            }
                            placeholder={getVariablePlaceholder(variable)}
                            rows={3}
                            className={`w-full px-3 py-2 border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent resize-none text-sm ${
                              !hasValue ? 'border-orange-300' : ''
                            }`}
                          />
                        </div>
                      );
                    })}
                  </div>
                </div>
              ) : (
                <div className="p-4 bg-muted/30 rounded-lg">
                  <div className="flex items-start gap-2">
                    <Info className="h-4 w-4 text-muted-foreground mt-0.5" />
                    <div className="text-sm text-muted-foreground">
                      <p>This prompt doesn't have any variables.</p>
                      <p className="mt-1 text-xs">
                        Variables make prompts reusable. Add them using{' '}
                        {`{{name}}`} syntax.
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Preview */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold">Preview</h3>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={handleCopyPreview}
                  disabled={!previewContent}
                >
                  <Copy className="h-4 w-4 mr-2" />
                  Copy
                </Button>
              </div>
              <div className="p-4 bg-accent/30 border rounded-lg min-h-32 max-h-64 overflow-y-auto">
                <pre className="whitespace-pre-wrap font-mono text-sm">
                  {previewContent || 'Enter variable values to see preview...'}
                </pre>
              </div>
            </div>

            {/* Advanced Settings */}
            <div className="border rounded-lg">
              <button
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="w-full px-4 py-3 flex items-center justify-between hover:bg-accent/50 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <Settings2 className="h-4 w-4" />
                  <span className="font-medium">Advanced Settings</span>
                </div>
                {showAdvanced ? (
                  <ChevronUp className="h-4 w-4" />
                ) : (
                  <ChevronDown className="h-4 w-4" />
                )}
              </button>

              {showAdvanced && (
                <div className="p-4 space-y-4 border-t">
                  {/* Temperature */}
                  <div>
                    <label className="flex items-center justify-between text-sm font-medium mb-2">
                      <span>Temperature</span>
                      <span className="text-muted-foreground">
                        {temperature}
                      </span>
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="2"
                      step="0.1"
                      value={temperature}
                      onChange={(e) =>
                        setTemperature(parseFloat(e.target.value))
                      }
                      className="w-full"
                    />
                    <div className="flex justify-between text-xs text-muted-foreground mt-1">
                      <span>Precise</span>
                      <span>Creative</span>
                    </div>
                  </div>

                  {/* Max Tokens */}
                  <div>
                    <label className="flex items-center justify-between text-sm font-medium mb-2">
                      <span>Max Tokens</span>
                      <span className="text-muted-foreground">{maxTokens}</span>
                    </label>
                    <input
                      type="range"
                      min="100"
                      max="4096"
                      step="100"
                      value={maxTokens}
                      onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                      className="w-full"
                    />
                    <div className="flex justify-between text-xs text-muted-foreground mt-1">
                      <span>100</span>
                      <span>4096</span>
                    </div>
                  </div>

                  {/* System Prompt */}
                  <div>
                    <label className="text-sm font-medium mb-2 block">
                      System Prompt (Optional)
                    </label>
                    <textarea
                      value={systemPrompt}
                      onChange={(e) => setSystemPrompt(e.target.value)}
                      placeholder="Provide context or instructions for the AI model..."
                      rows={3}
                      className="w-full px-3 py-2 border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent resize-none text-sm"
                    />
                  </div>

                  {/* AI Model Info */}
                  {aiSettings && (
                    <div className="p-3 bg-accent/30 rounded-md text-sm">
                      <div className="flex items-center gap-2 text-muted-foreground">
                        <Bot className="h-4 w-4" />
                        <span>
                          Using model:{' '}
                          <span className="font-medium text-foreground">
                            {aiSettings.model}
                          </span>
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Test Button */}
            <Button
              onClick={handleTest}
              disabled={!canTest || isLoading || !isAIAvailable}
              className="w-full"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Testing...
                </>
              ) : !isAIAvailable ? (
                <>
                  <AlertCircle className="h-4 w-4 mr-2" />
                  AI Not Configured
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" />
                  Test Prompt with AI
                </>
              )}
            </Button>

            {/* AI Settings Link */}
            {!isAIAvailable && (
              <div className="p-3 bg-orange-50 border border-orange-200 rounded-lg text-orange-700 dark:bg-orange-900/20 dark:border-orange-800 dark:text-orange-300 text-sm">
                <div className="flex items-start gap-2">
                  <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
                  <div>
                    <p>AI features are not configured.</p>
                    <Link
                      to="/settings"
                      className="underline hover:no-underline mt-1 inline-block"
                      onClick={() => onClose()}
                    >
                      Configure AI settings →
                    </Link>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Right Panel: Results */}
          <div className="border-l lg:border-l pl-6 space-y-4 overflow-y-auto">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">Results</h3>
              {testResult && (
                <div className="flex items-center gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={handleCopyResult}
                  >
                    <Copy className="h-4 w-4 mr-2" />
                    Copy
                  </Button>
                </div>
              )}
            </div>

            {/* Test Status */}
            {testResult && !testResult.error && (
              <div className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 dark:bg-green-900/20 dark:border-green-800 dark:text-green-300">
                <CheckCircle2 className="h-4 w-4 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium">
                    Test completed successfully
                  </p>
                  <div className="flex flex-wrap items-center gap-4 mt-1 text-xs">
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {testResult.execution_time_ms.toFixed(0)}ms
                    </span>
                    {testResult.model_used && (
                      <span className="flex items-center gap-1">
                        <Bot className="h-3 w-3" />
                        {testResult.model_used}
                      </span>
                    )}
                    {testResult.tokens_used && (
                      <span className="flex items-center gap-1">
                        <Zap className="h-3 w-3" />
                        {testResult.tokens_used.total} tokens
                      </span>
                    )}
                    {testResult.estimated_cost !== undefined && (
                      <span className="flex items-center gap-1">
                        <DollarSign className="h-3 w-3" />$
                        {testResult.estimated_cost.toFixed(4)}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            )}

            {(testError || testResult?.error) && (
              <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 dark:bg-red-900/20 dark:border-red-800 dark:text-red-300">
                <AlertCircle className="h-4 w-4 flex-shrink-0" />
                <div className="flex-1">
                  <p className="text-sm font-medium">Test failed</p>
                  <p className="text-xs mt-1">
                    {testError || testResult?.error}
                  </p>
                </div>
              </div>
            )}

            {/* Result Content */}
            {testResult ? (
              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-medium mb-2">Generated Result</h4>
                  <div className="p-4 bg-background border rounded-lg min-h-32 max-h-96 overflow-y-auto">
                    <pre className="whitespace-pre-wrap text-sm">
                      {testResult.result}
                    </pre>
                  </div>
                </div>

                {/* Token Usage Details */}
                {testResult.tokens_used && (
                  <div>
                    <h4 className="text-sm font-medium mb-2">Token Usage</h4>
                    <div className="grid grid-cols-3 gap-2">
                      <div className="p-2 bg-accent/50 rounded text-center">
                        <div className="text-xs text-muted-foreground">
                          Prompt
                        </div>
                        <div className="font-medium">
                          {testResult.tokens_used.prompt}
                        </div>
                      </div>
                      <div className="p-2 bg-accent/50 rounded text-center">
                        <div className="text-xs text-muted-foreground">
                          Completion
                        </div>
                        <div className="font-medium">
                          {testResult.tokens_used.completion}
                        </div>
                      </div>
                      <div className="p-2 bg-accent/50 rounded text-center">
                        <div className="text-xs text-muted-foreground">
                          Total
                        </div>
                        <div className="font-medium">
                          {testResult.tokens_used.total}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Variables Used */}
                {Object.keys(testResult.variables_used).length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium mb-2">Variables Used</h4>
                    <div className="space-y-2">
                      {Object.entries(testResult.variables_used).map(
                        ([variable, value]) => (
                          <div
                            key={variable}
                            className="p-2 bg-accent/50 rounded text-sm"
                          >
                            <div className="font-mono text-blue-600 mb-1">{`{{${variable}}}`}</div>
                            <div className="text-muted-foreground">
                              {value.length > 100
                                ? `${value.substring(0, 100)}...`
                                : value}
                            </div>
                          </div>
                        )
                      )}
                    </div>
                  </div>
                )}
              </div>
            ) : !testError ? (
              <div className="flex flex-col items-center justify-center py-12 text-center text-muted-foreground">
                <Play className="h-12 w-12 mb-4 opacity-50" />
                <p>Run a test to see results here</p>
                <p className="text-sm mt-1">
                  {variables.length > 0
                    ? 'Fill in the variables and click "Test Prompt"'
                    : 'Click "Test Prompt" to execute'}
                </p>
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}
