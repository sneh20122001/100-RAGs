import arxiv
from langchain import hub 
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter  
from app.config import GOOGLE_API_KEY


search = arxiv.Search(
    query="cat:cs.AI",
    max_results=500,
    sort_by=arxiv.SortCriterion.SubmittedDate
)

docs = []
for result in search.results():
    metadata = {
        "title": result.title,
        "authors": ", ".join([author.name for author in result.authors]),
        "published": result.published.strftime("%Y-%m-%d"),
        "url": result.entry_id
    }
    content = result.summary.strip()
    doc = Document(page_content=content, metadata=metadata)
    docs.append(doc)


text_splitter = RecursiveCharacterTextSplitter(
    chunk_size = 2000,
    chunk_overlap = 200
)
splits = text_splitter.split_documents(docs)


# Create vector store
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=GOOGLE_API_KEY)
vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings)
retriever = vectorstore.as_retriever()

prompt = hub.pull("rlm/rag-prompt")

# LLM model
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0, google_api_key=GOOGLE_API_KEY)

def format_docs(docs):
    return "\n".join(doc.page_content for doc in docs)

rag_chain = (
    {'context':retriever | format_docs,"question":RunnablePassthrough()}
    | prompt
    | llm 
    | StrOutputParser()
)

def ask_question(question):
    return rag_chain.invoke(question)


