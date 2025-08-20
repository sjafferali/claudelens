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
} from 'lucide-react';
import { Button } from '@/components/common';
import { Prompt, PromptTestResponse } from '@/api/types';
import { useTestPrompt } from '@/hooks/usePrompts';
import { substituteVariables, extractVariables } from '@/api/prompts';
import { VariableChips } from './VariableChips';
import { toast } from 'react-hot-toast';

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

  const testPrompt = useTestPrompt();
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
      });
      setTestResult(result);
    } catch (error) {
      console.error('Test failed:', error);
      const errorMessage =
        (error as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || 'Failed to test prompt';
      setTestError(errorMessage);
      setTestResult(null);
    }
  };

  const handleReset = () => {
    const resetInputs: VariableInputs = {};
    variables.forEach((variable) => {
      resetInputs[variable] = '';
    });
    setVariableInputs(resetInputs);
    setTestResult(null);
    setTestError(null);
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
              <h3 className="text-lg font-semibold mb-4">Variables</h3>
              {variables.length > 0 ? (
                <div className="space-y-4">
                  <VariableChips variables={variables} />
                  {variables.map((variable) => (
                    <div key={variable} className="space-y-2">
                      <label
                        htmlFor={`var-${variable}`}
                        className="text-sm font-medium flex items-center gap-2"
                      >
                        <span className="font-mono text-blue-600">{`{{${variable}}}`}</span>
                      </label>
                      <textarea
                        id={`var-${variable}`}
                        value={variableInputs[variable] || ''}
                        onChange={(e) =>
                          handleVariableChange(variable, e.target.value)
                        }
                        placeholder={`Enter value for ${variable}`}
                        rows={3}
                        className="w-full px-3 py-2 border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent resize-none text-sm"
                      />
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-muted-foreground text-sm">
                  This prompt doesn't have any variables.
                </p>
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

            {/* Test Button */}
            <Button
              onClick={handleTest}
              disabled={!canTest || isLoading}
              className="w-full"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Testing...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" />
                  Test Prompt
                </>
              )}
            </Button>
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
            {testResult && (
              <div className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 dark:bg-green-900/20 dark:border-green-800 dark:text-green-300">
                <CheckCircle2 className="h-4 w-4 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium">
                    Test completed successfully
                  </p>
                  <div className="flex items-center gap-4 mt-1 text-xs">
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {testResult.execution_time_ms}ms
                    </span>
                    <span>
                      {Object.keys(testResult.variables_used).length} variables
                      used
                    </span>
                  </div>
                </div>
              </div>
            )}

            {testError && (
              <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 dark:bg-red-900/20 dark:border-red-800 dark:text-red-300">
                <AlertCircle className="h-4 w-4 flex-shrink-0" />
                <div className="flex-1">
                  <p className="text-sm font-medium">Test failed</p>
                  <p className="text-xs mt-1">{testError}</p>
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
