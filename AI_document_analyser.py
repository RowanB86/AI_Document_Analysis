# -*- coding: utf-8 -*-
"""
Created on Wed Mar  5 22:59:51 2025

@author: RowanBarua
"""

import streamlit as st
import fitz
import openai
import time
import tiktoken

def count_tokens(text, model):
    # Load the encoding for the specified model
    encoding = tiktoken.encoding_for_model(model)
    
    # Encode the text and count tokens
    tokens = encoding.encode(text)
    return len(tokens)

if 'user_prompts' not in st.session_state:
    st.session_state.user_prompts = []
    
openai.api_key = st.secrets["openai"]["api_key"]

uploaded_files = st.file_uploader("Upload PDF documents to be scanned.", accept_multiple_files=True, type="pdf")

selected_model = st.selectbox("Select model",options=["gpt-4o","gpt-4o-mini","gpt-3.5-turbo"])

num_chars = int(st.text_input("Enter max number of characters of text to process at once" , value = "100000"))

overlap = int(st.text_input("Enter number of chars that each batch of text will overlap", value = "1000"))

system_prompt = st.text_input("Enter system prompt:", value="Your job is to summarise the uploaded documents to save the user having to read them in full.")

user_prompt = st.text_input("Enter user prompt (will be applied to each document): ", value="Summarise the contents of this document.") 
    
if st.button("Add user prompt"):
    
    if user_prompt not in st.session_state.user_prompts:
        st.session_state.user_prompts.append(user_prompt)
        
        
# Display each item with a delete button
for item in st.session_state.user_prompts:
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.write(item)
    with col2:
        if st.button("❌", key=item):
            st.session_state.user_prompts.remove(item)
            st.rerun()   
            
first_document_processed = False

if st.button("Summarise documents"):
    if uploaded_files:
        for file in uploaded_files:
            
            if first_document_processed:
                if doc_length > 80000:
                    st.write("Pausing for 1 minute to avoid exceeding rate limit.") 
                    time.sleep(60)                     

            doc = fitz.open(stream=file.read(), filetype="pdf")
            doc_text = "\n".join([page.get_text("text") for page in doc])
            doc_text = doc_text.strip()
            
            st.markdown(f"**Evaluation of Document {file.name}**")

            doc_length = len(doc_text)
            start_char = 0
            end_char = min(start_char + num_chars,doc_length)
             
            continue_processing = True
             
            text_block_num = 1
            
            while continue_processing:

                messages = [{"role": "system", "content": system_prompt}]
                for item in st.session_state.user_prompts:
                    messages += [{"role": "user", "content": item}]
                
                messages += [{"role": "user", "content": "This is the document you should base your answer(s) on: " + doc_text[start_char:end_char]}]
                response = openai.ChatCompletion.create(model=selected_model,messages=messages)
                doc_evaluation = response["choices"][0]["message"]["content"] 
                
                st.write("Text block :" + str(text_block_num))
                st.write(doc_evaluation)

                if end_char < doc_length:
                    start_char = max(0,end_char - overlap)
                    end_char = min(start_char + num_chars,doc_length)
                    st.write("Pausing for 1 minute to avoid exceeding rate limit.") 
                    time.sleep(60)                
                else:
                    chars_processed = doc_length
                    continue_processing = False
                    first_document_processed = True 
                
                
                text_block_num += 1
