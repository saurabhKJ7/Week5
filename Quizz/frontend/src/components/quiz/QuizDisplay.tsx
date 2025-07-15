import React, { useState } from 'react';

interface Question {
  id: string;
  question: string;
  options: string[];
  correctAnswer: string;
}

interface QuizDisplayProps {
  quiz: Question[];
}

const QuizDisplay: React.FC<QuizDisplayProps> = ({ quiz }) => {
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [submitted, setSubmitted] = useState(false);

  const handleAnswerChange = (questionId: string, answer: string) => {
    setAnswers(prev => ({ ...prev, [questionId]: answer }));
  };

  const handleSubmit = () => {
    setSubmitted(true);
  };

  const calculateScore = () => {
    let score = 0;
    quiz.forEach(q => {
      if (answers[q.id] === q.correctAnswer) {
        score++;
      }
    });
    return score;
  };

  return (
    <div>
      {quiz.map(q => (
        <div key={q.id} className="mb-6">
          <p className="font-semibold">{q.question}</p>
          <div className="space-y-2 mt-2">
            {q.options.map(option => (
              <label key={option} className="flex items-center">
                <input
                  type="radio"
                  name={q.id}
                  value={option}
                  onChange={() => handleAnswerChange(q.id, option)}
                  disabled={submitted}
                  className="mr-2"
                />
                <span
                  className={
                    submitted && option === q.correctAnswer
                      ? 'text-green-600'
                      : submitted && answers[q.id] === option && option !== q.correctAnswer
                      ? 'text-red-600'
                      : ''
                  }
                >
                  {option}
                </span>
              </label>
            ))}
          </div>
        </div>
      ))}
      
      {!submitted && (
        <button
          onClick={handleSubmit}
          className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
        >
          Submit Quiz
        </button>
      )}

      {submitted && (
        <div className="mt-6">
          <h3 className="text-lg font-bold">Your Score: {calculateScore()} / {quiz.length}</h3>
        </div>
      )}
    </div>
  );
};

export default QuizDisplay; 