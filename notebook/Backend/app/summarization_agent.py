from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from typing import List
from app.rag_pipeline import RAGPipeline

class SummarizationAgent:
    """
    An agent that generates summaries of documents using a map-reduce strategy.
    """

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.map_prompt = self._create_map_prompt()
        self.reduce_prompt = self._create_reduce_prompt()

    def _create_map_prompt(self) -> ChatPromptTemplate:
        """
        Creates the prompt for the map step (summarizing individual chunks).
        """
        system_message = """
You are a skilled summarizer. Your task is to create a concise summary of the following text chunk.
Focus on the key points and main ideas.
"""
        return ChatPromptTemplate.from_messages([("system", system_message), ("human", "{chunk}")])

    def _create_reduce_prompt(self) -> ChatPromptTemplate:
        """
        Creates the prompt for the reduce step (combining individual summaries).
        """
        system_message = """
You are an expert at synthesizing information. You have been provided with a series of summaries
from different parts of a document. Your task is to combine these summaries into a single,
coherent, and comprehensive final summary.
"""
        return ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", "Here are the individual summaries:\n{summaries}\n\nPlease create a final summary:")
        ])

    def summarize(self, rag_pipeline: RAGPipeline) -> str:
        """
        Generates a summary of all documents currently in the RAG pipeline.
        """
        if not rag_pipeline.documents_for_bm25:
            return "There are no documents to summarize."

        # Map step: Summarize each document chunk
        individual_summaries = []
        map_chain = self.map_prompt | self.llm | StrOutputParser()
        
        for doc in rag_pipeline.documents_for_bm25:
            summary = map_chain.invoke({"chunk": doc.page_content})
            individual_summaries.append(summary)

        # Reduce step: Combine the individual summaries
        combined_summaries = "\n\n".join(individual_summaries)
        reduce_chain = self.reduce_prompt | self.llm | StrOutputParser()
        final_summary = reduce_chain.invoke({"summaries": combined_summaries})

        return final_summary 