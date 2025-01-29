import PyPDF2
import io


def extract_text_from_pdf(uploaded_file):
    text = ""
    # Use BytesIO to handle the uploaded file correctly
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))

    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"

    return text

import openai

def summarize_text(text):
    client = openai.OpenAI()  # Use new OpenAI client
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": f"Summarize this text: {text}"}]
    )
    return response.choices[0].message.content


import requests


def get_harvard_citation(query):
    url = f"https://api.crossref.org/works?query={query}"
    response = requests.get(url).json()

    if "message" in response and "items" in response["message"]:
        first_result = response["message"]["items"][0]
        title = first_result.get("title", [""])[0]
        author = first_result.get("author", [{}])[0]
        year = first_result.get("issued", {}).get("date-parts", [[None]])[0][0]
        doi = first_result.get("DOI", "")

        citation = f"{author.get('family', 'Unknown')}, {year}. {title}. Available at: <https://doi.org/{doi}> [Accessed {year}]."
        return citation
    return "Citation not found"

def add_harvard_citations(text, sources):
    citations = [get_harvard_citation(source) for source in sources]
    return text + "\n\nReferences:\n" + "\n".join(citations)

def humanize_text(text):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": f"Rewrite this text in a more human-like, natural style: {text}"}]
    )
    return response["choices"][0]["message"]["content"]


from bs4 import BeautifulSoup
import requests


def check_plagiarism(text):
    query = "+".join(text.split()[:10])  # Search first 10 words
    url = f"https://www.google.com/search?q={query}"

    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)

    soup = BeautifulSoup(response.text, "html.parser")
    results = soup.find_all("div", class_="BNeawe vvjwJb AP7Wnd")

    return len(results) > 0  # True if similar content is found

def generate_essay(topic, summary, sources):
    prompt = f"""
    Write a well-structured academic essay on '{topic}' using Harvard-style citations. 
    Use the following key points:
    {summary}

    Ensure the writing style is human-like and plagiarism-free.
    """

    essay = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )["choices"][0]["message"]["content"]

    # Add citations
    final_essay = add_harvard_citations(essay, sources)

    # Humanize the text
    final_essay = humanize_text(final_essay)

    return final_essay


import streamlit as st

st.title("AI Research Assistant")

uploaded_file = st.file_uploader("Upload your research paper", type="pdf")

if uploaded_file:
    if uploaded_file is not None:
        text = extract_text_from_pdf(uploaded_file)
    summary = summarize_text(text)
    st.write("### Summary:")
    st.write(summary)

topic = st.text_input("Enter the essay topic")

if st.button("Generate Essay"):
    sources = ["climate change research", "AI impact on society"]  # Example references
    essay = generate_essay(topic, summary, sources)

    if check_plagiarism(essay):
        st.warning("Plagiarism detected! Try regenerating.")
    else:
        st.write("### Generated Essay:")
        st.write(essay)
