from datasets import load_dataset
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings,ChatGoogleGenerativeAI
from app.config import GOOGLE_API_KEY
from langchain import hub
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough 

dataset = load_dataset("SnehaDeshmukh/IndianBailJudgments-1200")

docs = []

for split in dataset.keys():
    for row in dataset[split]:
        parts = [
            row.get("facts","").strip(),
            row.get("legal_issues","").strip(),
            row.get("judgment_reason","").strip(),
            row.get("summary","").strip(),
        ]

        text = "\n\n".join(x for x in parts if x)
        metadata = {"id":row.get("id"), "split":split}
        docs.append(Document(page_content=text, metadata=metadata))


text_splitter = RecursiveCharacterTextSplitter(chunk_size = 2000,
                                               chunk_overlap = 200)
splits = text_splitter.split_documents(docs)


# Create vector store
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=GOOGLE_API_KEY)
vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings)
retriever = vectorstore.as_retriever()

# Load RAG prompt
prompt = hub.pull("rlm/rag-prompt")

# LLM model
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0, google_api_key=GOOGLE_API_KEY)

# Formatting retrieved docs
def format_docs(docs):
    return "\n".join(doc.page_content for doc in docs)

# Create RAG chain
rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

def ask_question(question):
    return rag_chain.invoke(question)