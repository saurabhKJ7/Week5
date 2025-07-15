import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import DocumentsPage from './pages/Documents/DocumentsPage';
import QuizGenerationPage from './pages/QuizGeneration/QuizGenerationPage';

function App() {
  return (
    <Router>
      <div>
        <nav className="bg-gray-800 p-4 text-white">
          <ul className="flex space-x-4">
            <li>
              <Link to="/">Documents</Link>
            </li>
            <li>
              <Link to="/generate-quiz">Generate Quiz</Link>
            </li>
          </ul>
        </nav>

        <main>
          <Routes>
            <Route path="/" element={<DocumentsPage />} />
            <Route path="/generate-quiz" element={<QuizGenerationPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
