from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_openai import ChatOpenAI
from typing import Dict, Any, List, Tuple

class QueryDecompositionAgent:
    """
    An agent that decomposes a complex query into a series of simpler,
    executable sub-queries and then synthesizes the results.
    """

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.query_decomposition_prompt = self._create_decomposition_prompt()
        self.synthesis_prompt = self._create_synthesis_prompt()

    def _create_decomposition_prompt(self) -> ChatPromptTemplate:
        """
        Creates the prompt for the query decomposition step.
        """
        system_message = """
You are an expert at query decomposition. Your task is to break down a complex user question
into a series of smaller, self-contained sub-questions. These sub-questions will then be
executed sequentially to build a comprehensive answer.

- The sub-questions should be answerable by a search over a document corpus.
- Each sub-question should be a standalone question.
- The plan should be logical and sequential.

Return a JSON object with a single key 'plan' containing a list of strings, where each string is a sub-question.
Example:
User Question: "Compare the performance of the latest React and Vue frameworks, and what are the main differences in their state management?"
{
    "plan": [
        "What are the latest performance metrics for the React framework?",
        "What are the latest performance metrics for the Vue framework?",
        "What is the primary state management approach in React?",
        "What is the primary state management approach in Vue?",
        "What are the main differences in state management between React and Vue?"
    ]
}
"""
        return ChatPromptTemplate.from_messages([("system", system_message), ("human", "{question}")])

    def _create_synthesis_prompt(self) -> ChatPromptTemplate:
        """
        Creates the prompt for the final answer synthesis step.
        """
        system_message = """
You are a master at synthesizing information. You have been provided with a series of
sub-questions and their corresponding answers. Your task is to combine this information
into a single, comprehensive, and well-structured final answer to the original user question.

- The final answer should be clear, concise, and directly address the user's original question.
- Do not just list the answers; synthesize them into a coherent narrative.
- If the answers are contradictory or insufficient, state that a clear answer could not be found.
"""
        return ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", "Original Question: {original_question}\n\nSub-Question Answers:\n{sub_question_answers}")
        ])

    def decompose_query(self, question: str) -> Dict[str, Any]:
        """
        Decomposes the user's question into a plan of sub-queries.
        """
        chain = self.query_decomposition_prompt | self.llm | JsonOutputParser()
        return chain.invoke({"question": question})

    def synthesize_answer(self, original_question: str, sub_question_answers: List[Tuple[str, str]]) -> str:
        """
        Synthesizes the final answer from the sub-question results.
        """
        formatted_answers = "\n\n".join([f"Sub-Question: {q}\nAnswer: {a}" for q, a in sub_question_answers])
        
        chain = self.synthesis_prompt | self.llm
        response = chain.invoke({
            "original_question": original_question,
            "sub_question_answers": formatted_answers
        })
        
        # Ensure we return a string
        if hasattr(response, 'content'):
            return str(response.content)
        return str(response)

    def execute_plan(self, question: str, rag_pipeline) -> Dict[str, Any]:
        """
        Executes the full query decomposition and synthesis process.
        
        Args:
            question: The original user question.
            rag_pipeline: An instance of the RAGPipeline to execute sub-queries.
            
        Returns:
            A dictionary containing the final answer and the intermediate steps.
        """
        # 1. Decompose the query into a plan
        decomposition = self.decompose_query(question)
        plan = decomposition.get("plan", [])

        if not plan:
            # If no plan is generated, fall back to a simple query
            result = rag_pipeline.query(question)
            return {
                "final_answer": result["answer"],
                "source_documents": result["source_documents"],
                "intermediate_steps": []
            }

        # 2. Execute each sub-query and collect the answers
        sub_question_answers = []
        all_source_documents = []

        for sub_query in plan:
            result = rag_pipeline.query(sub_query)
            answer = result.get("answer", "No answer found.")
            sub_question_answers.append((sub_query, answer))
            
            # Collect unique source documents
            for doc in result.get("source_documents", []):
                if doc not in all_source_documents:
                    all_source_documents.append(doc)

        # 3. Synthesize the final answer
        final_answer = self.synthesize_answer(question, sub_question_answers)

        return {
            "final_answer": final_answer,
            "source_documents": all_source_documents,
            "intermediate_steps": sub_question_answers
        } 