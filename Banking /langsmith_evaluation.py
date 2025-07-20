#!/usr/bin/env python3
"""
LangSmith Evaluation Framework for Banking RAG System
Comprehensive testing and evaluation suite
"""

import os
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any
import requests
from langsmith import Client
from langsmith.evaluation import evaluate, LangChainStringEvaluator
from langsmith.schemas import Example, Run

# Initialize LangSmith client
try:
    langsmith_client = Client()
    print("✅ LangSmith client initialized")
except Exception as e:
    print(f"❌ Failed to initialize LangSmith client: {e}")
    langsmith_client = None

class BankingRAGEvaluator:
    """Comprehensive evaluation framework for Banking RAG system"""
    
    def __init__(self, api_base_url: str = "http://localhost:8001"):
        self.api_base_url = api_base_url
        self.evaluation_datasets = {
            "banking_qa": self.create_banking_qa_dataset(),
            "compliance": self.create_compliance_dataset(),
            "rates_pricing": self.create_rates_pricing_dataset(),
            "loan_products": self.create_loan_products_dataset()
        }
    
    def create_banking_qa_dataset(self) -> List[Dict]:
        """Create general banking Q&A evaluation dataset"""
        return [
            {
                "question": "What are the current mortgage interest rates?",
                "expected_topics": ["rates", "mortgage", "interest", "pricing"],
                "evaluation_criteria": ["accuracy", "completeness", "source_citation"]
            },
            {
                "question": "Explain the loan underwriting process step by step",
                "expected_topics": ["underwriting", "process", "requirements", "steps"],
                "evaluation_criteria": ["clarity", "completeness", "practical_value"]
            },
            {
                "question": "What documentation is required for a business loan application?",
                "expected_topics": ["documentation", "business loan", "requirements", "application"],
                "evaluation_criteria": ["accuracy", "completeness", "practical_value"]
            },
            {
                "question": "What are the risk management policies for lending?",
                "expected_topics": ["risk management", "policies", "lending", "mitigation"],
                "evaluation_criteria": ["accuracy", "completeness", "regulatory_compliance"]
            }
        ]
    
    def create_compliance_dataset(self) -> List[Dict]:
        """Create compliance-specific evaluation dataset"""
        return [
            {
                "question": "What are the KYC requirements for new customers?",
                "expected_topics": ["KYC", "customer", "verification", "requirements"],
                "evaluation_criteria": ["regulatory_accuracy", "completeness", "clarity"]
            },
            {
                "question": "Explain the anti-money laundering procedures",
                "expected_topics": ["AML", "procedures", "compliance", "regulations"],
                "evaluation_criteria": ["regulatory_accuracy", "detail_level", "practical_steps"]
            },
            {
                "question": "What are the disclosure requirements for loan products?",
                "expected_topics": ["disclosure", "loan products", "requirements", "regulations"],
                "evaluation_criteria": ["legal_accuracy", "completeness", "clarity"]
            }
        ]
    
    def create_rates_pricing_dataset(self) -> List[Dict]:
        """Create rates and pricing evaluation dataset"""
        return [
            {
                "question": "What factors determine personal loan interest rates?",
                "expected_topics": ["factors", "personal loan", "interest rates", "determination"],
                "evaluation_criteria": ["accuracy", "comprehensiveness", "practical_value"]
            },
            {
                "question": "How do fixed vs variable mortgage rates compare?",
                "expected_topics": ["fixed rates", "variable rates", "mortgage", "comparison"],
                "evaluation_criteria": ["clarity", "accuracy", "comparison_quality"]
            },
            {
                "question": "What are the fees associated with commercial lending?",
                "expected_topics": ["fees", "commercial lending", "costs", "structure"],
                "evaluation_criteria": ["completeness", "accuracy", "transparency"]
            }
        ]
    
    def create_loan_products_dataset(self) -> List[Dict]:
        """Create loan products evaluation dataset"""
        return [
            {
                "question": "Compare different types of mortgage products available",
                "expected_topics": ["mortgage types", "products", "comparison", "features"],
                "evaluation_criteria": ["completeness", "clarity", "comparison_quality"]
            },
            {
                "question": "What are the eligibility criteria for small business loans?",
                "expected_topics": ["eligibility", "small business loans", "criteria", "requirements"],
                "evaluation_criteria": ["accuracy", "completeness", "practical_value"]
            },
            {
                "question": "Explain the differences between secured and unsecured loans",
                "expected_topics": ["secured loans", "unsecured loans", "differences", "features"],
                "evaluation_criteria": ["clarity", "accuracy", "educational_value"]
            }
        ]
    
    async def query_banking_rag(self, question: str) -> Dict[str, Any]:
        """Query the Banking RAG system"""
        try:
            payload = {
                "question": question,
                "use_conversation": False,
                "include_sources": True,
                "k": 5
            }
            
            response = requests.post(
                f"{self.api_base_url}/query",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "error": f"API error: {response.status_code}",
                    "response": "",
                    "sources": []
                }
                
        except Exception as e:
            return {
                "error": str(e),
                "response": "",
                "sources": []
            }
    
    def evaluate_response_quality(self, question: str, response: Dict, expected_data: Dict) -> Dict[str, float]:
        """Evaluate response quality based on multiple criteria"""
        scores = {}
        response_text = response.get("response", "").lower()
        
        # 1. Topic Coverage Score
        expected_topics = expected_data.get("expected_topics", [])
        topics_covered = sum(1 for topic in expected_topics if topic.lower() in response_text)
        scores["topic_coverage"] = topics_covered / len(expected_topics) if expected_topics else 0
        
        # 2. Source Citation Score
        sources = response.get("sources", [])
        scores["source_citation"] = min(len(sources) / 3, 1.0)  # Max score if 3+ sources
        
        # 3. Response Length Score (neither too short nor too long)
        response_length = len(response.get("response", ""))
        if 200 <= response_length <= 2000:
            scores["response_length"] = 1.0
        elif response_length < 200:
            scores["response_length"] = response_length / 200
        else:
            scores["response_length"] = max(0.5, 2000 / response_length)
        
        # 4. Banking Terminology Score
        banking_terms = [
            "loan", "mortgage", "interest", "rate", "credit", "bank", "financial",
            "compliance", "regulation", "policy", "risk", "underwriting", "documentation"
        ]
        terms_used = sum(1 for term in banking_terms if term in response_text)
        scores["banking_terminology"] = min(terms_used / 5, 1.0)
        
        # 5. Structure Score (markdown formatting)
        structure_indicators = ["##", "**", "•", "-", "*"]
        structure_score = sum(1 for indicator in structure_indicators if indicator in response.get("response", ""))
        scores["structure_quality"] = min(structure_score / 3, 1.0)
        
        return scores
    
    async def run_evaluation_suite(self, dataset_name: str = "all") -> Dict[str, Any]:
        """Run comprehensive evaluation suite"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "dataset_results": {},
            "overall_metrics": {}
        }
        
        datasets_to_test = (
            [dataset_name] if dataset_name != "all" 
            else list(self.evaluation_datasets.keys())
        )
        
        all_scores = []
        
        for dataset_key in datasets_to_test:
            dataset = self.evaluation_datasets[dataset_key]
            dataset_results = []
            
            print(f"\n📊 Evaluating dataset: {dataset_key}")
            print("=" * 50)
            
            for i, test_case in enumerate(dataset, 1):
                question = test_case["question"]
                print(f"Testing {i}/{len(dataset)}: {question[:50]}...")
                
                # Query the system
                response = await self.query_banking_rag(question)
                
                # Evaluate response
                scores = self.evaluate_response_quality(question, response, test_case)
                
                # Calculate overall score
                overall_score = sum(scores.values()) / len(scores)
                all_scores.append(overall_score)
                
                test_result = {
                    "question": question,
                    "response": response.get("response", "")[:200] + "...",  # Truncate for readability
                    "num_sources": len(response.get("sources", [])),
                    "scores": scores,
                    "overall_score": overall_score,
                    "has_error": "error" in response
                }
                
                dataset_results.append(test_result)
                
                # Show quick results
                print(f"  Score: {overall_score:.2f} | Sources: {test_result['num_sources']} | Error: {test_result['has_error']}")
            
            # Calculate dataset metrics
            dataset_scores = [r["overall_score"] for r in dataset_results]
            results["dataset_results"][dataset_key] = {
                "results": dataset_results,
                "avg_score": sum(dataset_scores) / len(dataset_scores),
                "min_score": min(dataset_scores),
                "max_score": max(dataset_scores),
                "total_tests": len(dataset_results)
            }
            
            print(f"Dataset {dataset_key} average score: {results['dataset_results'][dataset_key]['avg_score']:.2f}")
        
        # Overall metrics
        if all_scores:
            results["overall_metrics"] = {
                "total_tests": len(all_scores),
                "avg_score": sum(all_scores) / len(all_scores),
                "min_score": min(all_scores),
                "max_score": max(all_scores),
                "pass_rate": sum(1 for score in all_scores if score >= 0.7) / len(all_scores)
            }
        
        return results
    
    def save_evaluation_results(self, results: Dict, filename: str = None):
        """Save evaluation results to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"banking_rag_evaluation_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Evaluation results saved to: {filename}")
    
    def print_evaluation_summary(self, results: Dict):
        """Print a comprehensive evaluation summary"""
        print("\n" + "="*60)
        print("🏦 BANKING RAG SYSTEM EVALUATION SUMMARY")
        print("="*60)
        
        overall = results.get("overall_metrics", {})
        print(f"📊 Overall Performance:")
        print(f"   • Total Tests: {overall.get('total_tests', 0)}")
        print(f"   • Average Score: {overall.get('avg_score', 0):.3f}")
        print(f"   • Pass Rate (≥0.7): {overall.get('pass_rate', 0):.1%}")
        print(f"   • Score Range: {overall.get('min_score', 0):.3f} - {overall.get('max_score', 0):.3f}")
        
        print(f"\n📈 Dataset Breakdown:")
        for dataset_name, dataset_result in results.get("dataset_results", {}).items():
            print(f"   • {dataset_name.title()}:")
            print(f"     - Average Score: {dataset_result.get('avg_score', 0):.3f}")
            print(f"     - Tests: {dataset_result.get('total_tests', 0)}")
        
        # Recommendations
        avg_score = overall.get('avg_score', 0)
        print(f"\n💡 Recommendations:")
        if avg_score >= 0.8:
            print("   ✅ Excellent performance! System is production-ready.")
        elif avg_score >= 0.7:
            print("   ✅ Good performance. Consider minor optimizations.")
        elif avg_score >= 0.6:
            print("   ⚠️ Moderate performance. Needs improvement in key areas.")
        else:
            print("   ❌ Poor performance. Significant improvements needed.")
        
        print(f"\n🔧 Configuration Status:")
        # Check system health
        try:
            health_response = requests.get(f"{self.api_base_url}/health")
            if health_response.status_code == 200:
                health_data = health_response.json()
                print(f"   • LangSmith Tracing: {'✅' if health_data.get('langsmith_tracing') else '❌'}")
                print(f"   • OpenAI Available: {'✅' if health_data.get('openai_available') else '❌'}")
                print(f"   • Documents Loaded: {health_data.get('documents_in_store', 0):,}")
        except:
            print("   • System Status: ❌ Unable to connect")

async def main():
    """Main evaluation runner"""
    print("🏦 Banking RAG System - LangSmith Evaluation Framework")
    print("=" * 60)
    
    # Initialize evaluator
    evaluator = BankingRAGEvaluator()
    
    # Check if server is running
    try:
        health_response = requests.get(f"{evaluator.api_base_url}/health")
        if health_response.status_code != 200:
            print("❌ Banking RAG server is not running!")
            print("Please start the server: python simple_server.py")
            return
        
        health_data = health_response.json()
        print(f"✅ Server is running")
        print(f"   • LangSmith: {'✅' if health_data.get('langsmith_tracing') else '❌'}")
        print(f"   • OpenAI: {'✅' if health_data.get('openai_available') else '❌'}")
        
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return
    
    # Run evaluation
    print("\n🚀 Starting comprehensive evaluation...")
    results = await evaluator.run_evaluation_suite("all")
    
    # Print summary
    evaluator.print_evaluation_summary(results)
    
    # Save results
    evaluator.save_evaluation_results(results)
    
    print(f"\n✅ Evaluation completed!")

if __name__ == "__main__":
    asyncio.run(main()) 