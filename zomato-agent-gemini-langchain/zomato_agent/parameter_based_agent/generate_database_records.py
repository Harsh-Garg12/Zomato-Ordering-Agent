import pandas as pd
from .entities import get_entities
from .hybrid_search import get_food_scores
from .. import safe_query
from .search_query_params import get_search_query_and_params
from .prepare_db_records import prepare_db_records
from .generate_parameter_based_cypher import build_cypher_query
import asyncio

async def process_entity(entity, tolerance, passing_threshold, index):
    search_query, params = await get_search_query_and_params(entity, tolerance)

    food_scores = []
    if search_query:
        food_scores = await get_food_scores(search_query, passing_threshold)

    if food_scores:
        params["food_scores"] = food_scores

    # Build Cypher query (same as your existing logic)
    cypher_query = await build_cypher_query(entity, search_query, params)

    result = await safe_query(query=cypher_query, params=params)

    if result:
        temp_df = pd.DataFrame(result)
        temp_df.rename(columns=lambda x: f"{x}_{index}" if x != 'restaurant_id' else x, inplace=True)
        return (temp_df, params)

    return None

async def generate_database_records(state):
    entities = await get_entities(question=state.get('question'))
    tolerance = 10
    passing_threshold = state.get('passing_threshold', 0.98)

    tasks = [
        process_entity(entity, tolerance, passing_threshold, i + 1)
        for i, entity in enumerate(entities.order_info)
    ]

    results = await asyncio.gather(*tasks)

    list_of_dataframe = [res[0] for res in results if res is not None]
    if not list_of_dataframe:
      return {
          'next_action': 'generate_cypher',
          'steps': ['extract_entities', 'no_parameter_found', 'go_for_general_query_agent']
      }

    params = results[-1][1] if results[-1] is not None else {}

    output = await prepare_db_records(list_of_dataframe, params=params, n=len(list_of_dataframe))
    return {
        'next_action': 'generate_final_answer',
        'database_records': output,
        'steps': ['extract_entities', 'generate_parameter_based_cypher_query', 'execute_queries', 'generate_database_records']
    }
