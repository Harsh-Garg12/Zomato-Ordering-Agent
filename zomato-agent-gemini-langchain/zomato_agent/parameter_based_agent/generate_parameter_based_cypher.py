entity_cypher_map = {
    'delivery_rating': '''
      r.delivery_rating IS NOT NULL AND r.delivery_rating <> 'not_available'
      AND toFloatOrNull(r.delivery_rating) >= $delivery_rating
      ''',

    'phone_number': '''
      r.phone_no CONTAINS $phone_number
      ''',

    'address': '''
      toLower(r.address) CONTAINS $address
      ''',

    'deliverables': '''
      CALL db.index.fulltext.queryNodes('restaurant_deliverables_fulltext_index', $deliverables) YIELD node AS r, score AS restaurant_score
      ''',

    'name': '''
      ALL(pair IN $name WHERE
          (pair[1] = true AND toLower(r.name) CONTAINS toLower(pair[0]))
          OR
          (pair[1] = false AND NOT toLower(r.name) CONTAINS toLower(pair[0]))
      )
      ''',

    'food_scores': '''
      UNWIND $food_scores AS fs
      ''',

    'bestseller': '''
      f.bestseller = true
      ''',

    'type': '''
      f.type = $type
      ''',

    'food_rating': '''
      (f.rating IS NOT NULL AND f.rating <> 'not_available')
      AND toFloatOrNull(f.rating) >= $food_rating
      ''',

    'price': '''
      f.price <= $price + $tolerance
      '''
}

async def build_cypher_query(entity, search_query, params):
  cypher_query = '''
  '''
  x = set(params.keys()) == set(['limit', 'food_price_filter'])
  x = x or set(params.keys()) == set(['limit', 'food_rating_filter'])

  if entity.quantity and (x or search_query or any(key in ['price', 'type', 'food_rating', 'bestseller'] for key in params.keys())):
    params["quantity"] = entity.quantity

  if 'deliverables' in params:
    cypher_query += entity_cypher_map['deliverables'] + ' '

  if 'food_scores' in params:
    cypher_query += entity_cypher_map['food_scores'] + ' '
    cypher_query += 'MATCH (r:Restaurant)-[:DELIVERS]->(f:Food {id: fs.id})' + ' '
  elif 'quantity' in params:
    cypher_query += 'MATCH (r:Restaurant)-[:DELIVERS]->(f:Food)' + ' '
  else:
    cypher_query += 'MATCH (r:Restaurant)' + ' '

  where_cypher_query = ''''''

  list_of_param_keys_not_for_where_clause = ['deliverables', 'food_scores', 'quantity', 'tolerance', 'food_rating_filter', 'food_price_filter', 'restaurant_rating_filter', 'limit']

  for key in params.keys():
    if key not in list_of_param_keys_not_for_where_clause:
      if where_cypher_query:
        where_cypher_query += 'AND ' + entity_cypher_map[key] + ' '
      else:
        where_cypher_query += 'WHERE ' + entity_cypher_map[key] + ' '

  cypher_query += where_cypher_query + ' '

  return_cypher_query = '''
  '''
  if 'food_scores' in params and 'deliverables' in params:
    return_cypher_query = '''RETURN r.id AS restaurant_id,
                              r.name AS restaurant,
                              r.url  AS zomato_page,
                              r.delivery_rating AS delivery_rating,
                              f.name AS food_name,
                              f.bestseller AS bestseller,
                              f.price AS price,
                              f.type AS food_type,
                              coalesce($quantity, 1) AS quantity,
                              CASE
                              WHEN f.rating IS NOT NULL AND f.rating <> 'not_available' THEN f.rating
                              ELSE NULL
                              END AS food_rating,
                              f.desc AS description,
                              f.image_url AS food_image_url,
                              fs.score AS similarity_score,
                              restaurant_score
                            '''
  elif 'quantity' in params and 'deliverables' in params:
    return_cypher_query = '''RETURN r.id AS restaurant_id,
                              r.name AS restaurant,
                              r.url  AS zomato_page,
                              r.delivery_rating AS delivery_rating,
                              f.name AS food_name,
                              f.bestseller AS bestseller,
                              f.price AS price,
                              f.type AS food_type,
                              coalesce($quantity, 1) AS quantity,
                              CASE
                              WHEN f.rating IS NOT NULL AND f.rating <> 'not_available' THEN f.rating
                              ELSE NULL
                              END AS food_rating,
                              f.desc AS description,
                              f.image_url AS food_image_url,
                              restaurant_score
                            '''

  elif 'food_scores' in params:
    return_cypher_query = '''RETURN r.id AS restaurant_id,
                              r.name AS restaurant,
                              r.url AS zomato_page,
                              r.delivery_rating AS delivery_rating,
                              f.name AS food_name,
                              f.bestseller AS bestseller,
                              f.price AS price,
                              f.type AS food_type,
                              coalesce($quantity, 1) AS quantity,
                              CASE
                                WHEN f.rating IS NOT NULL AND f.rating <> 'not_available' THEN f.rating
                                ELSE NULL
                              END AS food_rating,
                              f.desc AS description,
                              f.image_url AS food_image_url,
                              fs.score AS similarity_score
                            '''
  elif 'quantity' in params:
    return_cypher_query = '''RETURN r.id AS restaurant_id,
                              r.name AS restaurant,
                              r.url AS zomato_page,
                              r.delivery_rating AS delivery_rating,
                              f.name AS food_name,
                              f.bestseller AS bestseller,
                              f.price AS price,
                              f.type AS food_type,
                              coalesce($quantity, 1) AS quantity,
                              CASE
                                WHEN f.rating IS NOT NULL AND f.rating <> 'not_available' THEN f.rating
                                ELSE NULL
                              END AS food_rating,
                              f.desc AS description,
                              f.image_url AS food_image_url
                            '''
  elif 'deliverables' in params:
    return_cypher_query = '''RETURN r.id AS restaurant_id,
                              r.name AS restaurant,
                              r.url AS zomato_page,
                              r.image_url AS restaurant_image_url,
                              CASE
                                WHEN r.delivery_rating IS NOT NULL AND r.delivery_rating <> 'not_available' THEN r.delivery_rating
                                ELSE NULL
                              END AS delivery_rating,
                              CASE
                                WHEN r.dining_rating IS NOT NULL AND r.dining_rating <> 'not_available' THEN r.dining_rating
                              ELSE NULL
                              END AS dining_rating,
                              r.deliverables AS deliverables,
                              r.phone_no AS phone_number,
                              r.address AS address,
                              restaurant_score
                            '''
  else:
    return_cypher_query = '''RETURN r.id AS restaurant_id,
                              r.name AS restaurant,
                              r.url AS zomato_page,
                              r.image_url AS restaurant_image_url,
                              CASE
                                WHEN r.delivery_rating IS NOT NULL AND r.delivery_rating <> 'not_available' THEN r.delivery_rating
                                ELSE NULL
                              END AS delivery_rating,
                              CASE
                                WHEN r.dining_rating IS NOT NULL AND r.dining_rating <> 'not_available' THEN r.dining_rating
                              ELSE NULL
                              END AS dining_rating,
                              r.deliverables AS deliverables,
                              r.phone_no AS phone_number,
                              r.address AS address
                            '''

  cypher_query += return_cypher_query

  return cypher_query