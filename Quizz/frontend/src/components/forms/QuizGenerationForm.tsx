import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import api from '../../services/api';

const quizGenerationSchema = z.object({
  docId: z.string().uuid(),
  query: z.string().min(1, 'Query is required'),
  numQuestions: z.number().min(1).max(20),
  difficulty: z.number().min(1).max(5),
});

type QuizGenerationFormInputs = z.infer<typeof quizGenerationSchema>;

interface QuizGenerationFormProps {
  documents: { id: string; filename: string }[];
  onQuizGenerated: (quiz: any) => void;
}

const QuizGenerationForm: React.FC<QuizGenerationFormProps> = ({ documents, onQuizGenerated }) => {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<QuizGenerationFormInputs>({
    resolver: zodResolver(quizGenerationSchema),
  });

  const onSubmit = async (data: QuizGenerationFormInputs) => {
    try {
      const response = await api.post('/quizzes/generate', data);
      onQuizGenerated(response.data.quiz);
    } catch (error) {
      console.error('Error generating quiz:', error);
      // Handle error
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <label htmlFor="docId" className="block text-sm font-medium text-gray-700">
          Select Document
        </label>
        <select
          id="docId"
          {...register('docId')}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
        >
          {documents.map(doc => (
            <option key={doc.id} value={doc.id}>
              {doc.filename}
            </option>
          ))}
        </select>
        {errors.docId && <p className="mt-2 text-sm text-red-600">{errors.docId.message}</p>}
      </div>

      <div>
        <label htmlFor="query" className="block text-sm font-medium text-gray-700">
          Topic/Query
        </label>
        <input
          type="text"
          id="query"
          {...register('query')}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
        />
        {errors.query && <p className="mt-2 text-sm text-red-600">{errors.query.message}</p>}
      </div>

      <div>
        <label htmlFor="numQuestions" className="block text-sm font-medium text-gray-700">
          Number of Questions
        </label>
        <input
          type="number"
          id="numQuestions"
          {...register('numQuestions', { valueAsNumber: true })}
          defaultValue={10}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
        />
        {errors.numQuestions && <p className="mt-2 text-sm text-red-600">{errors.numQuestions.message}</p>}
      </div>

      <div>
        <label htmlFor="difficulty" className="block text-sm font-medium text-gray-700">
          Difficulty (1-5)
        </label>
        <input
          type="number"
          id="difficulty"
          {...register('difficulty', { valueAsNumber: true })}
          defaultValue={2}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
        />
        {errors.difficulty && <p className="mt-2 text-sm text-red-600">{errors.difficulty.message}</p>}
      </div>

      <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
        Generate Quiz
      </button>
    </form>
  );
};

export default QuizGenerationForm; 