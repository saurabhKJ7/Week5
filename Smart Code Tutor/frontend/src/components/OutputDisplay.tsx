import React from 'react';

interface OutputDisplayProps {
  output: string[];
  explanation: string;
  isLoading: boolean;
  error?: string;
}

const OutputDisplay: React.FC<OutputDisplayProps> = ({
  output,
  explanation,
  isLoading,
  error,
}) => {
  return (
    <div className="mt-4 space-y-4">
      {/* Code Output */}
      <div className="bg-gray-900 rounded-lg p-4">
        <h3 className="text-white text-sm font-medium mb-2">Output</h3>
        {isLoading ? (
          <div className="animate-pulse flex space-x-4">
            <div className="flex-1 space-y-2">
              <div className="h-4 bg-gray-700 rounded"></div>
              <div className="h-4 bg-gray-700 rounded w-5/6"></div>
            </div>
          </div>
        ) : error ? (
          <pre className="text-red-400 font-mono text-sm whitespace-pre-wrap">
            {error}
          </pre>
        ) : (
          <pre className="text-green-400 font-mono text-sm whitespace-pre-wrap">
            {output.join('\n')}
          </pre>
        )}
      </div>

      {/* AI Explanation */}
      {explanation && (
        <div className="bg-blue-50 rounded-lg p-4">
          <h3 className="text-blue-900 text-sm font-medium mb-2">
            AI Explanation
          </h3>
          <div className="prose prose-sm max-w-none text-blue-900">
            {explanation}
          </div>
        </div>
      )}
    </div>
  );
};

export default OutputDisplay; 