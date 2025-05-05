FROM python:3.12-slim

WORKDIR /app

# Copy requirements.txt from zomato_agent folder
COPY zomato_agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire zomato_agent folder into /app/zomato_agent
COPY zomato_agent ./zomato_agent

EXPOSE 8080

CMD ["uvicorn", "zomato_agent.app:app", "--host", "0.0.0.0", "--port", "8080"]
