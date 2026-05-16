import os
import json
import uuid
import datetime
import asyncio
from typing import TypedDict, Annotated, List, Optional
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

from .logger import logger
from .resilience import with_breaker, llm_breaker, llm_fallback

class AgentState(TypedDict):
    original_query: str
    rewritten_query: str
    context: List[str]
    raw_response: str
    final_response: str
    verification_score: float
    is_safe: bool
    confidence_score: float
    messages: Annotated[List[BaseMessage], add_messages]

class LangGuardPipeline:
    def __init__(self, chroma_client=None, neo4j_manager=None):
        self.chroma_client = chroma_client
        self.neo4j_manager = neo4j_manager
        self.workflow = self._build_graph()
        self.checkpointer = MemorySaver()
        self.graph = self.workflow.compile(checkpointer=self.checkpointer)

    def _build_graph(self):
        workflow = StateGraph(AgentState)
        
        # Add Nodes
        workflow.add_node("rewriter", self.query_rewriter)
        workflow.add_node("retriever", self.context_retriever)
        workflow.add_node("reranker", self.context_reranker)
        workflow.add_node("generator", self.llm_generator)
        workflow.add_node("verifier", self.verifier_agent)
        workflow.add_node("guardrails", self.guardrails_node)

        # Add Edges
        workflow.set_entry_point("rewriter")
        workflow.add_edge("rewriter", "retriever")
        workflow.add_edge("retriever", "reranker")
        workflow.add_edge("reranker", "generator")
        workflow.add_edge("generator", "verifier")
        workflow.add_edge("verifier", "guardrails")
        workflow.add_edge("guardrails", END)
        
        return workflow

    # Node Implementations
    def query_rewriter(self, state: AgentState):
        llm = ChatGroq(model="llama-3.3-70b-versatile")
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Rewrite the user query for Vector/Graph search. Output ONLY the query."),
            ("human", "{query}")
        ])
        chain = prompt | llm
        result = chain.invoke({"query": state["original_query"]})
        return {"rewritten_query": result.content}

    async def context_retriever(self, state: AgentState):
        query = state["rewritten_query"]
        
        async def get_chroma():
            if not self.chroma_client: return []
            try:
                collection = self.chroma_client.get_or_create_collection(name="conversations")
                results = self.chroma_client.query(query_texts=[query], n_results=3)
                return results['documents'][0] if results['documents'] else []
            except: return []

        async def get_neo4j():
            if not self.neo4j_manager: return []
            driver = self.neo4j_manager.connect()
            if not driver: return []
            try:
                with driver.session() as session:
                    cypher = "MATCH (q:Query)-[:GEN]->(r:Res) WHERE q.text CONTAINS $q OR r.text CONTAINS $q RETURN r.text LIMIT 2"
                    res = session.run(cypher, q=query)
                    return [record["r.text"] for record in res]
            except: return []

        results = await asyncio.gather(get_chroma(), get_neo4j())
        return {"context": [item for sublist in results for item in sublist]}

    def context_reranker(self, state: AgentState):
        if not state["context"]: return {"context": []}
        llm = ChatGroq(model="llama-3.3-70b-versatile")
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Rank context by relevance. Output top 3 chunks separated by '---'."),
            ("human", "Query: {query}\nChunks:\n{chunks}")
        ])
        chain = prompt | llm
        result = chain.invoke({"query": state["rewritten_query"], "chunks": "\n".join(state["context"])})
        return {"context": [c.strip() for c in result.content.split('---') if c.strip()]}

    def llm_generator(self, state: AgentState):
        llm = ChatGroq(model="llama-3.3-70b-versatile")
        context_text = "\n".join(state["context"])
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Use the following context to answer. Plain text only. Context:\n{context}"),
            ("human", "{query}")
        ])
        chain = prompt | llm
        result = chain.invoke({"query": state["original_query"], "context": context_text})
        return {"raw_response": result.content}

    def verifier_agent(self, state: AgentState):
        llm = ChatGroq(model="llama-3.3-70b-versatile")
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Score response grounding against context (0.0 to 1.0). Output ONLY the number."),
            ("human", "Context: {context}\nResponse: {response}")
        ])
        chain = prompt | llm
        try: score = float(chain.invoke({"context": "\n".join(state["context"]), "response": state["raw_response"]}).content.strip())
        except: score = 0.5
        return {"verification_score": score}

    def guardrails_node(self, state: AgentState):
        is_safe = state["verification_score"] > 0.6
        final_resp = state["raw_response"] if is_safe else "I cannot answer this as it may contain hallucinated information."
        return {"is_safe": is_safe, "final_response": final_resp, "confidence_score": state["verification_score"]}

    async def astream(self, query: str, thread_id: str = "shared"):
        config = {"configurable": {"thread_id": thread_id}}
        inputs = {"original_query": query}
        async for event in self.graph.astream(inputs, config=config, stream_mode="updates"):
            yield event
