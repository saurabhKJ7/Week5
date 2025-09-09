import React, { useState } from 'react';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8001';

function Chat() {
  const [question, setQuestion] = useState('');
  const [response, setResponse] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;

    setIsLoading(true);
    setError('');
    setResponse(null);

    try {
      const { data } = await axios.post(`${API_BASE_URL}/query`, {
        question: question.trim(),
      });
      setResponse(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to get response');
    } finally {
      setIsLoading(false);
    }
  };

  const renderMetricsBadge = (metric, value) => {
    const color = value >= 0.9 ? 'green' : value >= 0.85 ? 'yellow' : 'red';
    return (
      <span
        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
          color === 'green'
            ? 'bg-green-100 text-green-800'
            : color === 'yellow'
            ? 'bg-yellow-100 text-yellow-800'
            : 'bg-red-100 text-red-800'
        }`}
      >
        {metric}: {value.toFixed(2)}
      </span>
    );
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white shadow sm:rounded-lg p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Ask Medical Questions</h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="question" className="sr-only">
              Question
            </label>
            <textarea
              id="question"
              name="question"
              rows={4}
              className="shadow-sm block w-full focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm border border-gray-300 rounded-md"
              placeholder="Enter your medical question here..."
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
            />
          </div>
          <button
            type="submit"
            disabled={isLoading}
            className={`inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 ${
              isLoading ? 'opacity-50 cursor-not-allowed' : ''
            }`}
          >
            {isLoading ? 'Processing...' : 'Ask Question'}
          </button>
        </form>

        {error && (
          <div className="mt-4 bg-red-50 text-red-700 p-4 rounded-md">
            {error}
          </div>
        )}

        {response && (
          <div className="mt-6 space-y-4">
            <div className={`p-4 rounded-md ${response.blocked ? 'bg-red-50 border border-red-200' : 'bg-gray-50'}`}>
              <div className="flex justify-between items-start">
                <h3 className="text-md font-medium text-gray-900">Answer</h3>
                <div className="flex space-x-2">
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      response.blocked
                        ? 'bg-red-100 text-red-800'
                        : 'bg-green-100 text-green-800'
                    }`}
                  >
                    {response.blocked ? 'BLOCKED' : 'SAFE'}
                  </span>
                  {response.safety_result && (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      Confidence: {(response.safety_result.confidence_score * 100).toFixed(0)}%
                    </span>
                  )}
                </div>
              </div>
              <p className="mt-2 text-sm text-gray-500">{response.answer}</p>
              
              {response.blocked && response.violations && (
                <div className="mt-3 p-3 bg-red-100 border border-red-200 rounded">
                  <h4 className="text-sm font-medium text-red-800 mb-2">Safety Violations:</h4>
                  <ul className="text-sm text-red-700 list-disc list-inside">
                    {response.violations.map((violation, index) => (
                      <li key={index}>{violation}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {response.safety_result && response.safety_result.metrics && (
              <div className="bg-gray-50 p-4 rounded-md">
                <h3 className="text-md font-medium text-gray-900 mb-2">Safety Metrics</h3>
                <div className="space-x-2">
                  {Object.entries(response.safety_result.metrics).map(([key, value]) => (
                    <React.Fragment key={key}>
                      {renderMetricsBadge(key, value)}
                    </React.Fragment>
                  ))}
                </div>
              </div>
            )}

            {response.context && (
              <div className="bg-gray-50 p-4 rounded-md">
                <h3 className="text-md font-medium text-gray-900 mb-2">Context Used</h3>
                <p className="text-sm text-gray-500 max-h-40 overflow-y-auto">{response.context}</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default Chat; 