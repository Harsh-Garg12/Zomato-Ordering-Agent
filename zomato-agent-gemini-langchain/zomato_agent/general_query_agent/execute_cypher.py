from .. import OverallState, safe_query


NO_RESULT = "I couldn't find any relevant information in the database"

async def execute_cypher(state: OverallState) -> OverallState:
    """
    Executes the given Cypher statement.
    """

    # records = enhanced_graph.query(state.get("cypher_statement"))
    records = await safe_query(query=state.get("cypher_statement"))

    return {
        "database_records": records if records else NO_RESULT,
        "next_action": "end",
        "steps": ["execute_cypher"],
    }