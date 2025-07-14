import networkx as nx
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI
from typing import List, Dict, Any
from app.rag_pipeline import RAGPipeline

class RelationshipMappingAgent:
    """
    An agent that extracts entities and relationships from documents to build a graph.
    """

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.extraction_prompt = self._create_extraction_prompt()

    def _create_extraction_prompt(self) -> ChatPromptTemplate:
        """
        Creates the prompt for extracting entities and relationships.
        """
        system_message = """
You are an expert at extracting entities and their relationships from text.
From the given text, identify the key entities (e.g., people, organizations, concepts)
and the relationships between them.

Return a JSON object with two keys: 'entities' and 'relationships'.
- 'entities' should be a list of strings, where each string is a unique entity.
- 'relationships' should be a list of lists, where each inner list contains two related entities.

Example:
Text: "Apple, the tech giant, was co-founded by Steve Jobs and Steve Wozniak. Tim Cook is the current CEO of Apple."
{
    "entities": ["Apple", "Steve Jobs", "Steve Wozniak", "Tim Cook"],
    "relationships": [
        ["Apple", "Steve Jobs"],
        ["Apple", "Steve Wozniak"],
        ["Apple", "Tim Cook"],
        ["Steve Jobs", "Steve Wozniak"]
    ]
}
"""
        return ChatPromptTemplate.from_messages([("system", system_message), ("human", "{chunk}")])

    def extract_graph(self, rag_pipeline: RAGPipeline) -> nx.Graph:
        """
        Extracts a graph of entities and relationships from all documents in the pipeline.
        """
        graph = nx.Graph()
        extraction_chain = self.extraction_prompt | self.llm | JsonOutputParser()

        for doc in rag_pipeline.documents_for_bm25:
            try:
                result = extraction_chain.invoke({"chunk": doc.page_content})
                entities = result.get("entities", [])
                relationships = result.get("relationships", [])

                for entity in entities:
                    if not graph.has_node(entity):
                        graph.add_node(entity)

                for rel in relationships:
                    if len(rel) == 2 and graph.has_node(rel[0]) and graph.has_node(rel[1]):
                        graph.add_edge(rel[0], rel[1])
            except Exception as e:
                # Log or handle cases where the LLM output is not valid JSON
                print(f"Could not extract graph from chunk: {e}")
                continue

        return graph

    def to_json(self, graph: nx.Graph) -> Dict[str, List[Dict[str, Any]]]:
        """
        Converts a networkx graph to a JSON format suitable for frontend visualization.
        """
        return {
            "nodes": [{"id": node, "label": node} for node in graph.nodes()],
            "edges": [{"from": u, "to": v} for u, v in graph.edges()],
        } 