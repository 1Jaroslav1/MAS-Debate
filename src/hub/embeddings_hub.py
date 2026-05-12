from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

openai_text_embedding_3_small = OpenAIEmbeddings(model="text-embedding-3-small")
