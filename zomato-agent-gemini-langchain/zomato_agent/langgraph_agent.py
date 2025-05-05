from langgraph.graph import END, START, StateGraph
from . import OverallState, InputState, OutputState
from typing import Literal
from .guardrails import guardrails
from .parameter_based_agent.generate_database_records import generate_database_records
from .general_query_agent.generate_cypher import generate_cypher
from .general_query_agent.validate_cypher import validate_cypher
from .general_query_agent.correct_cypher import correct_cypher
from .general_query_agent.execute_cypher import execute_cypher


def guardrails_condition(
    state: OverallState,
) -> Literal["generate_database_records", '__end__']:
  if state.get("next_action") == "end":
    return END
  else: # next_action = "restaurant"
    return "generate_database_records"

def database_record_condition(
    state: OverallState,
) -> Literal["generate_cypher", '__end__']:
  if state.get("next_action") == "generate_cypher":
    return "generate_cypher"
  else: # next_action = "generate_final_answer"
    return END

def validate_cypher_condition(
    state: OverallState
) -> Literal["correct_cypher", "execute_cypher", '__end__']:
  if state.get("next_action") == "correct_cypher":
    return "correct_cypher"
  elif state.get("next_action") == "execute_cypher":
    return "execute_cypher"
  else: # next_action == "end"
    return END


langgraph = StateGraph(state_schema=OverallState, input=InputState, output=OutputState)
langgraph.add_node(guardrails)
langgraph.add_node(generate_database_records)
langgraph.add_node(generate_cypher)
langgraph.add_node(validate_cypher)
langgraph.add_node(correct_cypher)
langgraph.add_node(execute_cypher)


langgraph.add_edge(START, "guardrails")
langgraph.add_conditional_edges(
    "guardrails",
    guardrails_condition,
)
langgraph.add_conditional_edges(
    "generate_database_records",
    database_record_condition,
)

langgraph.add_edge("generate_cypher", "validate_cypher")

langgraph.add_conditional_edges(
    "validate_cypher",
    validate_cypher_condition,
)

langgraph.add_edge("correct_cypher", "validate_cypher")
langgraph.add_edge("execute_cypher", END)

langgraph = langgraph.compile()
