import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { FiFileText, FiChevronLeft, FiPlus, FiSend, FiLayout, FiBookOpen, FiShare2, FiHelpCircle } from 'react-icons/fi';
import GraphVisualization from './components/GraphVisualization';
import QueryResult from './components/QueryResult';
import DecomposedQueryResult from './components/DecomposedQueryResult';
import './App.css';

function App() {
  const [sources, setSources] = useState([]);
  const [chatHistory, setChatHistory] = useState([]);
  const [query, setQuery] = useState('');
  const [useDecomposition, setUseDecomposition] = useState(false);
  const [isSourcesOpen, setIsSourcesOpen] = useState(true);
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory]);

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setLoading(true);
    setError(null);
    const formData = new FormData();
    formData.append('file', file);

    try {
      await axios.post('http://localhost:8000/upload/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setSources(prev => [...prev, file.name]);
    } catch (err) {
      setError('File upload failed.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleQuery = async () => {
    if (!query.trim()) return;

    const userMessage = { type: 'user', content: query };
    setChatHistory(prev => [...prev, userMessage]);
    setQuery('');
    setLoading(true);
    setError(null);

    try {
      if (query.toLowerCase() === 'summarize') {
        const res = await axios.post('http://localhost:8000/summarize/');
        const botMessage = { type: 'summary', data: res.data.summary };
        setChatHistory(prev => [...prev, botMessage]);
      } else if (query.toLowerCase() === 'map relationships') {
        const res = await axios.post('http://localhost:8000/map_relationships/');
        const botMessage = { type: 'graph', data: res.data };
        setChatHistory(prev => [...prev, botMessage]);
      } else {
        const endpoint = useDecomposition ? '/decomposed_query/' : '/query/';
        const res = await axios.post(`http://localhost:8000${endpoint}`, { query });
        const messageType = useDecomposition ? 'decomposed_query_result' : 'query_result';
        const botMessage = { type: messageType, data: res.data };
        setChatHistory(prev => [...prev, botMessage]);
      }
    } catch (err) {
      setError('An error occurred.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };
  
  const renderMessageContent = (msg) => {
    switch (msg.type) {
        case 'user':
            return <p><FiHelpCircle style={{marginRight: '8px'}} /><strong>You:</strong> {msg.content}</p>;
        case 'summary':
            return <div><h3>📝 Summary</h3><p>{msg.data}</p></div>;
        case 'graph':
            return <div><h3><FiShare2 style={{marginRight: '8px'}}/>Relationship Graph</h3><GraphVisualization graphData={msg.data} /></div>;
        case 'query_result':
            return <QueryResult data={msg.data} />;
        case 'decomposed_query_result':
            return <DecomposedQueryResult data={msg.data} />;
        default:
            return <pre>{JSON.stringify(msg.data, null, 2)}</pre>;
    }
  };

  return (
    <div className="notebook-container">
      <div className={`panel left-panel ${isSourcesOpen ? '' : 'closed'}`}>
        <div className="panel-header">
            <div className="panel-header-title">
                <FiBookOpen style={{marginRight: '8px'}}/>
                <h2>Sources</h2>
            </div>
            <button className="toggle-btn" onClick={() => setIsSourcesOpen(!isSourcesOpen)}>
                <FiChevronLeft />
            </button>
        </div>
        <input type="file" onChange={handleFileChange} disabled={loading} id="file-upload" style={{display: 'none'}} />
        <button className="add-source-btn" onClick={() => document.getElementById('file-upload').click()} disabled={loading}>
            <FiPlus style={{marginRight: '8px'}}/> Add Source
        </button>
        {sources.map((source, index) => (
          <div key={index} className="source-item">
            <FiFileText style={{marginRight: '8px'}}/>
            <p>{source}</p>
          </div>
        ))}
      </div>
      <div className="panel center-panel">
        <h1 className="main-title">NotebookLM</h1>
        <div className="chat-content">
          {chatHistory.map((msg, index) => (
            <div key={index} className={`chat-message result-card`}>
                {renderMessageContent(msg)}
            </div>
          ))}
          {loading && <div className="loader" />}
          {error && <div className="error-message">{error}</div>}
          <div ref={chatEndRef} />
        </div>
        <div className="chat-input-area">
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a question, or type 'summarize' or 'map relationships'..."
            rows="3"
            onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleQuery()}
          />
          <div className="chat-options">
            <div>
              <input 
                type="checkbox" 
                id="decompose" 
                checked={useDecomposition} 
                onChange={(e) => setUseDecomposition(e.target.checked)}
              />
              <label htmlFor="decompose">Use Query Decomposition</label>
            </div>
            <button onClick={handleQuery} disabled={loading || !query.trim()}>
              {loading ? <span className="loader" /> : <FiSend />}
            </button>
          </div>
        </div>
      </div>
      <div className="panel right-panel">
        <div className="panel-header">
            <FiLayout style={{marginRight: '8px'}}/>
            <h2>Studio</h2>
        </div>
        <div className="studio-card">
            <h4>Generate Content</h4>
            <p>Type 'summarize' or 'map relationships' in the chat to generate content here.</p>
        </div>
      </div>
    </div>
  );
}

export default App; 