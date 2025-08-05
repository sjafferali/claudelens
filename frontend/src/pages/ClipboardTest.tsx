import { useState } from 'react';
import { copyToClipboard } from '@/utils/clipboard';
import { Copy, Check } from 'lucide-react';

export default function ClipboardTest() {
  const [copied, setCopied] = useState(false);
  const [testText] = useState(
    'This is a test text for clipboard functionality!'
  );
  const [error, setError] = useState<string | null>(null);

  const handleCopy = async () => {
    setError(null);
    const success = await copyToClipboard(testText);
    if (success) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } else {
      setError(
        'Failed to copy to clipboard. Make sure you are using HTTPS or localhost.'
      );
    }
  };

  return (
    <div className="flex flex-col h-screen bg-layer-primary">
      <div className="bg-layer-secondary border-b border-primary-c px-6 py-4">
        <h2 className="text-2xl font-semibold text-primary-c">
          Clipboard Test
        </h2>
        <p className="text-tertiary-c mt-1">Test clipboard functionality</p>
      </div>

      <div className="flex-1 p-6">
        <div className="max-w-2xl mx-auto space-y-6">
          <div className="bg-layer-secondary border border-primary-c rounded-lg p-6">
            <h3 className="text-lg font-medium text-primary-c mb-4">
              Test Clipboard Copy
            </h3>

            <div className="space-y-4">
              <div>
                <p className="text-sm text-muted-c mb-2">Text to copy:</p>
                <div className="bg-layer-tertiary p-3 rounded border border-secondary-c">
                  <code className="text-secondary-c">{testText}</code>
                </div>
              </div>

              <button
                onClick={handleCopy}
                className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-hover transition-colors"
              >
                {copied ? (
                  <>
                    <Check className="h-4 w-4" />
                    Copied!
                  </>
                ) : (
                  <>
                    <Copy className="h-4 w-4" />
                    Copy to Clipboard
                  </>
                )}
              </button>

              {error && (
                <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                  <p className="text-sm text-red-600 dark:text-red-400">
                    {error}
                  </p>
                </div>
              )}

              <div className="space-y-2 text-sm text-muted-c">
                <p>Clipboard API Status:</p>
                <ul className="list-disc list-inside space-y-1 ml-4">
                  <li>
                    navigator.clipboard:{' '}
                    {navigator.clipboard ? '✅ Available' : '❌ Not available'}
                  </li>
                  <li>
                    Secure Context:{' '}
                    {window.isSecureContext ? '✅ Yes' : '❌ No'}
                  </li>
                  <li>Protocol: {window.location.protocol}</li>
                  <li>Hostname: {window.location.hostname}</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
