from .entities import EntityInfoItem

async def get_search_query_and_params(entity: EntityInfoItem, tolerance: int)->dict:
    search_query = ""
    params = {}

    '''Restaurant_parameters'''
    if entity.restaurant_rating != "not_available":
      params["delivery_rating"] = entity.restaurant_rating

    if entity.restaurant_phone_number:
      params["phone_number"] = entity.restaurant_phone_number

    if entity.restaurant_address:
      params["address"] = entity.restaurant_address.lower()

    if entity.restaurant_deliverables:
      params["deliverables"] = entity.restaurant_deliverables.lower()

    '''Food_parameters'''

    if entity.flavour:
      search_query += entity.flavour.lower()

    if entity.food_name:
      food_name = entity.food_name.lower()

      if food_name not in ['food', 'dish']:
        if search_query != "":
          search_query += " " + food_name
        else:
          search_query += food_name

    if entity.bestseller=="true":
      if search_query != "":
        search_query += ", " + "bestseller: true"
      params["bestseller"] = "true"

    if entity.type_!="not_mentioned":
      if search_query != "":
        search_query += ", " + "type: " + entity.type_
      params["type"] = entity.type_

    if entity.food_rating!="not_available":
      if search_query != "":
        search_query += ", " + "rating: " + str(entity.food_rating)
      params["food_rating"] = entity.food_rating

    if entity.food_price!=0.0:
      if search_query != "":
        search_query += ", " + "price: " + str(entity.food_price)
      params["price"] = entity.food_price
      params["tolerance"] = tolerance

    if entity.restaurant_name_pair:
      restaurant_name_pair = entity.restaurant_name_pair

      restaurant_name_pair_list = []

      for pair in restaurant_name_pair:
        restaurant_name = pair.restaurant_name.lower()
        condition = pair.condition
        if restaurant_name != "zomato":
          if search_query != "" and condition:
            search_query += ", " + "restaurant_name: " + pair.restaurant_name
          restaurant_name_pair_list.append([restaurant_name, condition])

      if restaurant_name_pair_list:
        params["name"] = restaurant_name_pair_list


    if entity.limit!=0:
      params["limit"] = entity.limit

    if entity.order_filter:
      if entity.order_filter.food_rating_filter:
        params['food_rating_filter'] = entity.order_filter.food_rating_filter
      if entity.order_filter.food_price_filter:
        params['food_price_filter'] = entity.order_filter.food_price_filter
      if entity.order_filter.restaurant_rating_filter:
        params['restaurant_rating_filter'] = entity.order_filter.restaurant_rating_filter

    return search_query, params