from langchain_core.prompts import PromptTemplate
from langchain_core.messages import AIMessage
from src.hub import gpt_4o_mini
from langgraph.prebuilt import ToolNode
from src.hub import get_tavily_tool
from src.reasoning import knowledge_parser_node, Knowledge
from pydantic import BaseModel, Field
from typing import List, Optional
import json

tavily_tool = get_tavily_tool(max_results=1)
tools = [tavily_tool]
team_tools_node = ToolNode(tools)

class RetrievedArticle(BaseModel):
    title: str = Field(description="The headline or title of the article.")
    summary: str = Field(description="A brief summary of the article's content.")
    url: str = Field(description="The link to the article.")
    publication_date: Optional[str] = Field(
        None, description="Optional publication date of the article."
    )


class KnowledgeRetrievalOutput(BaseModel):
    search_queries: List[str] = Field(
        description="List of alternative search query strings generated."
    )
    retrieved_articles: List[RetrievedArticle] = Field(
        description="List of candidate articles with their structured details."
    )

class SearchQueryOutput(BaseModel):
    search_queries: List[str] = Field(
        description="List of search query strings."
    )


def knowledge_retrieval_node(domain: str, direction: str, prev_articles: List[str], domains: List[str], metrics: List[str]) -> Knowledge:
    raw_evidence_list = web_search_node(domain, direction, prev_articles)
    
    all_items = []
    for json_str in raw_evidence_list:
        items = json.loads(json_str)
        all_items.extend(items)

    urls     = [item["url"]     for item in all_items]
    contents = [item["content"] for item in all_items]

    raw_content = "".join(contents)
    knowledge: Knowledge = knowledge_parser_node().invoke({"domains": domains, "text": raw_content, "metrics": metrics})

    return knowledge



def web_search_node(domain: str, direction: str, prev_articles: List[str]) -> List:
    search_query_prompt = PromptTemplate(
        template="""
            You are a Web Search Agent. Based on the following parameters, generate at least two distinct and diverse search queries that will help retrieve fresh and unique articles in the domain "{domain}".
            Direction: "{direction}"
            Previously retrieved articles: {prev_articles}

            For "create_new_argument", focus on fresh insights, emerging trends, or alternative perspectives.
            For "strengthen_existing_argument", focus on obtaining new evidence or diverse supporting viewpoints.

            Make sure each query is phrased so it's unlikely to return articles from any URL in {prev_articles}.  
            Return **only** a JSON object with a single key `"search_queries"` whose value is a list of your query strings.
        """,
        input_variables=["domain", "direction", "prev_articles"]
    )
    
    search_query_chain = search_query_prompt | gpt_4o_mini.with_structured_output(SearchQueryOutput)

    search_query_chain_params = {
        "domain": domain,
        "direction": direction,
        "prev_articles": ", ".join(prev_articles) if prev_articles else "None"
    }

    query_output: SearchQueryOutput = search_query_chain.invoke(search_query_chain_params)

    search_queries = query_output.search_queries

    search_messages = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "tavily_search_results_json",
                "args": {"query": query},
                "id": f"tool_call_{idx}",
                "type": "tool_call",
            }
            for idx, query in enumerate(search_queries)
        ],
    )

    tool_results = team_tools_node.invoke({"messages": [search_messages]})

    return [msg.content for msg in tool_results.get("messages", [])]

# class KnowledgeRetrievalInput(BaseModel):
#     domain: str = Field(description="The specific domain for the knowledge retrieval (e.g., climate, economy).")
#     direction: str = Field(description='The retrieval direction: "create_new_argument" or "strengthen_existing_argument".')
#     prev_articles: List[str] = Field(default=[], description="List of identifiers or summaries of previously retrieved articles.")


# class RetrievedArticle(BaseModel):
#     title: str = Field(description="The headline or title of the article.")
#     summary: str = Field(description="A brief summary of the article's content.")
#     url: str = Field(description="A URL link to the article.")
#     publication_date: Optional[str] = Field(None, description="Optional publication date of the article.")


# class KnowledgeRetrievalOutput(BaseModel):
#     search_queries: List[str] = Field(description="List of alternative search query strings generated.")
#     retrieved_articles: List[RetrievedArticle] = Field(description="List of candidate article objects with relevant information.")


# def knowledge_retrieval_node() -> KnowledgeRetrievalOutput:
#     prompt = PromptTemplate(
#         template="""
#             You are a Knowledge Retrieval Node assigned to find up-to-date, relevant articles in the domain "{domain}". The ASP solver has directed your focus as follows:
#             - Direction: "{direction}"
#             - Previously retrieved articles (if any): {prev_articles}

#             Your task is to craft search queries that **ensure diversity and freshness**, even if the domain and direction remain unchanged across rounds. Follow these guidelines:

#             For "{direction}" = "create_new_argument":
#                 - Generate search queries that explore fresh insights, emerging trends, or alternative perspectives in "{domain}".
#                 - Incorporate variant keywords or synonyms (e.g., "novel insights", "emerging trends", "alternative viewpoints") and include the round identifier to vary the phrasing.
#                 - Avoid repeating search terms or topics that appear in previously retrieved articles.

#             For "{direction}" = "strengthen_existing_argument":
#                 - Generate search queries that find articles supporting the existing argument in "{domain}" while introducing a new supporting angle.
#                 - Use additional qualifiers (e.g., "new evidence", "diverse perspectives", "corroborative research") in your search query.
#                 - Ensure the content you retrieve provides a different emphasis than what is already present in previously retrieved articles.

#             Additional Instructions:
#                 - Provide at least two alternative search queries that differ in phrasing and keywords.
#                 - Summarize each candidate article with its URL.
#                 - Your search queries must purposefully avoid duplicating content found in previous rounds.

#             Proceed with generating your unique search queries and retrieving the article results accordingly.
#         """,
#         input_variables=["domain", "direction", "prev_articles"]
#     )
    
#     return prompt | gpt_4o_mini.with_structured_output(KnowledgeRetrievalOutput)
