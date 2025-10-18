"""
Smart PDF Chat - Production Streamlit App
Deployable to Streamlit Cloud or Hugging Face Spaces
"""

import streamlit as st
import os
import time
from pathlib import Path
import tempfile
from datetime import datetime
import json

# Suppress warnings
import warnings
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

# Import ML libraries
import torch
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
import pdfplumber
from typing import Dict, List
import numpy as np
import uuid

# ========================================
# CONFIGURATION
# ========================================
MODEL_CHOICE = os.environ.get('MODEL_CHOICE', 'flan-t5')  # or 'mistral'
CHUNK_SIZE = 600
CHUNK_OVERLAP = 100
TOP_K = 3

# ========================================
# PAGE CONFIG
# ========================================
st.set_page_config(
    page_title="Smart PDF Chat",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========================================
# CORE CLASSES
# ========================================

class PDFProcessor:
    """Extract text from PDF files"""
    
    def extract_text(self, pdf_path: str) -> Dict:
        text_by_page = {}
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    if text := page.extract_text():
                        text_by_page[page_num] = text
            return {
                'file_name': Path(pdf_path).name,
                'num_pages': len(text_by_page),
                'text_by_page': text_by_page
            }
        except Exception as e:
            st.error(f"Error processing {Path(pdf_path).name}: {e}")
            return None


class TextChunker:
    """Split text into overlapping chunks"""
    
    def __init__(self, chunk_size=600, chunk_overlap=100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_with_metadata(self, text_by_page: Dict, file_name: str) -> List[Dict]:
        chunks = []
        for page_num, text in text_by_page.items():
            start = 0
            while start < len(text):
                end = start + self.chunk_size
                chunk = text[start:end].strip()
                if chunk:
                    chunks.append({
                        'text': chunk,
                        'page': page_num,
                        'file_name': file_name
                    })
                start = end - self.chunk_overlap
        return chunks


class VectorStore:
    """ChromaDB vector database"""
    
    def __init__(self):
        self.client = chromadb.Client(Settings(anonymized_telemetry=False))
        self.collection = None
        self._ensure_collection()
    
    def _ensure_collection(self):
        """Ensure collection exists before operations"""
        try:
            self.collection = self.client.get_collection('pdfs')
        except:
            self.collection = self.client.create_collection('pdfs', metadata={"hnsw:space": "cosine"})
    
    def add_documents(self, chunks: List[Dict], embeddings: np.ndarray):
        self._ensure_collection()  # Ensure collection exists
        self.collection.add(
            ids=[str(uuid.uuid4()) for _ in chunks],
            embeddings=embeddings.tolist(),
            documents=[c['text'] for c in chunks],
            metadatas=[{'page': c['page'], 'file_name': c['file_name']} for c in chunks]
        )
    
    def query(self, emb: np.ndarray, top_k=3):
        self._ensure_collection()  # Ensure collection exists
        results = self.collection.query(query_embeddings=[emb.tolist()], n_results=top_k)
        return {
            'documents': results['documents'][0] if results['documents'] else [],
            'metadatas': results['metadatas'][0] if results['metadatas'] else []
        }
    
    def clear(self):
        """Clear all documents"""
        try:
            self.client.delete_collection('pdfs')
        except:
            pass
        finally:
            self._ensure_collection()  # Recreate collection


class RAGSystem:
    """End-to-end RAG pipeline"""
    
    def __init__(self, pdf_proc, chunker, emb_model, vec_store, gen_fn):
        self.pdf_proc = pdf_proc
        self.chunker = chunker
        self.emb_model = emb_model
        self.vec_store = vec_store
        self.generate = gen_fn
    
    def ingest_pdf(self, pdf_path: str) -> Dict:
        pdf_data = self.pdf_proc.extract_text(pdf_path)
        if not pdf_data:
            return {'error': 'Failed to extract text'}
        
        chunks = self.chunker.chunk_with_metadata(pdf_data['text_by_page'], pdf_data['file_name'])
        
        embeddings = self.emb_model.encode(
            [c['text'] for c in chunks],
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        
        self.vec_store.add_documents(chunks, embeddings)
        
        return {
            'file_name': pdf_data['file_name'],
            'num_pages': pdf_data['num_pages'],
            'num_chunks': len(chunks)
        }
    
    def query(self, question: str, top_k=3) -> Dict:
        start = time.time()
        
        # Embed query
        query_emb = self.emb_model.encode([question], convert_to_numpy=True, normalize_embeddings=True)[0]
        
        # Retrieve
        results = self.vec_store.query(query_emb, top_k)
        if not results['documents']:
            return {'answer': 'No documents found. Please upload PDFs first.', 'sources': [], 'time': 0}
        
        # Format context
        context = '\n'.join([f"[Pg{m['page']}] {doc}" for doc, m in zip(results['documents'], results['metadatas'])])
        
        # Generate
        answer = self.generate(question, context)
        
        elapsed = time.time() - start
        
        return {
            'answer': answer,
            'sources': results['metadatas'],
            'time': elapsed
        }


# ========================================
# MODEL LOADING (CACHED)
# ========================================

@st.cache_resource(show_spinner=False)
def load_models():
    """Load all models (cached to avoid reloading)"""
    
    with st.spinner("🤖 Loading AI models... (first time only, ~2 min)"):
        # Embedding model
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2', device=device)
        
        # LLM model (Flan-T5 for speed)
        model_name = 'google/flan-t5-large'
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSeq2SeqLM.from_pretrained(
            model_name,
            device_map="auto",
            dtype=torch.float16 if torch.cuda.is_available() else torch.float32
        )
        
        llm_pipe = pipeline(
            "text2text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=80,
            do_sample=False,
            num_beams=1
        )
        
        def generate(prompt, context):
            full_prompt = f"answer: {prompt}\n\ncontext: {context[:600]}"
            result = llm_pipe(full_prompt)[0]['generated_text']
            return result.strip()
        
        return embedding_model, generate, device


# ========================================
# INITIALIZE SESSION STATE
# ========================================

def init_session_state():
    """Initialize session state variables"""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.chat_history = []
        st.session_state.uploaded_files = []
        st.session_state.total_chunks = 0


# ========================================
# MAIN APP
# ========================================

def main():
    init_session_state()
    
    # Header
    st.title("📚 Smart PDF Chat")
    st.markdown("**Ask questions about your documents using AI**")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Model info
        device_info = "GPU" if torch.cuda.is_available() else "CPU"
        st.info(f"**Device:** {device_info}\n**Model:** Flan-T5 Large")
        
        st.markdown("---")
        
        # Upload section
        st.header("📤 Upload PDFs")
        uploaded_files = st.file_uploader(
            "Choose PDF files",
            type=['pdf'],
            accept_multiple_files=True,
            help="Upload one or more PDF documents"
        )
        
        # Process button
        if uploaded_files:
            if st.button("🚀 Process PDFs", type="primary", use_container_width=True):
                process_pdfs(uploaded_files)
        
        st.markdown("---")
        
        # Stats
        if st.session_state.uploaded_files:
            st.header("📊 Stats")
            st.metric("Files Loaded", len(st.session_state.uploaded_files))
            st.metric("Total Chunks", st.session_state.total_chunks)
        
        st.markdown("---")
        
        # Clear button
        if st.button("🗑️ Clear All", use_container_width=True):
            clear_all()
        
        st.markdown("---")
        
        # Export chat
        if st.session_state.chat_history:
            if st.button("💾 Export Chat", use_container_width=True):
                export_chat()
    
    # Main content
    if not st.session_state.uploaded_files:
        # Welcome screen
        st.markdown("""
        ## 👋 Welcome!
        
        ### How to use:
        1. **Upload PDFs** in the sidebar
        2. **Click "Process PDFs"** to analyze them
        3. **Ask questions** in the chat below
        
        ### Features:
        - ⚡ Fast responses (1-2 seconds)
        - 📄 Multi-document support
        - 🔍 Source citations with page numbers
        - 💾 Export chat history
        - 🎯 Accurate AI-powered answers
        
        ### Example questions:
        - "What is the main topic of this document?"
        - "Summarize the key findings"
        - "What methodology was used?"
        - "List the main conclusions"
        """)
    else:
        # Chat interface
        chat_interface()


def process_pdfs(uploaded_files):
    """Process uploaded PDF files"""
    
    # Load models
    embedding_model, generate, device = load_models()
    
    # Initialize components
    pdf_processor = PDFProcessor()
    chunker = TextChunker(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    vector_store = VectorStore()
    
    # Clear previous data if new files
    if uploaded_files != st.session_state.get('last_upload'):
        vector_store.clear()
        st.session_state.uploaded_files = []
        st.session_state.total_chunks = 0
    
    # Store RAG system in session state
    if 'rag' not in st.session_state:
        st.session_state.rag = RAGSystem(pdf_processor, chunker, embedding_model, vector_store, generate)
    
    progress_bar = st.progress(0)
    status = st.empty()
    
    total_files = len(uploaded_files)
    
    for idx, uploaded_file in enumerate(uploaded_files):
        status.text(f"Processing {uploaded_file.name}... ({idx+1}/{total_files})")
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_path = tmp_file.name
        
        try:
            # Ingest
            result = st.session_state.rag.ingest_pdf(tmp_path)
            
            if 'error' not in result:
                st.session_state.uploaded_files.append({
                    'name': result['file_name'],
                    'pages': result['num_pages'],
                    'chunks': result['num_chunks']
                })
                st.session_state.total_chunks += result['num_chunks']
        finally:
            os.unlink(tmp_path)
        
        progress_bar.progress((idx + 1) / total_files)
    
    status.empty()
    progress_bar.empty()
    
    st.success(f"✅ Processed {len(uploaded_files)} files successfully!")
    st.session_state.last_upload = uploaded_files
    st.rerun()


def chat_interface():
    """Chat interface for asking questions"""
    
    st.header("💬 Chat with Your Documents")
    
    # Display file info
    with st.expander("📄 Loaded Documents", expanded=False):
        for file_info in st.session_state.uploaded_files:
            st.markdown(f"- **{file_info['name']}** - {file_info['pages']} pages, {file_info['chunks']} chunks")
    
    # Display chat history
    for chat in st.session_state.chat_history:
        with st.chat_message("user"):
            st.markdown(chat['question'])
        
        with st.chat_message("assistant"):
            st.markdown(chat['answer'])
            if chat['sources']:
                sources_text = ", ".join([f"Pg{s['page']} ({s['file_name']})" for s in chat['sources']])
                st.caption(f"📚 Sources: {sources_text} | ⏱️ {chat['time']:.1f}s")
    
    # Chat input
    if question := st.chat_input("Ask a question about your documents..."):
        # Display user message
        with st.chat_message("user"):
            st.markdown(question)
        
        # Get response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = st.session_state.rag.query(question, top_k=TOP_K)
            
            st.markdown(response['answer'])
            
            if response['sources']:
                sources_text = ", ".join([f"Pg{s['page']} ({s['file_name']})" for s in response['sources']])
                st.caption(f"📚 Sources: {sources_text} | ⏱️ {response['time']:.1f}s")
        
        # Save to history
        st.session_state.chat_history.append({
            'question': question,
            'answer': response['answer'],
            'sources': response['sources'],
            'time': response['time'],
            'timestamp': datetime.now().isoformat()
        })


def clear_all():
    """Clear all data"""
    st.session_state.chat_history = []
    st.session_state.uploaded_files = []
    st.session_state.total_chunks = 0
    if 'rag' in st.session_state:
        st.session_state.rag.vec_store.clear()
    st.success("✅ All data cleared!")
    st.rerun()


def export_chat():
    """Export chat history as JSON"""
    export_data = {
        'exported_at': datetime.now().isoformat(),
        'files': st.session_state.uploaded_files,
        'chat_history': st.session_state.chat_history
    }
    
    json_str = json.dumps(export_data, indent=2)
    st.download_button(
        label="📥 Download Chat History",
        data=json_str,
        file_name=f"pdf_chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )


# ========================================
# RUN APP
# ========================================

if __name__ == "__main__":
    main()

