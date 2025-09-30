import os
from qdrant_client import QdrantClient
from langchain_community.vectorstores import Qdrant
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_community.llms import HuggingFacePipeline
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline, BitsAndBytesConfig

QDRANT_URL = os.getenv("QDRANT_URL")
COLLECTION_NAME = "cv-document-embeddings"
hf_token = os.getenv("HUGGINGFACE_HUB_TOKEN")

# Qdrant + embeddings
qdrant_client = QdrantClient(url=QDRANT_URL)
embeddings = SentenceTransformerEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
vectorstore = Qdrant(
    client=qdrant_client,
    collection_name=COLLECTION_NAME,
    embeddings=embeddings
)

model_name = "mistralai/Mistral-7B-Instruct-v0.2"

# Quantization config
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype="float16",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
)

# Tokenizer
tokenizer = AutoTokenizer.from_pretrained(
    model_name,
    token=hf_token,
    use_fast=True
)

# Model
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    device_map="auto",             # GPU if available
    quantization_config=bnb_config,
    token=hf_token
)

# Pipeline
pipe = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    max_new_tokens=512,
    do_sample=False,
    temperature=0.0
)
llm = HuggingFacePipeline(pipeline=pipe)

template = """
Use the following context to answer the question below. 
Answer in one concise paragraph. 
Do NOT include the context text in your answer. 
If the answer is unknown, say "I don't know".

Context:
{context}

Question:
{question}

Answer:
"""

qa_prompt = PromptTemplate(
    input_variables=["context", "question"],
    template=template
)

retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=retriever,
    chain_type_kwargs={"prompt": qa_prompt}
)

def answer_question(question: str):
    return qa_chain.run(question)
