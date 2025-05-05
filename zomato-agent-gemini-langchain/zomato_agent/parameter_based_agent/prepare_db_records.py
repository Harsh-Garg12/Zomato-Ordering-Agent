from functools import reduce
import pandas as pd
import numpy as np
import re

list_of_keys = ['restaurant', 'restaurant_score', 'zomato_page', 'restaurant_image_url', 'delivery_rating', 'dining_rating', 'deliverables', 'phone_number',
                'address', 'food_name', 'food_type', 'bestseller', 'price', 'quantity', 'food_rating', 'description', 'food_image_url', 'similarity_score']

async def sort_final_df(final_df):
    # 1) Count non‑null restaurant_* families
    restaurant_cols = [c for c in final_df.columns if re.match(r'restaurant_\d+$', c)]
    restaurant_count = final_df[restaurant_cols].notna().sum(axis=1)

    # 2) Compute average similarity_score_* per row (if any such columns exist)
    sim_cols = [c for c in final_df.columns if re.match(r'similarity_score_\d+$', c)]
    if sim_cols:
        sim_mean = final_df[sim_cols].mean(axis=1, skipna=True)
    else:
        # no columns → all zeros so they sort to bottom
        sim_mean = pd.Series(0, index=final_df.index)

    # 3) Compute average restaurant_score_* per row (if any exist)
    score_cols = [c for c in final_df.columns if re.match(r'restaurant_score_\d+$', c)]
    if score_cols:
        score_mean = final_df[score_cols].mean(axis=1, skipna=True)
    else:
        score_mean = pd.Series(0, index=final_df.index)

    # 4) Attach these as temporary columns (optional) or sort via the Series directly
    final_df.loc[:, '_rest_count'] = restaurant_count
    final_df.loc[:, '_sim_mean']   = sim_mean
    final_df.loc[:, '_score_mean'] = score_mean

    # 5) Sort by the three keys, all descending
    final_df.sort_values(
        ['_rest_count', '_sim_mean', '_score_mean'],
        ascending=[False, False, False],
        inplace=True
    )

    # 6) Drop the helpers
    final_df.drop(columns=['_rest_count', '_sim_mean', '_score_mean'], inplace=True)
    final_df.reset_index(inplace=True, drop=True)

    return final_df

async def prepare_db_records(list_of_dataframe, params, n):
  output = []

  final_df = reduce(lambda left, right: pd.merge(left, right, on='restaurant_id', how='outer'), list_of_dataframe)

  final_df = final_df.drop_duplicates().copy()

  final_df = await sort_final_df(final_df)


  limit = params.get('limit', 1000)

  x = set(params.keys()) == set(['quantity', 'limit', 'food_price_filter'])
  x = x or set(params.keys()) == set(['quantity', 'limit', 'food_rating_filter'])
  x = x or set(params.keys()) == set(['quantity', 'limit', 'restaurant_rating_filter'])

  if not x and final_df.shape[0] > limit:
    final_df = final_df.head(limit)

  for _, row in final_df.iterrows():
    total_cost = 0
    avg_similarity_score = []
    deal = []
    for i in range(1, n+1):
      if pd.notna(row[f'restaurant_{i}']):
        deal_item = {}

        if f'price_{i}' in row and f'quantity_{i}' in row and row[f'quantity_{i}']:
          total_cost += row[f'price_{i}']*int(row[f'quantity_{i}'])

        if f'similarity_score_{i}' in row:
          avg_similarity_score.append(row[f'similarity_score_{i}'])
        elif f'restaurant_score_{i}' in row:
          avg_similarity_score.append(row[f'restaurant_score_{i}'])

        deal_item = {key: row[f'{key}_{i}'] for key in list_of_keys if f'{key}_{i}' in row}
        deal.append(deal_item)

    if avg_similarity_score:
      avg_similarity_score = round(float(np.mean(avg_similarity_score)), 3)


    data = {'deal': deal}
    if total_cost != 0:
        data['total_cost'] = total_cost
    if avg_similarity_score:
        data['avg_similarity_score'] = avg_similarity_score

    output.append(data)

  filter_flag = False

  if 'food_price_filter' in params:
    try:
      price_pfx = 1
      if params['food_price_filter'] == 'DESC':
        price_pfx = -1

      output.sort(
          key=lambda x: (-1 * len(x['deal']), -1 * x['avg_similarity_score'], price_pfx * x['total_cost']) if 'avg_similarity_score' in x else (-1 * len(x['deal']), price_pfx * x['total_cost'])
      )

      filter_flag = True
    except:
      pass

  elif 'food_rating_filter' in params:
    try:
      rating_pfx = 1
      default_value = 1e3
      if params['food_rating_filter'] == 'DESC':
        rating_pfx = -1
        default_value = 0

      output.sort(
          key = lambda x: (-1*len(x['deal']), -1*x['avg_similarity_score'], rating_pfx*(x['deal'][0]['food_rating'], default_value)) if 'avg_similarity_score' in x else (-1*len(x['deal']), rating_pfx*(x['deal'][0]['food_rating'], default_value))
      )

      filter_flag = True
    except:
      pass

  elif 'restaurant_rating_filter' in params:
    try:
      restaurant_rating_rating_pfx = 1
      default_value = 1e3
      if params['restaurant_rating_filter'] == 'DESC':
        restaurant_rating_rating_pfx = -1
        default_value = 0

      output.sort(
          key = lambda x: (-1*len(x['deal']), -1*x['avg_similarity_score'], restaurant_rating_rating_pfx*(x['deal'][0]['delivery_rating'], default_value)) if 'avg_similarity_score' in x else (-1*len(x['deal']), restaurant_rating_rating_pfx*(x['deal'][0]['delivery_rating'], default_value)),
      )
      filter_flag = True
    except:
      pass

  if not filter_flag:
    output.sort(
        key = lambda x: (-1*len(x['deal']), -1*x['avg_similarity_score']) if 'avg_similarity_score' in x else (-1*len(x['deal']))
    )


  del final_df

  if len(output)!=limit:
    output = output[:limit]

  return output