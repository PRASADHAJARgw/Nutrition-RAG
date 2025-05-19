import streamlit as st
from dotenv import load_dotenv
load_dotenv()
import google.generativeai as genai
import os
from langchain.schema import Document
from PyPDF2 import PdfReader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
import requests
import tempfile
st.set_page_config(layout="wide")
# ---- Frontend and user input ----
st.header(":orange[FuelFit 🌿 🍁] Fuel your body with what helps it flourish", divider="rainbow")
st.subheader("Nutrition Meets AI: Your Personalized Nutrition Assistant")

st.markdown("#### :blue[Enter Your Details]")
name = st.text_input("*Name*") 
age = st.number_input("*Age*", min_value=1, max_value=90)
weight = st.number_input("*Weight (in kg)*", min_value=1, max_value=200)
height = st.number_input("*Height (in cm)*", min_value=1, max_value=300)
gender = st.selectbox("*Gender*", ["Male", "Female", "Other"]) 
disease_options = [
    "Diabetes", "Hypertension", "Thyroid", "Heart Disease", "Asthma", "Cholesterol",
    "Depression", "Migraine", "Liver Disease", "Obesity", "Anemia", "Arthritis",
    "Kidney Disease", "None"
]
diseases = st.multiselect("*Any Diseases*", disease_options)

# ---- RAG Setup ----
genai.configure(api_key=os.getenv("GOOGLE_API_1"))
gemini_model = genai.GenerativeModel("gemini-2.0-flash")

@st.cache_resource(show_spinner="Loading Embedding Model...")
def embeddings():
    return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

embedding_model = embeddings()

@st.cache_resource(show_spinner="Processing PDF and Generating Embeddings")
def load_pdf_and_create_vectordb(pdf_path):
    raw_text = ""
    pdf = PdfReader(pdf_path)
    for page in pdf.pages:
        text = page.extract_text()
        if text:
            raw_text += text
    if not raw_text.strip():
        return None, None
    document = Document(page_content=raw_text)
    splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents([document])
    chunk_pieces = [chunk.page_content for chunk in chunks]
    vectordb = FAISS.from_texts(chunk_pieces, embedding_model)
    return vectordb, raw_text
def download_pdf(url):
    response = requests.get(url)
    response.raise_for_status()
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    temp.write(response.content)
    temp.close()
    return temp.name
# Path to your saved PDF file
PDF_PATH = "https://drive.google.com/uc?export=download&id=10NsLSVc5YTFpzujKv45wOhr2uFpF3IF9"  # <-- Change this to your actual PDF path
local_pdf_path = download_pdf(PDF_PATH)
vectordb, pdf_text = load_pdf_and_create_vectordb(local_pdf_path)

if vectordb is None:
    st.warning("No text could be extracted from the PDF. Please check the file.")
else:
    st.markdown("#### :blue[Generate a plan:]")

    col1, col2 = st.columns(2)
    with col1:
        diet_btn = st.button("Create Diet Chart")
    with col2:
        workout_btn = st.button("Create Workout Plan")


    # Handle Diet Chart generation
    if diet_btn:
        with st.spinner("Generating your personalized diet chart..."):
            retriever = vectordb.as_retriever()
            plan_query = f"Create a detailed, personalized diet chart for a person named {name}, age {age}, weight {weight}kg, height {height}cm, diseases: {', '.join(diseases) if diseases else 'None'},gender={gender}. Use the context below from the PDF for evidence-based recommendations."
            relevant_docs = retriever.get_relevant_documents(plan_query)
            context = "\n\n".join([doc.page_content for doc in relevant_docs])
            prompt = f'''You are a certified nutritionist. Use the context below to create a detailed, day-wise diet chart for the user."
context: {context}
user details: Name={name}, Age={age}, Weight={weight}kg, Height={height}cm, Diseases={', '.join(diseases) if diseases else 'None'},gender={gender}
Diet Chart:'''
            response = gemini_model.generate_content(prompt)
            st.markdown("**Personalized Diet Chart:**")
            st.write(response.text)

    # Handle Workout Plan generation
    if workout_btn:
        with st.spinner("Generating your personalized workout plan..."):
            retriever = vectordb.as_retriever()
            plan_query = f"Create a detailed, personalized workout plan for a person named {name}, age {age}, weight {weight}kg, height {height}cm, diseases: {', '.join(diseases) if diseases else 'None'},gender={gender}.Use the context below from the PDF for evidence-based recommendations."
            relevant_docs = retriever.get_relevant_documents(plan_query)
            context = "\n\n".join([doc.page_content for doc in relevant_docs])
            prompt = f'''You are a certified fitness coach. Use the context below to create a detailed, week-wise workout plan for the user."
context: {context}
user details: Name={name}, Age={age}, Weight={weight}kg, Height={height}cm, Diseases={', '.join(diseases) if diseases else 'None'},gender={gender}
Workout Plan:'''
            response = gemini_model.generate_content(prompt)
            st.markdown("**Personalized Workout Plan:**")
            st.write(response.text)
            
st.markdown("""
    <style>.footer {position: fixed;left: 0;bottom: 0;width: 100%;
        background: white;color:black;text-align: center;padding: 10px 0;
        z-index: 100;border-top: 1px solid #e6e6e6;}
    </style>
    <div class="footer">
        Made with ❤️ by Prasad Hajare | Powered by Avanya AI | Made in My BHARAT 
    </div>""",unsafe_allow_html=True
)