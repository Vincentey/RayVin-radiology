"""
RAG Pipeline for X-Ray Clinical Recommendations

This module handles:
1. Embedding clinical recommendations using OpenAI
2. Storing and retrieving from Pinecone vector database
3. Generating contextualized recommendations using GPT-4
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec
from .knowledge_base import PATHOLOGY_RECOMMENDATIONS
from .ct_mri_knowledge_base import CT_MRI_RECOMMENDATIONS

# Load environment variables from .env file
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(env_path)


class RAGPipeline:
    """
    RAG Pipeline for retrieving and generating clinical recommendations
    based on chest X-ray findings.
    """
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        pinecone_api_key: Optional[str] = None,
        index_name: str = "xray-recommendations",
        embedding_model: str = "text-embedding-3-small",
        llm_model: str = "gpt-4"
    ):
        """
        Initialize the RAG pipeline.
        
        Args:
            openai_api_key: OpenAI API key (defaults to env var OPENAI_API_KEY)
            pinecone_api_key: Pinecone API key (defaults to env var PINECONE_API_KEY)
            index_name: Name of the Pinecone index
            embedding_model: OpenAI embedding model to use
            llm_model: OpenAI chat model for generation
        """
        # Initialize OpenAI
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY env var or pass openai_api_key")
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        
        # Initialize Pinecone
        self.pinecone_api_key = pinecone_api_key or os.getenv("PINECONE_API_KEY")
        if not self.pinecone_api_key:
            raise ValueError("Pinecone API key not provided. Set PINECONE_API_KEY env var or pass pinecone_api_key")
        self.pc = Pinecone(api_key=self.pinecone_api_key)
        
        self.index_name = index_name
        self.embedding_model = embedding_model
        self.llm_model = llm_model
        self.embedding_dimension = 1536  # text-embedding-3-small dimension
        
        # Index will be initialized lazily
        self._index = None
        self._is_populated = False
    
    def _get_or_create_index(self):
        """Get existing index or create a new one."""
        if self._index is not None:
            return self._index
        
        # Check if index exists
        existing_indexes = [idx.name for idx in self.pc.list_indexes()]
        
        if self.index_name not in existing_indexes:
            print(f"Creating new Pinecone index: {self.index_name}")
            self.pc.create_index(
                name=self.index_name,
                dimension=self.embedding_dimension,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
            print(f"Index '{self.index_name}' created successfully")
        
        self._index = self.pc.Index(self.index_name)
        return self._index
    
    def _create_embedding(self, text: str, max_retries: int = 3) -> List[float]:
        """Create embedding vector for given text with retry logic."""
        import time
        
        for attempt in range(max_retries):
            try:
                response = self.openai_client.embeddings.create(
                    model=self.embedding_model,
                    input=text,
                    timeout=30.0
                )
                return response.data[0].embedding
            except Exception as e:
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Failed to create embedding after {max_retries} attempts: {e}")
                time.sleep(2 ** attempt)  # Exponential backoff
        
        raise RuntimeError("Unexpected error in embedding creation")
    
    def _create_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Create embedding vectors for multiple texts."""
        response = self.openai_client.embeddings.create(
            model=self.embedding_model,
            input=texts
        )
        return [item.embedding for item in response.data]
    
    def populate_knowledge_base(self, force: bool = False) -> Dict:
        """
        Embed all clinical recommendations and store in Pinecone.
        
        Args:
            force: If True, re-populate even if already done
            
        Returns:
            Dict with status and counts
        """
        index = self._get_or_create_index()
        
        # Check if already populated
        stats = index.describe_index_stats()
        if stats.total_vector_count > 0 and not force:
            print(f"Index already contains {stats.total_vector_count} vectors. Use force=True to re-populate.")
            self._is_populated = True
            return {
                "status": "already_populated",
                "vector_count": stats.total_vector_count
            }
        
        # If forcing, delete existing vectors
        if force and stats.total_vector_count > 0:
            print("Deleting existing vectors...")
            index.delete(delete_all=True)
        
        # Combine X-ray and CT/MRI recommendations
        all_recommendations = PATHOLOGY_RECOMMENDATIONS + CT_MRI_RECOMMENDATIONS
        print(f"Embedding {len(all_recommendations)} clinical recommendations...")
        print(f"  - X-ray pathologies: {len(PATHOLOGY_RECOMMENDATIONS)}")
        print(f"  - CT/MRI pathologies: {len(CT_MRI_RECOMMENDATIONS)}")
        
        # Prepare vectors for upsert
        vectors_to_upsert = []
        
        for doc in all_recommendations:
            # Create embedding for the content
            embedding = self._create_embedding(doc["content"])
            
            # Get modality from doc or infer from id
            modality = doc.get("modality", "X-ray")
            if doc["id"].startswith("ct_"):
                modality = "CT"
            elif doc["id"].startswith("mri_"):
                modality = "MRI"
            
            vectors_to_upsert.append({
                "id": doc["id"],
                "values": embedding,
                "metadata": {
                    "pathology": doc["pathology"],
                    "urgency": doc["urgency"],
                    "specialty": doc["specialty"],
                    "modality": modality,
                    "content": doc["content"][:1000]  # Truncate for metadata limit
                }
            })
            print(f"  Embedded: {doc['pathology']} ({modality})")
        
        # Upsert in batches
        batch_size = 100
        for i in range(0, len(vectors_to_upsert), batch_size):
            batch = vectors_to_upsert[i:i + batch_size]
            index.upsert(vectors=batch)
        
        self._is_populated = True
        print(f"Successfully populated {len(vectors_to_upsert)} vectors")
        
        return {
            "status": "populated",
            "vector_count": len(vectors_to_upsert)
        }
    
    def retrieve_recommendations(
        self, 
        findings: List[str], 
        top_k: int = 5
    ) -> List[Dict]:
        """
        Retrieve relevant clinical recommendations based on findings.
        
        Args:
            findings: List of pathology findings from the vision model
            top_k: Number of recommendations to retrieve
            
        Returns:
            List of relevant recommendation documents
        """
        if not findings:
            return []
        
        index = self._get_or_create_index()
        
        # Ensure knowledge base is populated
        if not self._is_populated:
            stats = index.describe_index_stats()
            if stats.total_vector_count == 0:
                print("Knowledge base empty. Populating...")
                self.populate_knowledge_base()
            else:
                self._is_populated = True
        
        # Create query embedding from findings
        query_text = f"Clinical recommendations for chest X-ray findings: {', '.join(findings)}"
        query_embedding = self._create_embedding(query_text)
        
        # Search Pinecone
        results = index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        # Combine all recommendation sources
        all_recommendations = PATHOLOGY_RECOMMENDATIONS + CT_MRI_RECOMMENDATIONS
        
        # Extract and format results
        retrieved_docs = []
        for match in results.matches:
            # Get full content from knowledge base
            full_doc = None
            for doc in all_recommendations:
                if doc["id"] == match.id:
                    full_doc = doc
                    break
            
            retrieved_docs.append({
                "id": match.id,
                "pathology": match.metadata.get("pathology"),
                "urgency": match.metadata.get("urgency"),
                "specialty": match.metadata.get("specialty"),
                "modality": match.metadata.get("modality", "X-ray"),
                "content": full_doc["content"] if full_doc else match.metadata.get("content"),
                "similarity_score": match.score
            })
        
        return retrieved_docs
    
    def generate_recommendations(
        self,
        findings: List[str],
        finding_probabilities: Optional[Dict[str, float]] = None,
        patient_context: Optional[str] = None
    ) -> Dict:
        """
        Generate clinical recommendations using RAG.
        
        Args:
            findings: List of positive findings from vision model
            finding_probabilities: Optional dict of finding -> probability
            patient_context: Optional additional patient context
            
        Returns:
            Dict with generated recommendations and retrieved documents
        """
        # Retrieve relevant documents
        retrieved_docs = self.retrieve_recommendations(findings, top_k=len(findings) + 2)
        
        # Build context from retrieved documents
        context_parts = []
        for doc in retrieved_docs:
            context_parts.append(f"=== {doc['pathology']} (Urgency: {doc['urgency']}) ===\n{doc['content']}")
        
        context = "\n\n".join(context_parts)
        
        # Build findings description
        findings_desc = []
        for finding in findings:
            if finding_probabilities and finding in finding_probabilities:
                prob = finding_probabilities[finding]
                findings_desc.append(f"- {finding}: {prob:.1%} confidence")
            else:
                findings_desc.append(f"- {finding}")
        
        findings_text = "\n".join(findings_desc)
        
        # Create prompt for GPT-4
        system_prompt = """You are an expert radiologist generating structured radiology reports. 
Format your response as a professional radiology report following ACR guidelines.

IMPORTANT: Include standard disclaimer about AI-assisted analysis requiring physician review."""

        user_prompt = f"""Generate a structured radiology report based on the AI-detected findings and clinical guidelines.

DETECTED FINDINGS:
{findings_text}

{f"CLINICAL HISTORY: {patient_context}" if patient_context else "CLINICAL HISTORY: Not provided"}

REFERENCE GUIDELINES:
{context}

FORMAT YOUR RESPONSE AS A RADIOLOGY REPORT:

EXAMINATION: Chest Radiograph (X-Ray)

TECHNIQUE: [Standard PA/AP view, AI-assisted analysis]

FINDINGS:
[List each finding with location and characteristics]

IMPRESSION:
1. [Primary finding with clinical significance]
2. [Secondary findings if any]

RECOMMENDATIONS:
1. [Most urgent action]
2. [Follow-up imaging if needed]
3. [Specialist referral if indicated]

URGENCY: [Emergent/Urgent/Semi-urgent/Routine]

---
DISCLAIMER: This report was generated with AI assistance using TorchXRayVision and GPT-4. 
All findings require verification by a qualified radiologist. Clinical correlation is recommended."""

        # Generate response with GPT-4 (with retry logic)
        import time
        generated_text = None
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                response = self.openai_client.chat.completions.create(
                    model=self.llm_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3,  # Lower temperature for more consistent medical advice
                    max_tokens=2000,
                    timeout=60.0
                )
                generated_text = response.choices[0].message.content
                break
            except Exception as e:
                print(f"GPT-4 API attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    # Graceful degradation: generate basic report without GPT-4
                    generated_text = self._generate_fallback_report(findings, finding_probabilities, retrieved_docs)
                else:
                    time.sleep(2 ** attempt)
        
        # Determine overall urgency from findings
        urgency_levels = {"emergent": 4, "urgent": 3, "semi-urgent": 2, "routine": 1}
        max_urgency = "routine"
        max_urgency_score = 0
        
        for doc in retrieved_docs:
            urgency = doc.get("urgency", "routine")
            score = urgency_levels.get(urgency, 1)
            if score > max_urgency_score:
                max_urgency_score = score
                max_urgency = urgency
        
        return {
            "findings": findings,
            "recommendations": generated_text,
            "retrieved_documents": retrieved_docs,
            "overall_urgency": max_urgency,
            "model_used": self.llm_model
        }
    
    def _generate_fallback_report(
        self,
        findings: List[str],
        finding_probabilities: Optional[Dict[str, float]],
        retrieved_docs: List[Dict]
    ) -> str:
        """Generate a basic report when GPT-4 is unavailable."""
        report_lines = [
            "EXAMINATION: Chest Radiograph (X-Ray)",
            "",
            "TECHNIQUE: Standard PA/AP view, AI-assisted analysis",
            "",
            "FINDINGS:",
        ]
        
        for finding in findings:
            prob = finding_probabilities.get(finding, 0) if finding_probabilities else 0
            report_lines.append(f"- {finding}: AI detected with {prob:.1%} confidence")
        
        report_lines.extend([
            "",
            "IMPRESSION:",
        ])
        
        for i, finding in enumerate(findings, 1):
            report_lines.append(f"{i}. {finding} detected - requires clinical correlation")
        
        report_lines.extend([
            "",
            "RECOMMENDATIONS:",
            "1. Clinical correlation with patient history and physical examination",
            "2. Consider follow-up imaging if clinically indicated",
            "3. Specialist referral as appropriate",
            "",
            "URGENCY: See retrieved guidelines for urgency levels",
            "",
            "---",
            "DISCLAIMER: This is a basic report generated due to API limitations.",
            "AI-assisted analysis using TorchXRayVision. All findings require verification",
            "by a qualified radiologist. Clinical correlation is recommended."
        ])
        
        return "\n".join(report_lines)


# Singleton instance for the pipeline
_rag_pipeline_instance: Optional[RAGPipeline] = None


def get_rag_pipeline() -> Optional[RAGPipeline]:
    """Get or create the singleton RAG pipeline instance."""
    global _rag_pipeline_instance
    
    if _rag_pipeline_instance is None:
        try:
            _rag_pipeline_instance = RAGPipeline()
        except ValueError as e:
            # Missing API keys - log and return None
            print(f"RAG Pipeline initialization failed (missing API keys): {e}")
            return None
        except Exception as e:
            print(f"RAG Pipeline initialization failed: {e}")
            return None
    
    return _rag_pipeline_instance


def initialize_rag_pipeline(
    openai_api_key: Optional[str] = None,
    pinecone_api_key: Optional[str] = None,
    populate: bool = True
) -> RAGPipeline:
    """
    Initialize the RAG pipeline with optional population of knowledge base.
    
    Args:
        openai_api_key: OpenAI API key
        pinecone_api_key: Pinecone API key
        populate: Whether to populate the knowledge base on initialization
        
    Returns:
        Initialized RAGPipeline instance
    """
    global _rag_pipeline_instance
    
    _rag_pipeline_instance = RAGPipeline(
        openai_api_key=openai_api_key,
        pinecone_api_key=pinecone_api_key
    )
    
    if populate:
        _rag_pipeline_instance.populate_knowledge_base()
    
    return _rag_pipeline_instance

