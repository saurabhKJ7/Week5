import json
import pandas as pd
from typing import List, Dict
from ragas.metrics import (
    faithfulness,
    context_precision,
    context_recall,
    answer_relevancy,
)
import asyncio
from main import query_documents, Query

class EvaluationResult:
    def __init__(self, question: str, answer: str, metrics: Dict[str, float], passed: bool):
        self.question = question
        self.answer = answer
        self.metrics = metrics
        self.passed = passed

    def to_dict(self):
        return {
            "question": self.question,
            "answer": self.answer,
            "metrics": self.metrics,
            "passed": self.passed
        }

async def evaluate_question(question: str) -> EvaluationResult:
    """Evaluate a single question using the RAG pipeline."""
    query = Query(question=question)
    response = await query_documents(query)
    
    passed = (
        response.metrics["faithfulness"] >= 0.90 and
        response.metrics["context_precision"] >= 0.85
    )
    
    return EvaluationResult(
        question=question,
        answer=response.answer,
        metrics=response.metrics,
        passed=passed
    )

async def batch_evaluate(questions: List[str]) -> List[EvaluationResult]:
    """Run batch evaluation on a list of questions."""
    tasks = [evaluate_question(q) for q in questions]
    results = await asyncio.gather(*tasks)
    return results

def load_test_questions(file_path: str) -> List[str]:
    """Load test questions from a JSON or CSV file."""
    if file_path.endswith('.json'):
        with open(file_path, 'r') as f:
            data = json.load(f)
            return data['questions']
    elif file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
        return df['question'].tolist()
    else:
        raise ValueError("Unsupported file format. Use JSON or CSV.")

def save_results(results: List[EvaluationResult], output_path: str):
    """Save evaluation results to a JSON file."""
    output = {
        "results": [r.to_dict() for r in results],
        "summary": {
            "total_questions": len(results),
            "passed": sum(1 for r in results if r.passed),
            "average_metrics": {
                metric: sum(r.metrics[metric] for r in results) / len(results)
                for metric in results[0].metrics.keys()
            }
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

async def main(test_file: str, output_file: str = "evaluation_results.json"):
    """Run the complete evaluation pipeline."""
    print("Loading test questions...")
    questions = load_test_questions(test_file)
    
    print(f"Running evaluation on {len(questions)} questions...")
    results = await batch_evaluate(questions)
    
    print("Saving results...")
    save_results(results, output_file)
    
    # Print summary
    passed = sum(1 for r in results if r.passed)
    print(f"\nEvaluation Summary:")
    print(f"Total Questions: {len(results)}")
    print(f"Passed: {passed} ({passed/len(results)*100:.1f}%)")
    print("\nAverage Metrics:")
    for metric in results[0].metrics.keys():
        avg = sum(r.metrics[metric] for r in results) / len(results)
        print(f"{metric}: {avg:.3f}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python eval.py <test_file> [output_file]")
        sys.exit(1)
    
    test_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "evaluation_results.json"
    
    asyncio.run(main(test_file, output_file)) 