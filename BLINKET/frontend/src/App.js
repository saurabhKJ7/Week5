import React, { useState } from 'react';

const API_URL = "http://localhost:8000";

function App() {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);
  const [healthStatus, setHealthStatus] = useState('');

  const handleQuery = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResponse('');
    setHealthStatus('');
    const res = await fetch(`${API_URL}/api/v1/query/nl-query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query }),
    });
    if (!res.ok) {
      setResponse(`Error: ${res.statusText}`);
    } else {
      const data = await res.json();
      setResponse(data.response);
    }
    setLoading(false);
  };

  const handleHealthCheck = async () => {
    setLoading(true);
    setResponse('');
    setHealthStatus('');
    const res = await fetch(`${API_URL}/api/v1/query/nl-query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: 'health-check' }),
    });
    if (res.ok) {
      const data = await res.json();
      setHealthStatus(`Health Check OK: ${data.response}`);
    } else {
      setHealthStatus(`Health Check Failed: ${res.statusText}`);
    }
    setLoading(false);
  };

  return (
    <div className="bg-gray-900 min-h-screen text-white p-8">
      <div className="container mx-auto">
        <h1 className="text-4xl font-bold mb-8 text-center">Quick Commerce Price Comparison</h1>
        
        <div className="flex justify-center mb-4">
          <button
            onClick={handleHealthCheck}
            className="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-lg transition duration-300"
            disabled={loading}
          >
            Test Backend Connection
          </button>
        </div>
        {healthStatus && <p className="text-center text-lg mb-4">{healthStatus}</p>}

        <form onSubmit={handleQuery} className="mb-8">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a question, e.g., 'Which app has the cheapest onions right now?'"
            className="w-full p-4 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            className="mt-4 w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-lg transition duration-300"
            disabled={loading}
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </form>

        {response && (
          <div className="bg-gray-800 p-6 rounded-lg">
            <h2 className="text-2xl font-bold mb-4">Response</h2>
            <p className="text-gray-300">{response}</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
