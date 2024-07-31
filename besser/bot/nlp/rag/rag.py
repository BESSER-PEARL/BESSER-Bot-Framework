import logging
import os
from typing import TYPE_CHECKING

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore, VectorStoreRetriever
from langchain_text_splitters import TextSplitter

from besser.bot.core.message import Message, MessageType
from besser.bot.nlp.llm.llm import LLM

if TYPE_CHECKING:
    from besser.bot.core.bot import Bot
    from besser.bot.core.session import Session
    from besser.bot.nlp.nlp_engine import NLPEngine


class RAG:

    DEFAULT_LLM_PROMPT = "You are an assistant for question-answering tasks. Based on the previous messages in the conversation (if provided), and additional context retrieved from a database (if provided), answer the user question. If you don't know the answer, just say that you don't know. Note that if the question refers to a previous message, you may have to ignore the context since it is retrieved from the database based only on the question (the retrieval does not take into account the previous messages). Use three sentences maximum and keep the answer concise"

    def __init__(self, bot: 'Bot', vector_store: VectorStore, splitter: TextSplitter, llm_name: str, llm_prompt: str = None, k: int = 4, num_previous_messages: int = 0):
        self._nlp_engine: 'NLPEngine' = bot.nlp_engine
        self.vector_store: VectorStore = vector_store
        self.splitter: TextSplitter = splitter
        self.llm_name: str = llm_name
        if not llm_prompt:
            llm_prompt = RAG.DEFAULT_LLM_PROMPT
        self.llm_prompt = llm_prompt
        self.k: int = k
        self.num_previous_messages: int = num_previous_messages
        self._nlp_engine._rag = self

    def load_pdfs(self, path: str):
        documents = []
        for file in os.listdir(path):
            if file.endswith('.pdf'):
                pdf_path = os.path.join(path, file)
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

    def create_prompt(self, history: list[Message], docs: list[Document], question: str, llm_prompt: str = None, num_previous_messages: int = None):
        if not llm_prompt:
            llm_prompt = self.llm_prompt
        if not num_previous_messages:
            num_previous_messages = self.num_previous_messages
        def format_docs(_docs):
            return "\n\n".join(doc.page_content for doc in _docs)

        result = [llm_prompt]
        if num_previous_messages > 0:
            for message in history[-(num_previous_messages + 1):-1]:
                if message.type == MessageType.RAG_ANSWER:
                    result.append(f'Assistant: {message.content["answer"]}')
                elif message.type == MessageType.STR:
                    result.append(f'{"User" if message.is_user else "Assistant"}: {message.content}')
        result.append(f'Context: {format_docs(docs)}')
        result.append(f'Question: {question}')
        result.append(f'Answer: ')
        return '\n\n'.join(result)

    def run(self, session: 'Session' = None, message: str = None, llm_prompt: str = None, llm_name: str = None, k: int = None, num_previous_messages: int = None):
        if not message and not session:
            raise ValueError('RAG Run: Must provide either a message or a session')
        if not llm_name:
            llm_name = self.llm_name
        if not message:
            message = session.message
        if not session:
            history = []
        else:
            history = session.chat_history
        docs: list[Document] = self.run_retrieval(question=message, k=k)
        prompt = self.create_prompt(history=history, docs=docs, question=message, llm_prompt=llm_prompt, num_previous_messages=num_previous_messages)
        llm: LLM = self._nlp_engine._llms[llm_name]
        llm_response: str = llm.predict(prompt)
        return RAGMessage(llm_name=llm_name, answer=llm_response, docs=docs)


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
