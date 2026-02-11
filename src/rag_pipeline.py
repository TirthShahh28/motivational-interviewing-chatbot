"""
RAG (Retrieval-Augmented Generation) Pipeline
=============================================
Handles loading, chunking, embedding, and retrieval of expert knowledge.

The knowledge base contains SME-provided guidelines on:
- Motivational Interviewing techniques
- Harm reduction strategies  
- De-escalation approaches
- Sample therapeutic dialogues
"""

import os
from pathlib import Path
from typing import List, Optional
from loguru import logger

from langchain_community.document_loaders import (
    TextLoader,
    DirectoryLoader,
    UnstructuredMarkdownLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

from src.config import (
    KNOWLEDGE_BASE_DIR,
    CHROMA_PERSIST_DIR,
    EMBEDDING_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    TOP_K_RESULTS
)


class KnowledgeRetriever:
    """
    Manages the RAG pipeline for expert knowledge retrieval.
    
    Architecture:
    1. Load documents from knowledge_base/
    2. Chunk into semantic units
    3. Embed using sentence-transformers
    4. Store in ChromaDB for vector search
    5. Retrieve relevant chunks at query time
    """
    
    def __init__(self, persist_directory: Path = None):
        """
        Initialize the knowledge retriever.
        
        Args:
            persist_directory: Where to store/load the vector database
        """
        self.persist_dir = persist_directory or CHROMA_PERSIST_DIR
        self.embeddings = None
        self.vectorstore = None
        self.retriever = None
        
        self._initialize_embeddings()
        
    def _initialize_embeddings(self):
        """Load the embedding model."""
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'},  # Change to 'cuda' if GPU available
            encode_kwargs={'normalize_embeddings': True}
        )
        logger.info("Embedding model loaded successfully")
    
    def load_and_index_documents(self, knowledge_dir: Path = None) -> int:
        """
        Load documents from knowledge base and create vector index.
        
        Args:
            knowledge_dir: Directory containing knowledge base files
            
        Returns:
            Number of chunks indexed
        """
        knowledge_dir = knowledge_dir or KNOWLEDGE_BASE_DIR
        
        if not knowledge_dir.exists():
            logger.warning(f"Knowledge base directory not found: {knowledge_dir}")
            return 0
        
        logger.info(f"Loading documents from: {knowledge_dir}")
        
        # Load different file types
        documents = []
        
        # Load .txt files
        txt_loader = DirectoryLoader(
            str(knowledge_dir),
            glob="**/*.txt",
            loader_cls=TextLoader,
            loader_kwargs={'encoding': 'utf-8'}
        )
        
        # Load .md files
        md_loader = DirectoryLoader(
            str(knowledge_dir),
            glob="**/*.md",
            loader_cls=TextLoader,
            loader_kwargs={'encoding': 'utf-8'}
        )
        
        try:
            documents.extend(txt_loader.load())
            documents.extend(md_loader.load())
        except Exception as e:
            logger.error(f"Error loading documents: {e}")
            
        if not documents:
            logger.warning("No documents found in knowledge base")
            return 0
        
        logger.info(f"Loaded {len(documents)} documents")
        
        # Split into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        chunks = text_splitter.split_documents(documents)
        logger.info(f"Split into {len(chunks)} chunks")
        
        # Create vector store
        self.persist_dir.parent.mkdir(parents=True, exist_ok=True)
        
        self.vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=str(self.persist_dir)
        )
        
        # Create retriever
        self.retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": TOP_K_RESULTS}
        )
        
        logger.info(f"Vector store created with {len(chunks)} chunks")
        return len(chunks)
    
    def load_existing_index(self) -> bool:
        """
        Load an existing vector store from disk.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.persist_dir.exists():
            logger.warning("No existing vector store found")
            return False
        
        try:
            self.vectorstore = Chroma(
                persist_directory=str(self.persist_dir),
                embedding_function=self.embeddings
            )
            self.retriever = self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": TOP_K_RESULTS}
            )
            logger.info("Loaded existing vector store")
            return True
        except Exception as e:
            logger.error(f"Failed to load vector store: {e}")
            return False
    
    def retrieve(self, query: str, k: int = None) -> List[dict]:
        """
        Retrieve relevant knowledge for a query.
        
        Args:
            query: The search query (usually user message + context)
            k: Number of results to return
            
        Returns:
            List of dicts with 'content' and 'metadata' keys
        """
        if self.vectorstore is None:
            logger.warning("Vector store not initialized")
            return []
        
        k = k or TOP_K_RESULTS
        
        try:
            docs = self.vectorstore.similarity_search(query, k=k)
            
            results = []
            for doc in docs:
                results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "source": doc.metadata.get("source", "unknown")
                })
            
            logger.debug(f"Retrieved {len(results)} documents for query")
            return results
            
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            return []
    
    def retrieve_for_state(
        self, 
        user_message: str, 
        emotion: str, 
        defensiveness: str
    ) -> List[dict]:
        """
        Retrieve knowledge tailored to user's current state.
        
        Constructs an enhanced query that includes state information
        to find the most relevant intervention strategies.
        
        Args:
            user_message: What the user said
            emotion: Detected emotional state
            defensiveness: Detected defensiveness level
            
        Returns:
            List of relevant knowledge chunks
        """
        # Build enhanced query
        state_context = []
        
        if defensiveness in ["moderate", "high"]:
            state_context.append(f"handling {defensiveness} defensiveness")
            state_context.append("resistance reduction")
            
        if emotion in ["frustrated", "angry"]:
            state_context.append("de-escalation")
            state_context.append("validation")
        elif emotion in ["sad", "hopeless"]:
            state_context.append("building hope")
            state_context.append("empathy")
        elif emotion in ["anxious"]:
            state_context.append("reducing anxiety")
            state_context.append("reassurance")
        elif emotion in ["contemplative", "hopeful"]:
            state_context.append("supporting change")
            state_context.append("change talk")
        
        # Combine into search query
        enhanced_query = f"{user_message} {' '.join(state_context)}"
        
        return self.retrieve(enhanced_query)
