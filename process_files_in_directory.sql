CREATE OR REPLACE FUNCTION process_files_in_directory(
    dataset_name VARCHAR,
    directory_path VARCHAR,
	do_truncate BOOL
) RETURNS VOID AS $$

import os
import time

#***********************************************************
#***********************************************************
#*************Caching Python Libraries**********************
#****************Ollama, TextSplitter, PDFLoader************
#***********************************************************

last_checkpoint_time = time.time()
if 'cached_ollama' not in SD:
    try:
        import ollama
        SD['cached_ollama'] = ollama
        plpy.notice("ollama loaded and cached successfully.")
    except Exception as e:
        plpy.error(f"Failed to load model: {str(e)}")
		
if 'cached_RecursiveCharacterTextSplitter' not in SD:
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        SD['cached_RecursiveCharacterTextSplitter'] = RecursiveCharacterTextSplitter
        plpy.notice("RecursiveCharacterTextSplitter loaded and cached successfully.")
    except Exception as e:
        plpy.error(f"Failed to load model: {str(e)}")
if 'cached_PyPDFLoader' not in SD:
	try:
		from langchain.document_loaders import PyPDFLoader
		SD['cached_PyPDFLoader'] = PyPDFLoader
		plpy.notice("PyPDFLoader loaded and cached successfully.")
	except Exception as e:
		plpy.error(f"Failed to load model: {str(e)}")

plpy.notice(f"Objects loading time: {time.time() - last_checkpoint_time:.2f} seconds.")
last_checkpoint_time = time.time()

model = SD['cached_ollama']
splitter = SD['cached_RecursiveCharacterTextSplitter']
pdf_loader = SD['cached_PyPDFLoader']

#***********************************************************
#***********************************************************
#*************Create / Drop Table/Index*********************
#***********************************************************
#***********************************************************

if(do_truncate):	#drop index, table
	plpy.execute(f"""DROP INDEX IF EXISTS {dataset_name}_vector_index;""")	
	plpy.execute(f"""drop table if exists {dataset_name}""")
#create table, index
plpy.execute(f"""create table IF NOT EXISTS {dataset_name} (id bigserial PRIMARY KEY, filename varchar(1024), content TEXT, embedding vector(1024));""")
plpy.execute(f"""CREATE INDEX if not exists {dataset_name}_vector_index ON {dataset_name} USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 256);""")
plpy.notice(f"table/index drop/create time: {time.time() - last_checkpoint_time:.2f} seconds.")
last_checkpoint_time = time.time()

#***********************************************************
#***********************************************************
#******prepare insert sql for storing data *****************
#**********in PGVector table********************************
#***********************************************************

insert_plan = plpy.prepare(f"""
    INSERT INTO {dataset_name} (content, embedding, filename)
    VALUES ($1, $2, $3)
""", ["text", "vector", "text"])

#***********************************************************
#***********************************************************
#******iterate and load files from the provided directory***
#***********************************************************
#***********************************************************

file_list = os.listdir(directory_path)
for filename in file_list:
	plpy.notice(f"process file name {filename}")
	file_path = os.path.join(directory_path, filename)
	if filename.lower().endswith('.pdf'):
		try:
			loader = pdf_loader(file_path)
			document = loader.load()
			plpy.notice(f"file loading time: {time.time() - last_checkpoint_time:.2f} seconds.")
			last_checkpoint_time = time.time()	

			#***********************************************************
			#***********************************************************
			#*************document chunking*****************************
			#***********************************************************
			#***********************************************************
			
			text_splitter = splitter.from_tiktoken_encoder(
				model_name="gpt-4",
				chunk_size=200,
				chunk_overlap=20,
			)
			chunks = text_splitter.split_documents(document)
			plpy.notice(f"file splitting time: {time.time() - last_checkpoint_time:.2f} seconds.")
			last_checkpoint_time = time.time()
			for row in chunks:
				try:
					chunk=row.page_content.replace('\x00', '')

					#***********************************************************
					#***********************************************************
					#*************Generate and save embedding for each chunk****
					#**************in PGVector table ***************************
					#***********************************************************
					
					response = model.embeddings(model="mxbai-embed-large", prompt=chunk)
					embedding = response["embedding"]
					content_utf8 = chunk.encode('utf-8', 'ignore').decode('utf-8')
					plpy.execute(insert_plan, [content_utf8, embedding, filename])
				except Exception as e:
					plpy.warning(f"Failed to process chunk in file {filename}: {str(e)}")
		except Exception as e:
			plpy.warning(f"Failed to process file {filename}: {str(e)}")
		plpy.notice(f"chunks embedding generation and db insertion time: {time.time() - last_checkpoint_time:.2f} seconds.")
		last_checkpoint_time = time.time()
plpy.notice(f"Done: {time.time() - last_checkpoint_time:.2f} seconds.")
$$ LANGUAGE plpython3u;