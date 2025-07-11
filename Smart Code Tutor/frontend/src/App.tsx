import { useState, useCallback } from 'react';
import CodeEditor from './components/CodeEditor';
import OutputDisplay from './components/OutputDisplay';
import useWebSocket from './hooks/useWebSocket';

// Get the current frontend port from the window location
const currentPort = window.location.port;
// Use the current port to determine which backend port to connect to
const WEBSOCKET_URL = `http://localhost:8000`;

function App() {
  const [language, setLanguage] = useState<'python' | 'javascript'>('python');
  const [code, setCode] = useState('');
  const [output, setOutput] = useState<string[]>([]);
  const [explanation, setExplanation] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | undefined>();

  const handleOutput = useCallback((data: string) => {
    setOutput(prev => [...prev, data]);
    setIsLoading(false);
  }, []);

  const handleError = useCallback((error: string) => {
    setError(error);
    setIsLoading(false);
  }, []);

  const handleExplanation = useCallback((explanation: string) => {
    setExplanation(explanation);
  }, []);

  const { executeCode, requestExplanation, isConnected } = useWebSocket({
    url: WEBSOCKET_URL,
    onOutput: handleOutput,
    onError: handleError,
    onExplanation: handleExplanation,
  });

  const handleRunCode = useCallback(() => {
    if (!isConnected) {
      setError('Not connected to server. Please wait for connection...');
      return;
    }
    setIsLoading(true);
    setOutput([]);
    setError(undefined);
    setExplanation('');
    executeCode(code, language);
  }, [code, language, executeCode, isConnected]);

  const handleExplain = useCallback(() => {
    if (!isConnected) {
      setError('Not connected to server. Please wait for connection...');
      return;
    }
    if (!output.length) {
      setError('No output to explain. Run some code first.');
      return;
    }
    requestExplanation(code, output.join('\n'));
  }, [code, output, requestExplanation, isConnected]);

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Smart Code Tutor</h1>
          <p className="mt-2 text-gray-600">
            Write, run, and learn from your code with AI-powered explanations
          </p>
        </header>

        <main className="space-y-6">
          {/* Language Selection */}
          <div className="flex items-center space-x-4">
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value as 'python' | 'javascript')}
              className="block rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            >
              <option value="python">Python</option>
              <option value="javascript">JavaScript</option>
            </select>

            <div className="flex-1" />

            <div className="space-x-4">
              <button
                onClick={handleRunCode}
                disabled={!isConnected || isLoading}
                className={`btn ${isConnected ? 'btn-primary' : 'btn-disabled'}`}
              >
                {isLoading ? 'Running...' : 'Run Code'}
              </button>
              <button
                onClick={handleExplain}
                disabled={!output.length || !isConnected || isLoading}
                className={`btn ${isConnected && output.length ? 'btn-secondary' : 'btn-disabled'}`}
              >
                Explain Code
              </button>
            </div>
          </div>

          {/* Editor */}
          <CodeEditor
            language={language}
            code={code}
            onChange={setCode}
          />

          {/* Output */}
          <OutputDisplay
            output={output}
            explanation={explanation}
            isLoading={isLoading}
            error={error}
          />
        </main>

        {/* Connection Status */}
        <footer className="mt-8 text-center text-sm">
          {isConnected ? (
            <span className="text-green-500 font-medium">Connected to server</span>
          ) : (
            <span className="text-red-500 font-medium">
              Disconnected from server
              {error && ` - ${error}`}
            </span>
          )}
        </footer>
      </div>
    </div>
  );
}

export default App;
