
# 🍽️ Zomato Ordering Agent

A prototype **GraphRAG-based food ordering assistant** built using **Gemini 2.5 Flash**, **Neo4j AuraDB**, **LangChain**, and **LangGraph**. It enables users to place food orders conversationally by querying a knowledge graph of restaurants and dishes from the NCR region.

![diagram-export-5-5-2025-5_58_19-PM](https://github.com/user-attachments/assets/9b4845a1-5ece-498f-8c62-6265099e47cf)

---

![Screenshot 2025-05-05 173813](https://github.com/user-attachments/assets/9015076f-7d0c-4e99-be4f-10dddcc4ca38)

---

## 🚀 Live Demo

Try it out here: [Zomato Ordering Agent on Hugging Face Spaces](https://huggingface.co/spaces/Harshgarg12/zomato-ai-agent)

---

## 🧠 Project Overview

- **LLM**: Gemini 2.5 Flash (used for few-shot prompting & entity extraction)
- **Database**: Neo4j AuraDB (stores restaurants, food items, and their metadata as nodes & relationships)
- **Frameworks**: LangChain, LangGraph
- **Frontend**: Gradio SDK
- **Deployment**: GCP Cloud Run + API Gateway

---

## 🛠️ Features

- Guardrails to allow only food-ordering-related queries.
- Entity extraction (food type, name, restaurant, rating, etc.) using FAISS + Pydantic + Gemini.
- Hybrid semantic + lexical search using Neo4j vector and keyword matching.
- Asynchronous Cypher generation and querying for each item.
- Context-aware food deal generation per user request.

---

## 📦 Repository Structure

```
.
├── zomato-agent-gemini-langchain/   # Core agent implementation
│   └── ...                          # (add relevant scripts here)
├── Zomato_Ordering_Agent.ipynb     # Notebook to explore or test components
└── README.md
```

---

## 📋 Usage

```bash
# Step into the agent directory
cd zomato-agent-gemini-langchain/

# Run the application
python -m zomato_agent.app
```

---

## 📉 Latency Optimization Highlights

- Reduced response time from **50-60s to 10-20s** through:
  - FAISS-based filtering of few-shot examples before prompting.
  - Asynchronous Cypher query execution.
  - Avoiding heavy `ORDER BY` and indexing frequently used properties in Neo4j.

---

## 📚 Dataset

Contains metadata of ~400 restaurants in the NCR region including:
- `restaurant_name`, `address`, `phone_number`, `delivery_rating`
- `food_name`, `type`, `rating`, `bestseller`, `price`, etc.

---

## 📎 License

This project is for research and educational purposes only.

---

## 💬 Feedback

If you try it out, feel free to share your feedback or raise issues!
