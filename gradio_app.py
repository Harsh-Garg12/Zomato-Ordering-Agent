import time
import json
import os
import requests
import gradio as gr
from dotenv import load_dotenv

CURRENT_DIR = os.path.dirname(__file__)
file_path = os.path.join(CURRENT_DIR, '.env')

load_dotenv(dotenv_path=file_path)

VEG_SYMBOL = "<img src='https://gimgs2.nohat.cc/thumb/f/640/vegetarian-food-symbol-icon-non-veg-symbol-png--m2H7H7m2K9m2Z5A0.jpg' style='width: 15px; height: 15px; margin-right: 5px; vertical-align: middle; display: inline-block;' />"
NON_VEG_SYMBOL = "<img src='https://rukminim3.flixcart.com/image/850/1000/kzfvzww0/noodle/n/1/m/280-buldak-cream-carbonara-hot-chiken-flavor-ramen-140g-1pack-original-imagbg69ynhtw8h2.jpeg' style='width: 15px; height: 15px; margin-right: 5px; vertical-align: middle; display: inline-block;' />"


def format_response(database_records, result_count):
    formatted_output = ""
    list_of_output = []

    number_of_results_obtained = len(database_records)
    if isinstance(database_records, list):
        if number_of_results_obtained>result_count:
            database_records = database_records[:result_count]
    
        number_of_results_to_be_displayed = len(database_records)
        formatted_output += f"<div><b>1-{number_of_results_to_be_displayed} of over {number_of_results_obtained} results</b></div>"
    

    if isinstance(database_records, list):
        if all("deal" in record for record in database_records):  # Type 1 or Type 2
            for record in database_records:

                total_cost = record.get('total_cost', 'N/A')
                zomato_page = record.get('zomato_page', '#')
                restaurant = record.get("deal", [])[0].get("restaurant", "")

                if total_cost != 'N/A':
                    formatted_output += f"<div><h3>{restaurant} | total: ₹{round(total_cost, 2)} | visit: <a href='{zomato_page}' target='_blank'>zomato_page</a></h3></div>"

                for deal in record.get("deal", []):

                    if "food_name" in deal and "food_image_url" in deal:
                        food_type_symbol = VEG_SYMBOL if deal.get('food_type').lower() == 'veg' else NON_VEG_SYMBOL

                        bestseller_tag = ""
                        if deal.get("bestseller"):
                            bestseller_tag = "<div style='display:inline-block;padding:2px 6px;background-color:orange;color:white;border-radius:4px;font-size:10px;margin-left:5px;'>BESTSELLER</div>"

                        food_rating_tag = ""
                        
                        food_rating = deal.get('food_rating')

                        if food_rating and food_rating != 'not_available':
                            food_rating_tag = f"<div style='display:inline-block;padding:2px 6px;background-color:green;color:white;border-radius:4px;font-size:10px;margin-left:5px;'>{str(food_rating)}</div>"

                        formatted_output += f"""
                        <div style='display: flex; align-items: center; margin-bottom: 15px;'>
                            {f"<img src='{deal['food_image_url']}' style='width: 150px; height: 150px; object-fit: cover; margin-right: 20px; border-radius: 10px;' />" if deal.get('food_image_url') else ""}
                            <div style="display: flex; flex-direction: column; justify-content: center;">
                                <h4 style='margin:0; display: flex; align-items: center;'>{food_type_symbol}<span>{deal['food_name']}</span> {bestseller_tag} {food_rating_tag}</h4>
                                <p>₹{deal['price']} | qty: {deal.get('quantity', '1')}</p>
                                <p>{deal.get('description', 'No description available.')}</p>
                            </div>
                        </div>
                        """
                    else:
                        formatted_output += f"""
                        <div style='display: flex; align-items: center; margin-bottom: 15px;'>
                            {f"<img src='{deal['restaurant_image_url']}' style='width: 150px; height: 150px; object-fit: cover; margin-right: 20px; border-radius: 10px;' />" if deal.get('restaurant_image_url') else ""}
                            <div style="display: flex; flex-direction: column; justify-content: center;">
                                <h4>{deal['restaurant']}</h4>
                                <p><strong>Deliverables:</strong>{deal.get('deliverables', 'Deliverables not available.')}</p>
                                <p><strong>Address:</strong> {deal.get('address', 'No address provided')}</p>
                                <p><strong>Phone:</strong> {deal.get('phone_number', 'No phone number available')}</p>
                                <p><strong>Delivery Rating:</strong> {deal['delivery_rating']}</p>
                                <p><strong>Dining Rating:</strong> {deal['dining_rating']}</p>
                                <p><a href='{deal['zomato_page']}' target='_blank'>Visit Zomato Page</a></p>
                            </div>
                        </div>
                        <hr style='border: none; border-top: 1px solid #ccc; margin: 10px 0;' />
                        """

                formatted_output += """<hr style='border: none; border-top: 1px solid #ccc; margin: 10px 0;' />"""
                list_of_output.append(formatted_output)
                formatted_output = ""

        elif all("restaurant" in record for record in database_records):  # Type 3
            for record in database_records:
                if 'food_name' not in record:
                    formatted_output += f"""
                    <div style='display: flex; align-items: center; margin-bottom: 15px;'>
                        {f"<img src='{record['restaurant_image_url']}' style='width: 150px; height: 150px; object-fit: cover; margin-right: 20px; border-radius: 10px;' />" if record.get('restaurant_image_url') else ""}
                        <div style="display: flex; flex-direction: column; justify-content: center;">
                            <h4>{record['restaurant']}</h4>
                            <p><strong>Deliverables:</strong>{record.get('deliverables', 'Deliverables not available.')}</p>
                            <p><strong>Address:</strong> {record.get('address', 'No address provided')}</p>
                            <p><strong>Phone:</strong> {record.get('phone_number', 'No phone number available')}</p>
                            <p><strong>Delivery Rating:</strong> {record.get('delivery_rating', '')}</p>
                            <p><strong>Dining Rating:</strong> {record.get('dining_rating', '')}</p>
                            <p><a href='{record['zomato_page']}' target='_blank'>Visit Zomato Page</a></p>
                        </div>
                    </div>
                    <hr style='border: none; border-top: 1px solid #ccc; margin: 10px 0;' />
                    """
                else:
                    zomato_page = record.get('zomato_page', '')
                    restaurant = record.get('restaurant', '')

                    food_type_symbol = VEG_SYMBOL if record.get('food_type').lower() == 'veg' else NON_VEG_SYMBOL

                    if zomato_page and restaurant:
                        formatted_output += f"<div><h3>{(restaurant)} | visit: <a href='{zomato_page}' target='_blank'>zomato_page</a></h3></div>"

                    bestseller_tag = ""
                    if record.get("bestseller"):
                        bestseller_tag = "<div style='display:inline-block;padding:2px 6px;background-color:orange;color:white;border-radius:4px;font-size:10px;margin-left:5px;'>BESTSELLER</div>"

                    food_rating_tag = ""
                    
                    food_rating = record.get('food_rating')

                    if food_rating and food_rating != 'not_available':
                        food_rating_tag = f"<div style='display:inline-block;padding:2px 6px;background-color:green;color:white;border-radius:4px;font-size:10px;margin-left:5px;'>{str(food_rating)}</div>"

                    formatted_output += f"""
                    <div style='display: flex; align-items: center; margin-bottom: 15px;'>
                        {f"<img src='{record['food_image_url']}' style='width: 150px; height: 150px; object-fit: cover; margin-right: 20px; border-radius: 10px;' />" if record.get('food_image_url') else ""}
                        <div style="display: flex; flex-direction: column; justify-content: center;">
                            <h4 style='margin:0; display: flex; align-items: center;'>{food_type_symbol}<span>{record['food_name']}</span> {bestseller_tag} {food_rating_tag}</h4>
                            <p>₹{record['price']} | qty: {record.get('quantity', '1')}</p>
                            <p>{record.get('description', 'No description available.')}</p>
                        </div>
                    </div>
                    """
                formatted_output += """<hr style='border: none; border-top: 1px solid #ccc; margin: 10px 0;' />"""
                list_of_output.append(formatted_output)
                formatted_output = ""
                
    else:  # Type 4
        formatted_output = database_records

    if list_of_output:
        formatted_output = "".join(list_of_output)

    return formatted_output

