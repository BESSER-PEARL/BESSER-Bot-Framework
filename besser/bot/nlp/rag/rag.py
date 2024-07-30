import logging
import os
from typing import TYPE_CHECKING

from huggingface_hub import login
from langchain_community.chat_models import ChatOpenAI, ChatHuggingFace
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings, OpenAIEmbeddings
from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline
from langchain_community.vectorstores import Chroma
from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.prompt_values import PromptValue
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.vectorstores import VectorStore, VectorStoreRetriever
from langchain_text_splitters import TextSplitter, RecursiveCharacterTextSplitter, CharacterTextSplitter

from besser.bot import nlp
from besser.bot.core.message import Message
from besser.bot.nlp import llm

if TYPE_CHECKING:
    from besser.bot.core.session import Session
    from besser.bot.nlp.nlp_engine import NLPEngine


def load_hf_llm(model_id: str, hf_token: str, max_length=2000) -> ChatHuggingFace:
    login(hf_token)
    hf = HuggingFacePipeline.from_model_id(
        model_id=model_id,
        task="text-generation",
        pipeline_kwargs={
            "max_length": max_length,
            "return_full_text": False,
            # "max_new_tokens": 10
        },
    )
    return ChatHuggingFace(llm=hf)


class RAG:

    @staticmethod
    def create_from_properties(nlp_engine: 'NLPEngine') -> 'RAG':
        logging.info(f"[RAG] Creating from properties...")

        # Embeddings
        embeddings_suite = nlp_engine.get_property(nlp.NLP_RAG_EMBEDDINGS_SUITE),
        embeddings_model = nlp_engine.get_property(nlp.NLP_RAG_EMBEDDINGS_NAME),
        if embeddings_suite == llm.OPENAI_LLM_SUITE:
            embeddings = OpenAIEmbeddings(model_name=embeddings_model)
        elif embeddings_suite == llm.HUGGINGFACE_LLM_SUITE:
            embeddings = HuggingFaceEmbeddings(model_name=embeddings_model)

        # Text Splitter
        splitter_name = nlp_engine.get_property(nlp.NLP_RAG_SPLITTER),
        chunk_size = nlp_engine.get_property(nlp.NLP_RAG_CHUNK_SIZE),
        chunk_overlap = nlp_engine.get_property(nlp.NLP_RAG_CHUNK_OVERLAP)
        if splitter_name == 'RecursiveCharacterTextSplitter':
            splitter: TextSplitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        elif splitter_name == 'CharacterTextSplitter':
            splitter: TextSplitter = CharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        # Vector Store
        vector_store_name = nlp_engine.get_property(nlp.NLP_RAG_VECTORSTORE),
        persist_directory = nlp_engine.get_property(nlp.NLP_RAG_PERSIST_DIRECTORY)
        if vector_store_name == 'chroma':
            vector_store: VectorStore = Chroma.from_documents(
                embedding=embeddings,
                persist_directory=persist_directory,
                documents=[]
            )

        # LLM
        llm_suite = nlp_engine.get_property(nlp.NLP_RAG_LLM_SUITE)
        llm_name = nlp_engine.get_property(nlp.NLP_RAG_LLM_NAME)
        if llm_suite == llm.OPENAI_LLM_SUITE:
            llm_model: BaseChatModel = ChatOpenAI(model=llm_name)
        elif llm_suite == llm.HUGGINGFACE_LLM_SUITE:
            max_length = nlp_engine.get_property(nlp.NLP_RAG_MAX_LENGTH)
            hf_token = nlp_engine.get_property(nlp.HF_API_KEY)
            llm_model: BaseChatModel = load_hf_llm(model_id=llm_name, hf_token=hf_token, max_length=max_length)

        return RAG(
            nlp_engine=nlp_engine,
            vector_store=vector_store,
            splitter=splitter,
            llm_model=llm_model
        )

    DEFAULT_LLM_PROMPT = "You are an assistant for question-answering tasks. Based on the previous messages in the conversation (if provided), and additional context retrieved from a database (if provided), answer the user question. If you don't know the answer, just say that you don't know. Note that if the question refers to a previous message, you may have to ignore the context since it is retrieved from the database based only on the question (the retrieval does not take into account the previous messages). Use three sentences maximum and keep the answer concise"

    def __init__(self, nlp_engine: 'NLPEngine', vector_store: VectorStore, splitter: TextSplitter, llm_model: BaseChatModel, llm_prompt: str = None, source_path: str = None, k: int = 4, num_context: int = 0):
        self.nlp_engine: 'NLPEngine' = nlp_engine
        self.vector_store: VectorStore = vector_store
        self.splitter: TextSplitter = splitter
        self.llm: BaseChatModel = llm_model
        if not llm_prompt:
            llm_prompt = RAG.DEFAULT_LLM_PROMPT
        self.llm_prompt = llm_prompt
        self.k: int = k
        self.num_context: int = num_context
        if source_path:
            self.fill_db(source_path=source_path)

    def fill_db(self, source_path: str, loader: BaseLoader=None):
        documents = []
        for file in os.listdir(source_path):
            if file.endswith('.pdf'):
                # TODO: OTHER FORMATS
                pdf_path = os.path.join(source_path, file)
                loader = PyPDFLoader(pdf_path)
                documents.extend(loader.load())
        chunked_documents = self.splitter.split_documents(documents)
        self.vector_store.add_documents(chunked_documents)
        logging.info(f'[RAG] Added {len(chunked_documents)} chunks to RAG\'s vector store. Total: {len(self.vector_store.get()["documents"])}')

    def run_retrieval(self, question: str, k: int = None) -> list[Document]:
        if not k:
            k = self.k
        retriever: VectorStoreRetriever = self.vector_store.as_retriever(search_kwargs={"k": k}) # todo: set another attr for the retriever? (to be customizable)
        return retriever.invoke(question)

    def create_prompt(self, history: list[Message], docs: list[Document], question: str, llm_prompt: str = None, num_context: int = None) -> PromptValue:
        if not llm_prompt:
            llm_prompt = self.llm_prompt
        if not num_context:
            num_context = self.num_context
        def format_docs(_docs):
            return "\n\n".join(doc.page_content for doc in _docs)

        conversation = [("human", llm_prompt)]
        if num_context > 0:
            conversation.extend(("human" if message.is_user else "ai", message.content) for message in history[-num_context:])
        conversation.append(("human", "Context: {context}\nQuestion: {question}\nAnswer:"))
        template = ChatPromptTemplate.from_messages(conversation)
        prompt_value = template.invoke(
            {
                "context": format_docs(docs),
                "question": question
            }
        )
        return prompt_value

    def run_rag(self, session: 'Session', message: str, llm_prompt: str = None, k: int = None, num_context: int = None):
        if not message:
            message = session.message
        docs: list[Document] = self.run_retrieval(question=message, k=k)
        prompt = self.create_prompt(history=session.chat_history, docs=docs, question=message, llm_prompt=llm_prompt, num_context=num_context)
        llm_response: AIMessage = self.llm.invoke(prompt)
        return RAGMessage(llm_name=self.llm.model_name, answer=llm_response.content, docs=docs)


class RAGMessage:

    def __init__(self, llm_name: str, answer: str, docs: list[Document]):
        self.llm_name: str = llm_name
        self.answer: str = answer
        self.docs: list[Document] = docs

    def to_dict(self):
        """Returns a dictionary containing the attributes of the RAGMessage object."""
        return {
            "llm_name": self.llm_name,
            "answer": self.answer,
            "docs": [{
                'content': doc.page_content,
                'metadata': doc.metadata,
            } for doc in self.docs]
        }
