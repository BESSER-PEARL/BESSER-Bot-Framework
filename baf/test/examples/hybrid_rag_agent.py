# You may need to add your working directory to the Python path. To do so, uncomment the following lines of code
# import sys
# sys.path.insert("path/to/baf") # Replace with your directory path

import logging
import os
import pickle

from chromadb import EphemeralClient
from langchain_community.document_loaders.recursive_url_loader import RecursiveUrlLoader
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from baf import nlp
from baf.core.agent import Agent
from baf.core.session import Session
from baf.exceptions.logger import logger
from baf.library.transition.events.base_events import ReceiveFileEvent
from baf.nlp.llm.llm_openai_api import LLMOpenAI
from baf.nlp.rag.rag import RAG, RAGMessage, HybridRAG

logger.setLevel(logging.INFO)

agent = Agent('hybrid_rag_agent')
agent.load_properties('config.yaml')
websocket_platform = agent.use_websocket_platform(use_ui=True)

splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
gpt = LLMOpenAI(agent=agent, name='gpt-4o-mini', parameters={})

openai_api_key = agent.get_property(nlp.OPENAI_API_KEY)
vector_store = Chroma(
    client=EphemeralClient(),
    embedding_function=OpenAIEmbeddings(openai_api_key=openai_api_key),
)

# Option A: pre-indexed corpus (BM25 + vector ready before agent starts)
# Choose ONE loading strategy (A1 / A2 / A3). All produce `all_docs`.
# The common block below then splits, caches, and indexes them.

# A1: Crawl one or more URLs  ← active by default; comment out to switch strategy
urls = [
    'https://arxiv.org/pdf/2603.23802',
    'https://www.aisi.gov.uk/blog/how-are-ai-agents-used-evidence-from-177000-ai-agent-tools',
    ]
all_docs = []
for url in urls:
    loader = RecursiveUrlLoader(url=url, max_depth=1, timeout=10)
    all_docs.extend(loader.load())

# A2: Load local documents (PDF, DOCX, TXT, MD from a directory)
# all_docs = []
# docs_dir = '/path/to/your/documents/'
# for fname in os.listdir(docs_dir):
#     fmt = fname.rsplit('.', 1)[-1].lower()
#     if fmt in RAG.SUPPORTED_FORMATS:
#         all_docs.extend(RAG.load_documents_from_path(os.path.join(docs_dir, fname), fmt))

# A3: Raw text (hardcoded facts, content built from prompts or config)
# all_docs = [
#     Document(page_content="Your first block of knowledge here.", metadata={}),
#     Document(page_content="Your second block of knowledge here.", metadata={}),
# ]

# ── Common block (shared by all Option A strategies) ─────────────────────────
_SPLITS_PATH = 'splits.pkl'
if os.path.exists(_SPLITS_PATH):
    with open(_SPLITS_PATH, 'rb') as f:
        splits = pickle.load(f)
else:
    splits = splitter.split_documents(all_docs)
    with open(_SPLITS_PATH, 'wb') as f:
        pickle.dump(splits, f)

vector_store.add_documents(splits)

rag = HybridRAG(
    agent=agent,
    vector_store=vector_store,
    splitter=splitter,
    llm_name='gpt-4o-mini',
    k=4,
    bm25_docs=splits,  # seeds BM25 at startup; runtime uploads update it automatically
)

# ── Option B: runtime uploads only (no pre-indexed corpus) ───────────────────
# Omit bm25_docs — BM25 activates automatically after the first add_file / add_text call.
# Comment out the entire Option A + common block above and uncomment this:
# rag = HybridRAG(agent=agent, vector_store=vector_store, splitter=splitter,
#                 llm_name='gpt-4o-mini', k=4)


# ── States ────────────────────────────────────────────────────────────────────
def upload_file_body(session: Session):
    rag.add_file(session.event.file)  # indexes to Chroma and rebuilds BM25


initial_state = agent.new_state('initial_state', initial=True)
upload_file_state = agent.new_state('upload_file_state')
ask_question_state = agent.new_state('ask_question_state')


def initial_body(session: Session):
    session.reply('Hi! Ask your question.')


initial_state.set_body(initial_body)
initial_state.when_event(ReceiveFileEvent()).go_to(upload_file_state)
initial_state.when_no_intent_matched().go_to(ask_question_state)

upload_file_state.set_body(upload_file_body)
upload_file_state.when_no_intent_matched().go_to(ask_question_state)


def ask_question_body(session: Session):
    rag_message: RAGMessage = session.run_rag(session.event.message)
    websocket_platform.reply_rag(session, rag_message)


ask_question_state.set_body(ask_question_body)
ask_question_state.go_to(initial_state)

if __name__ == '__main__':
    agent.run()