def get_database_records(query, threshold):
    try:
        response = json.loads(requests.post(
            url='http://localhost:8080/query',
            json={
                "query": query,
                "threshold": threshold
            }
        ).text)
        
        database_records = response.get('database_records')
        return database_records
    except Exception as e:
        print(f"Request failed: {e}")
        return "Looks like there's some error while fetching the data for this query, please clear the input and try again with a new query."
    
def chatbot_wrapper(query, threshold, result_count):
    start_time = time.time()

    database_records = get_database_records(query=query, threshold=threshold)

    response = format_response(database_records, result_count)

    elapsed_time = round(time.time() - start_time, 2)
    return response, f"Execution time: {elapsed_time} seconds"

with gr.Blocks() as demo:
    gr.Markdown("""
    ## Zomato Ordering Agent
    Ask questions about food delivery and dining options.
    ### Responses may take up to 2 minutes, especially for large orders, complex queries, first-time requests, or after periods of inactivity..
    """, elem_id='markdown')

    # Inject custom CSS to control button colors and hover message
    gr.HTML("""
    <style>
    #submit-btn {
        background-color: #f97316 !important;
        color: white !important;
    }
    #submit-btn.processing {
        background-color: #e5e7eb !important;
        color: black !important;
    }
    #clear-btn {
        background-color: #e5e7eb !important;
        color: black !important;
    }
    #markdown {
        margin-bottom: -40px;
    }

    .textbox-container {
        margin-top: -10000px;
    }            
    .threshold-tooltip {
        position: relative;
        display: inline-block;
        cursor: pointer;
        margin-left: -15px;
    }

    .tooltip-text {
        visibility: hidden;
        opacity: 0;
        position: absolute;
        background-color: #f1f1f1;
        color: #000;
        padding: 6px 10px;
        border-radius: 6px;
        z-index: 9999;
        white-space: nowrap;
        top: 10%;
        left: 0;
        transform: translateY(5px);
        box-shadow: 0px 0px 6px rgba(0, 0, 0, 0.2);
        transition: opacity 0.3s;
        font-size: 12px;
    }
            
    .threshold-tooltip:hover .tooltip-text {
        visibility: visible;
        opacity: 1;
    }
    </style>
    """)

    query = gr.Textbox(label="query", lines=1, placeholder="Type your food query here...")

    with gr.Row():
        threshold = gr.Slider(
            label="Threshold",
            minimum=0.90,
            maximum=1.0,
            value=0.97,
            step=0.01,
            elem_id="threshold-slider"
        )

        gr.HTML("""
        <div class="threshold-tooltip">
            <i class="info-icon">ℹ️</i>
            <div class="tooltip-text">Reducing the threshold can yield more expected results but may increase latency</div>
        </div>
        """)
        
        result_count = gr.Slider(
            label="Result Count",
            minimum=10,
            maximum=200,
            value=60,
            step=1
        )

    with gr.Row():
        submit_btn = gr.Button("Submit", elem_id="submit-btn")
        clear_btn = gr.Button("Clear", elem_id="clear-btn")

    with gr.Row():
        gr.Examples(
            examples=[
                ["What's the top 10 most expensive dish at zomato?"],
                ["Mocha"],
                ["Mc aloo tikki burger"],
                ["My order: 1 - Kadai Paneer, 1 - Mix Veg, 6 - Roti or tandoori roti"],
                ["what's all restaurant out there which serves turkish food?"],
                ["Show me some a good deal for masala dosa with lassi."],
                ["Show me all the bestselling veg dishes."],
                ["what all italian restaurants are available near connaught place."],
                ["hey, show me a good deal for butter chicken with garlic naan."],
                ["show me a top 5 highest rated burrito."],
                ["Show me a good deal for a dal fry with roti under 300."],
                ["Show me the Veg menu of KFC?"],
                ["Show me all the restaurant who serves south indian food with their rating atleast 3.5."],
                ["Show me a top 5 highest rated sushi."],
                ["show me some options for dark chocolate cake."],
                ["Hey, show me a momos deal under 200."],
                ["Show me an option for veg thali with mango lassi under 300."],
                ["Show me a option for chicken burger, not from KFC."],
                ["Show me a top 1 highest rated cafe at zomato?"],
                ["Hey, I want to eat milk cake, can you show some options."],
                ["Show me the non-veg burgers from McDonald."]
            ],
            inputs=query
        )

    response_output = gr.HTML()
    time_display = gr.Textbox(label="Execution Time", interactive=False)

    def wrapped_callback(query, threshold, result_count):
        # Pass threshold and result_count to your backend as needed
        response, exec_time = chatbot_wrapper(query, threshold, result_count)
        return (
            response,
            exec_time,
            gr.update(interactive=True, value="Submit", elem_classes=[])
        )

    def on_submit(query):
        return gr.update(interactive=False, value="Processing...", elem_classes=["processing"])

    submit_btn.click(
        on_submit,
        inputs=[query],
        outputs=[submit_btn],
    ).then(
        wrapped_callback,
        inputs=[query, threshold, result_count],
        outputs=[response_output, time_display, submit_btn]
    )

    clear_btn.click(
        fn=lambda: ("", "", gr.update(interactive=True, value="Submit", elem_classes=[])),
        outputs=[query, response_output, submit_btn]
    )

demo.launch(share=True)