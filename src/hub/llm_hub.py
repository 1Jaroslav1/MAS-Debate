from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mistralai import ChatMistralAI
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

gpt_4o_mini = ChatOpenAI(model="gpt-4o-mini")

gemini_3_flash = ChatGoogleGenerativeAI(model="gemini-3-flash-preview")
mistral = ChatMistralAI(model="mistral-large-latest")

def get_llm(model_name: str | None) -> ChatOpenAI:
    """Return a ChatOpenAI client for the given model name.

    Falls back to gpt-4o-mini if name is None/empty.
    """
    if model_name is None or str(model_name).strip() == "":
        return gpt_4o_mini
    return ChatOpenAI(model=model_name)
