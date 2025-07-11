import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from langchain_core.documents import Document 
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma 
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.config import GOOGLE_API_KEY
from langchain import hub 
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser


visited = set()

def crawl(url,base_url, depth=0,max_depth=5):
    if depth>max_depth or url in visited:
        return []
    
    print(f"Crawling: {url}")
    visited.add(url)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        )
    }

    try:
        response = requests.get(url,headers=headers,timeout=5)
        if response.status_code !=200:
            print(f"Failed ({response.status_code}): {url}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text(separator="\n",strip=True)
        doc = Document(page_content=text,metadata={'source':url})

        # Find internal Links 
        links = [
            urljoin(url, a['href'])
            for a in soup.find_all("a",href=True)
            if urlparse(urljoin(url, a['href'])).netloc == urlparse(base_url).netloc
        ]

        docs = [doc] 
        for link in links:
            docs.extend(crawl(link,base_url,depth+1,max_depth))
        return docs
    
    except Exception as e:
        print(f"Error: {e}")
        return []    
    

docs1 = crawl("https://github.com/pytorch",
              "https://github.com/pytorch",max_depth=2)

# Start Crawling 
docs2 = crawl("https://docs.pytorch.org/docs/stable/index.html",
              "https://docs.pytorch.org/docs/stable/index.html",max_depth=2)

docs = docs1 + docs2

text_splitter = RecursiveCharacterTextSplitter(chunk_size = 1000,
                                               chunk_overlap = 200)
splits = text_splitter.split_documents(docs)


embeddings = GoogleGenerativeAIEmbeddings(
    model="models/text-embedding-004",
    google_api_key= GOOGLE_API_KEY
)
vectorstore = Chroma.from_documents(documents=splits,
                                    embedding=embeddings)


retriever = vectorstore.as_retriever()


prompt = hub.pull("rlm/rag-prompt")


llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
    google_api_key =GOOGLE_API_KEY
)

def format_docs(docs):
    return "\n".join(doc.page_content for doc in docs)


rag_chain = ({"context":retriever | format_docs,
              "question":RunnablePassthrough()}
              | prompt 
              | llm 
              | StrOutputParser())

def ask_question(question):
    return rag_chain.invoke(question)