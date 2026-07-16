from langgraph_engine import app

result = app.invoke({"user_query": "Student details for ADMN20251144"})
print(result["response"])
