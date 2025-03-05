from langchain.text_splitter import MarkdownTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain.schema import Document
from bs4 import BeautifulSoup
import requests
import html2text
import os
from dotenv import load_dotenv
from together import Together

# Load environment variables
load_dotenv()

together_api_key = os.getenv("TOGETHER_API_KEY")
client = Together(api_key=together_api_key)

# Load embedding model
embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en")

# Function to call LLaMA model with retrieved context
def llama_generate_answer(context, user_input, max_tokens=512):
    prompt = f"Answer the following question based on the provided context.\n\nContext:\n{context}\n\nQuestion: {user_input}\n\nAnswer:"
    response = client.chat.completions.create(
                        model="meta-llama/Llama-Vision-Free",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=max_tokens
                )

    return response.choices[0].message.content

# Web scraping function
def webscraping(url):
    response = requests.get(url)
    if response.status_code == 500:
        print("Server error")
        return None, None
    
    soup = BeautifulSoup(response.content, 'html.parser')
    for script in soup(["script", "style"]):
        script.extract()
    
    html = str(soup)
    html2text_instance = html2text.HTML2Text()
    text = html2text_instance.handle(html)
    
    try:
        page_title = soup.title.string.strip()
    except:
        page_title = url.replace("https://", "").replace("http://", "").replace("/", "-")
    
    meta_description = soup.find("meta", attrs={"name": "description"})
    description = meta_description["content"] if meta_description else page_title
    metadata = {'title': page_title, 'url': url, 'description': description}
    
    return text, metadata

# Create or load vector store
def get_vectorstore(url):
    if os.path.exists("data/chroma"):
        return Chroma(
            collection_name="website_data",
            embedding_function=embeddings,
            persist_directory="data/chroma"
        )
    
    text, metadata = webscraping(url)
    if not text:
        raise ValueError("Failed to scrape the website.")
    
    doc_chunks = []
    text_splitter = MarkdownTextSplitter()
    chunks = text_splitter.split_text(text)
    for chunk in chunks:
        doc = Document(page_content=chunk, metadata=metadata)
        doc_chunks.append(doc)
    
    vector_store = Chroma(
        collection_name="website_data",
        embedding_function=embeddings,
        persist_directory="data/chroma"
    )
    
    vector_store.add_documents(doc_chunks)
    vector_store.persist()
    return vector_store

# Retrieve relevant context from vector store
def retrieve_context(vector_store, user_input, k=4):
    retriever = vector_store.as_retriever()
    docs = retriever.get_relevant_documents(user_input, k=k)
    context = "\n\n".join([doc.page_content for doc in docs])
    return context

# Get response based on retrieved context
def get_response(user_input):
    vector_store = Chroma(
        collection_name="website_data",
        embedding_function=embeddings,
        persist_directory="data/chroma"
    )
    context = retrieve_context(vector_store, user_input)
    response_text = llama_generate_answer(context, user_input)
    return response_text

# Setup function to initialize vector store
def setup():
    global vectors
    try:
        url = "https://www.wellsfargo.com/biz/checking/compare-checking-accounts/"
        vectors = get_vectorstore(url)
        print("Vector store successfully created.")
        return True
    except Exception as e:
        print(f"Error while processing the URL: {e}")
        return False
