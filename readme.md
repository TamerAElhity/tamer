# install the below dependencies
-----------------
Install the below 
* postgresql
	>* create database named "testdb" and install pgvector and PL/Python extensions
	>* change the db username and password in the rag2.py and uploaded_files2.py
	>* run process_files_in_directory.sql and augmented_response.sql to create PL/Python functions on testdb
* python3
* pip
* psycopg2 (pip install psycopg2)

	https://pypi.org/project/psycopg2/

* langchain (pip install langchain)

	https://pypi.org/project/langchain/

* langchain_text_splitters (pip install langchain-text-splitters)

	https://pypi.org/project/langchain-text-splitters/

* tiktoken (pip install tiktoken)

	https://pypi.org/project/tiktoken/

* pdfplumber
pip install pdfplumber

* streamlit (pip install streamlit)

	https://docs.streamlit.io/get-started/installation

* ollama

	>* Ollama Python Library: https://pypi.org/project/ollama/

	>* ollama service: https://ollama.com/download and/or https://github.com/ollama/ollama

	>* models to pull

	>>* mxbai-embed-large: ollama pull mxbai-embed-large
	
	>>* llama3.1: ollama pull llama3.1


Run the streamlit application

	streamlit run rag2.py
	streamlit run upload_files2.py