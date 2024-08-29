import streamlit as st
import pandas as pd
from io import StringIO
import pdfplumber
import ollama
import math

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_core.documents.base import Document
import os
import datetime;

import psycopg2
db_ip = st.text_input('dbip', '')

if len(db_ip)>0:
    conn = psycopg2.connect(
        user="postgres",
        password="edb",
        host=db_ip,
        port=5432,  # The port you exposed in docker-compose.yml
        database="testdb"
    
    )
    
    #st.write("start: ", datetime.datetime.now())
    dataset_name = st.text_input('Data Set Name', '')
    trancate = st.checkbox('Truncate')
    with st.form("my-form", clear_on_submit=True):
        uploaded_files = st.file_uploader("Choose a file", type="pdf", accept_multiple_files=True,)
        submitted = st.form_submit_button("Upload")
    
        if submitted and len(uploaded_files)>0 and len(dataset_name)>0 is not None:
            cur = conn.cursor()
            st.write("Uploading files:")
            for uploaded_file in uploaded_files:
                st.write(uploaded_file.name)
            if trancate:
                cur.execute("DROP TABLE if exists edb_"+dataset_name)
                cur.execute("CREATE TABLE if not exists edb_"+dataset_name+" (id bigserial PRIMARY KEY, filename varchar(1024), content TEXT, embedding vector(1024))")
                cur.execute("TRUNCATE table edb_"+dataset_name)
            for uploaded_file in uploaded_files:     
                my_bar = st.progress(0, text=uploaded_file.name + " chunking")
                with open(uploaded_file.name, mode='wb') as w:
                    w.write(uploaded_file.getvalue())
                if uploaded_file: # check if path is not None
                    loader = PyPDFLoader(uploaded_file.name)
                    document = loader.load()
                    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
                                    model_name="gpt-4",
                                    chunk_size=100,
                                    chunk_overlap=10,
                                )
                    chunks = text_splitter.split_documents(document)
                    #print(chunks[1])
                    #my_bar.progress(20, text=uploaded_file.name + " generating and storing vectors")
                    
                    
                    # store each document in a vector embedding database
                    
                    for i, row in enumerate(chunks):
                        my_bar.progress(math.floor(i/len(chunks)*100), text=uploaded_file.name +" ("+str(i)+"/"+ str(len(chunks)) + ") generating and storing vectors")
                        response = ollama.embeddings(model="mxbai-embed-large", prompt=row.page_content.replace('\x00',''))
                        embedding = response["embedding"]
                        #print("\r",i,"/",len(chunks), end='')
                        #print(embedding)
                        #print(row.page_content.replace('\x00',''))
                        #pdf_countries
                        cur.execute(
                            "INSERT INTO edb_"+dataset_name+" (content, embedding,filename) VALUES (%s, %s, %s)",
                            (row.page_content.replace('\x00',''), embedding, uploaded_file.name)
                            )
                    os.remove(uploaded_file.name)
            cur.close()
            conn.commit()
            #st.rerun()
            #st.write("done")