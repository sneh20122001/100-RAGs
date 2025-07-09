from langchain_community.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings 
from app.config import GOOGLE_API_KEY
from langchain import hub
from langchain_google_genai import ChatGoogleGenerativeAI 
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser


loader = DirectoryLoader("E:/Learning_project/006_misinfoRAG/covid_dataset", show_progress=True, use_multithreading=True)
docs = loader.load()


text_splitter = RecursiveCharacterTextSplitter(chunk_size = 2000,
                                               chunk_overlap = 200)
splits = text_splitter.split_documents(docs)


embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004",google_api_key=GOOGLE_API_KEY)  
vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings)


retriever = vectorstore.as_retriever()

prompt = hub.pull("rlm/rag-prompt")


llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
    google_api_key=GOOGLE_API_KEY
)

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)


def ask_question(question):
    return rag_chain.invoke(question)