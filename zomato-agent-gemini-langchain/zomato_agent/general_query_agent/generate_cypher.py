import os
import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_neo4j import Neo4jVector
from .. import embedding_model, llm, graph_schema, OverallState


CURRENT_DIR = os.path.dirname(__file__)
file_path = os.path.join(CURRENT_DIR, 'fewshot_examples_cypher_queries.json')

with open(file_path, 'r') as f:
    examples = json.load(f)

example_selector = SemanticSimilarityExampleSelector.from_examples(
    examples,
    embedding_model,
    Neo4jVector,
    k=5,
    input_keys=["question"]
)

text2cypher_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            (
                "Given an input question, convert it to a Cypher query. No pre-amble."
                "Do not wrap the response in any backticks or anything else. Respond with a Cypher statement only!"
            ),
        ),
        (
            "human",
            (
                """You are a Neo4j expert. Given an input question, create a syntactically correct Cypher query to run.

FOLLOWING TWO POINTS ARE VERY IMPORTANT: 

1. Do not wrap the response in any backticks or anything else. Respond with a Cypher statement only! Be consistent with the return result.

2. If the question demand food listing then always ensure that the cypher query must always return retaurant, zomato_page, food_name, bestseller, price, food_type, food_rating, description, food_image_url as present in the examples.

3. If you require to use WHERE clause for restaurant name i.e., r.name in cypher query, then always use like this way: toLower(r.name) CONTAINS <name_in_lowercase> OR NOT toLower(r.name) CONTAINS <name_in_lowercase>

Here is the schema information
{schema}

Below are a number of examples of questions and their corresponding Cypher queries.

{fewshot_examples}

User input: {question}
Cypher query:"""
            ),
        ),
    ]
)

text2cypher_chain = text2cypher_prompt | llm | StrOutputParser()

async def generate_cypher(state: OverallState) -> OverallState:
    """
    Generates a cypher statement based on the provided schema and user input
    """

    NL = '\n'
    fewshot_examples = (NL*2).join(
        [
            f"Question: {el['question']}{NL}Cypher:{el['query']}"
            for el in example_selector.select_examples(
                {"question": state.get("question")}
            )
        ]
    )

    generated_cypher = await text2cypher_chain.ainvoke(
        {
            "question": state.get("question"),
            "fewshot_examples": fewshot_examples,
            "schema": graph_schema,
        }
    )

    return {"cypher_statement": generated_cypher, "steps": ["generate_cypher"]}