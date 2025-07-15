import React, { useState, useEffect } from 'react';
import QuizGenerationForm from '../../components/forms/QuizGenerationForm';
import QuizDisplay from '../../components/quiz/QuizDisplay';
import api from '../../services/api';

interface Document {
  id: string;
  filename: string;
}

const QuizGenerationPage: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [quiz, setQuiz] = useState<any[] | null>(null);

  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        const response = await api.get('/documents?processed=true');
        setDocuments(response.data);
      } catch (error) {
        console.error('Error fetching documents:', error);
      }
    };
    fetchDocuments();
  }, []);

  const handleQuizGenerated = (generatedQuiz: any) => {
    setQuiz(generatedQuiz);
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Generate Quiz</h1>
      
      <div className="mb-8">
        <QuizGenerationForm documents={documents} onQuizGenerated={handleQuizGenerated} />
      </div>

      {quiz && (
        <div>
          <h2 className="text-xl font-semibold mb-2">Generated Quiz</h2>
          <QuizDisplay quiz={quiz} />
        </div>
      )}
    </div>
  );
};

export default QuizGenerationPage; 