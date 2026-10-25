from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
import logging
import json
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)

# Login
@csrf_exempt
def login_user(request):
    data = json.loads(request.body)
    username = data['userName']
    password = data['password']

    user = authenticate(username=username, password=password)
    response = {"userName": username}

    if user is not None:
        login(request, user)
        response = {"userName": username, "status": "Authenticated"}

    return JsonResponse(response)

# Logout
@csrf_exempt
def logout_request(request):
    logout(request)
    return JsonResponse({"status": "Logged out"})

# Registration
@csrf_exempt
def registration(request):
    if request.method == "POST":
        data = json.loads(request.body)

        username = data["userName"]
        password = data["password"]
        first_name = data["firstName"]
        last_name = data["lastName"]
        email = data["email"]

        if User.objects.filter(username=username).exists():
            return JsonResponse({"userName": username, "error": "Already Registered"})

        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email,
        )

        login(request, user)

        return JsonResponse({"userName": username, "status": "Registered"})

    return JsonResponse({"error": "Invalid Request"})

def getallcarmakes(request):
    from .models import CarMake

    makes = CarMake.objects.prefetch_related("models").all().order_by("name")
    data = []

    for make in makes:
        data.append({
            "id": make.id,
            "name": make.name,
            "description": make.description,
            "models": [
                {
                    "id": model.id,
                    "name": model.name,
                    "type": model.type,
                    "year": model.year,
                }
                for model in make.models.all().order_by("name", "year")
            ],
        })

    return JsonResponse(data, safe=False)
