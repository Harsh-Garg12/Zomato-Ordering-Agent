from .. import OverallState, safe_query, graph_schema, graph_structured_schema, llm
from neo4j.exceptions import CypherSyntaxError
from typing import List, Optional
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_neo4j.chains.graph_qa.cypher_utils import CypherQueryCorrector, Schema


validate_cypher_system = """
You are a Cypher expert reviewing a statement written by a junior developer.
"""

validate_cypher_user = """You must check the following:
* Are there any syntax errors in the Cypher statement?
* Are there any missing or undefined variables in the Cypher statement?
* Are any node labels missing from the schema?
* Are any relationship types missing from the schema?
* Are any of the properties not included in the schema?
* Does the Cypher statement include enough information to answer the question?

Examples of good errors:
* Label (:Foo) does not exist, did you mean (:Bar)?
* Property bar does not exist for label Foo, did you mean baz?
* Relationship FOO does not exist, did you mean FOO_BAR?

Schema:
{schema}

The question is:
{question}

The Cypher statement is:
{cypher}

Make sure you don't make any mistakes!"""

validate_cypher_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            validate_cypher_system,
        ),
        (
            "human",
            (validate_cypher_user),
        ),
    ]
)

class Property(BaseModel):
    """
    Represents a filter condition based on a specific node property in a graph in a Cypher statement.
    """

    node_label: str = Field(
        description="The label of the node to which this property belongs."
    )

    property_key: str = Field(
        description="The key of the property being filtered."
    )

    property_value: str = Field(
        description="The value that the property is being matched against."
    )

class ValidateCypherOutput(BaseModel):
    """
    Represents the validation result of a Cypher query's output,
    including any errors and applied filters.
    """

    errors: Optional[List[str]] = Field(
        description="A list of syntax or semantical errors in the Cypher statement. Always explain the discrepancy between schema and Cypher statement"
    )

    filters: Optional[List[Property]] = Field(
        description="A list of property-based filters applied in the Cypher statement."
    )

validate_cypher_chain = validate_cypher_prompt | llm.with_structured_output(
    ValidateCypherOutput
)

# Cypher query corrector is experimental
corrector_schema = [
    Schema(el["start"], el["type"], el["end"])
    for el in graph_structured_schema.get("relationships")
]

cypher_query_corrector = CypherQueryCorrector(corrector_schema)

async def validate_cypher(state: OverallState) -> OverallState:
    """
    Validates the Cypher statements and maps any property values to the database.
    """
    errors = []
    mapping_errors = []

    try:
    #   enhanced_graph.query(f"EXPLAIN {state.get('cypher_statement')}")
        await safe_query(query=f"EXPLAIN {state.get('cypher_statement')}")
    except CypherSyntaxError as e:
      errors.append(e.message)

    # Experimental feature for correcting relationship directions
    corrected_cypher = cypher_query_corrector(state.get("cypher_statement"))
    if not corrected_cypher:
      errors.append("The generated Cypher statement doesn't fit the graph schema")
    if not corrected_cypher == state.get("cypher_statement"):
      print("Relationship direction was corrected")

    # Use LLM to find additional potential errors and get the mapping for values

    llm_output = await validate_cypher_chain.ainvoke(
        {
            "question": state.get("question"),
            "cypher": state.get("cypher_statement"),
            "schema": graph_schema,
        }
    )

    if llm_output.errors:
      errors.extend(llm_output.errors)

    if llm_output.filters:
      for filter in llm_output.filters:
        if (
            not [
                prop
                for prop in graph_structured_schema["node_props"][
                    filter.node_label
                ]
                if prop["property"] == filter.property_key
            ][0]["type"]
            == "STRING"
        ):
          continue

        # mapping = enhanced_graph.query(
        #     f"MATCH (n: {filter.node_label}) WHERE toLower(n. `{filter.property_key}`) = toLower($value) RETURN 'yes' LIMIT 1",
        #     {"value": filter.property_value},
        # )

        mapping = await safe_query(
           query=f"MATCH (n: {filter.node_label}) WHERE toLower(n. `{filter.property_key}`) = toLower($value) RETURN 'yes' LIMIT 1",
           params={"value": filter.property_value},
        )

        if not mapping:
          print(
              f"Missing value mapping for {filter.node_label} on property {filter.property_key} with value {filter.property_value}"
          )

          mapping_errors.append(
              f"Missing value mapping for {filter.node_label} on property {filter.property_key} with value {filter.property_value}"
          )

    if mapping_errors:
      next_action = "end"
    elif errors:
      next_action = "correct_cypher"
    else:
      next_action = "execute_cypher"


    return {
        "next_action": next_action,
        "cypher_statement": corrected_cypher,
        "cypher_errors": errors,
        "steps": ["validate_cypher"],
    }