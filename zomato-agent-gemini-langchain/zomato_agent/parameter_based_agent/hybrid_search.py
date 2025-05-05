import re
from langchain_neo4j import Neo4jVector
from .. import embedding_model

food_vector_index = Neo4jVector.from_existing_graph(
    embedding=embedding_model,
    index_name="food_embedding_index",             # vector index name
    keyword_index_name="food_fulltext_index",      # explicitly pass keyword index name
    search_type="hybrid",                          # hybrid search: vector + keyword
    node_label="Food",
    text_node_properties=["price", "bestseller", "name", "type", "desc", "rating", "category", "restaurant_name", "id"],
    embedding_node_property="embedding"
)


async def get_food_scores(search_query: str, passing_threshold:float):
  food_scores = []
  hybrid_search_output = food_vector_index.similarity_search_with_score(query=search_query, k=1000)

  for doc, score in hybrid_search_output:
      if score < passing_threshold:
          break
      match = re.search(r'id:\s*([a-f0-9\-]+)', doc.page_content)
      if match:
          node_id = match.group(1)
          food_scores.append({"id": node_id, "score": score})

  return food_scores
