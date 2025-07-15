import React, { useState, useEffect } from 'react';
import DocumentUpload from '../../components/forms/DocumentUpload';
import api from '../../services/api';

interface Document {
  id: string;
  filename: string;
  content_type: string;
  processed: boolean;
}

const DocumentsPage: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [message, setMessage] = useState('');

  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        const response = await api.get('/documents');
        setDocuments(response.data);
      } catch (error) {
        console.error('Error fetching documents:', error);
      }
    };
    fetchDocuments();
  }, []);

  const handleUploadSuccess = (data: any) => {
    setDocuments(prev => [...prev, data]);
    setMessage(`Document '${data.filename}' uploaded successfully!`);
    // Clear message after 3 seconds
    setTimeout(() => setMessage(''), 3000);
  };

  const handleProcessDocument = async (docId: string) => {
    try {
      const response = await api.post(`/documents/${docId}/process`);
      setMessage(response.data.message);
      // Update the document status to processed
      setDocuments(prev => 
        prev.map(doc => doc.id === docId ? { ...doc, processed: true } : doc)
      );
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      console.error('Error processing document:', error);
      setMessage('Error processing document.');
      setTimeout(() => setMessage(''), 3000);
    }
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Manage Documents</h1>
      
      {message && <div className="p-4 mb-4 text-sm text-green-700 bg-green-100 rounded-lg">{message}</div>}

      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-2">Upload New Document</h2>
        <DocumentUpload onUploadSuccess={handleUploadSuccess} />
      </div>

      <div>
        <h2 className="text-xl font-semibold mb-2">Uploaded Documents</h2>
        <ul className="space-y-2">
          {documents.map(doc => (
            <li key={doc.id} className="p-4 border rounded-lg flex justify-between items-center">
              <div>
                <p className="font-semibold">{doc.filename}</p>
                <p className="text-sm text-gray-500">{doc.content_type}</p>
              </div>
              <div>
                {doc.processed ? (
                  <span className="text-green-500">Processed</span>
                ) : (
                  <button
                    onClick={() => handleProcessDocument(doc.id)}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    Process
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default DocumentsPage; 