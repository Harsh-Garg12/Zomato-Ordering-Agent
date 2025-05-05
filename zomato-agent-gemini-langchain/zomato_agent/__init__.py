import os
from dotenv import load_dotenv
from langchain_neo4j import Neo4jGraph
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from operator import add
from typing import Annotated, List
from typing_extensions import TypedDict
from functools import lru_cache
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


CURRENT_DIR = os.path.dirname(__file__)
file_path = os.path.join(CURRENT_DIR, '.env')

load_dotenv(dotenv_path=file_path)

# os.environ["NEO4J_URI"] = os.getenv("NEO4J_URI")
# os.environ["NEO4J_USERNAME"] = os.getenv("NEO4J_USERNAME")
# os.environ["NEO4J_PASSWORD"] = os.getenv("NEO4J_PASSWORD")
# os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY")

assert os.getenv("GEMINI_API_KEY"), "GEMINI_API_KEY not set in environment"
assert os.getenv("NEO4J_URI"), "NEO4J_URI not set in environment"
assert os.getenv("NEO4J_USERNAME"), "NEO4J_USERNAME not set in environment"
assert os.getenv("NEO4J_PASSWORD"), "NEO4J_PASSWORD not set in environment"

# @lru_cache
# def get_graph():
#   enhanced_graph = Neo4jGraph(enhanced_schema=True, timeout=600)
#   return enhanced_graph

enhanced_graph = Neo4jGraph(
  driver_config={
        'connection_acquisition_timeout': 30,
        'max_connection_pool_size': 50,
        'keep_alive': True,
        'max_connection_lifetime': 1800, 
        'connection_timeout': 10,
  },
)


graph_schema = enhanced_graph.schema
graph_structured_schema = enhanced_graph.structured_schema

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2))
async def safe_query(query, params=None):
    enhanced_graph._driver.verify_connectivity()

    if params:
      return enhanced_graph.query(
        query=query,
        params=params
      )
    else:
      return enhanced_graph.query(
        query=query
      )


# LLM_MODEL = "gemini-2.0-flash-001"
LLM_MODEL = "gemini-2.5-flash-preview-04-17"

llm = ChatGoogleGenerativeAI(
    model=LLM_MODEL,
    api_key=os.environ["GEMINI_API_KEY"],
    temperature=0,  # Deterministic output
    top_p=1.0       # Full probability distribution
)

EMBEDDING_MODEL = "models/embedding-001"

embedding_model = GoogleGenerativeAIEmbeddings(
      model=EMBEDDING_MODEL, task_type="semantic_similarity",
      google_api_key=os.getenv("GEMINI_API_KEY"),
    )


class InputState(TypedDict):
  question: str
  passing_threshold: float

class OverallState(TypedDict):
  question: str
  passing_threshold: float
  next_action: str
  cypher_statement: str
  cypher_errors: List[str]
  database_records: List[dict]
  steps: Annotated[List[str], add]

class OutputState(TypedDict):
  answer: str
  cypher_statement: str
  steps: List[str]
  database_records: List[dict]