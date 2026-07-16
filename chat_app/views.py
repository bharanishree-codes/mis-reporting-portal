from .langgraph_engine import graph
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json

@csrf_exempt
def gemini_chat(request):
    if request.method == "POST":
        data = json.loads(request.body)
        user_query = data.get("user_query", "")

        result = graph.invoke({"user_query": user_query})
        answer = result.get("final_answer", result.get("answer", "No response generated."))

        return JsonResponse({"answer": answer})

    return render(request, "chat_app/gemini_chat.html")
