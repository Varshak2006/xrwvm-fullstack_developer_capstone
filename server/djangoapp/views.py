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

# Dealership and review integration
from .restapis import get_request, analyze_review_sentiments


def get_dealerships(request):
    try:
        state = request.GET.get("state")
        if state:
            dealerships = get_request(f"fetchDealers/{state}")
        else:
            dealerships = get_request("fetchDealers")

        return JsonResponse(dealerships, safe=False)
    except Exception as error:
        logger.exception("Unable to retrieve dealerships")
        return JsonResponse(
            {"error": "Unable to retrieve dealerships"},
            status=502,
        )


def get_dealer_reviews(request, dealer_id):
    try:
        reviews = get_request(f"fetchReviews/dealer/{dealer_id}")

        for review in reviews:
            try:
                result = analyze_review_sentiments(review.get("review", ""))
                review["sentiment"] = result.get("sentiment", "unknown")
            except Exception:
                logger.exception("Unable to analyze a review")
                review["sentiment"] = "unknown"

        return JsonResponse(reviews, safe=False)
    except Exception:
        logger.exception("Unable to retrieve dealer reviews")
        return JsonResponse(
            {"error": "Unable to retrieve dealer reviews"},
            status=502,
        )

# Submit a dealership review
@csrf_exempt
def add_review(request):
    if request.method != "POST":
        return JsonResponse(
            {"status": 405, "error": "POST method required"},
            status=405,
        )

    try:
        data = json.loads(request.body)

        required_fields = [
            "name",
            "dealership",
            "review",
            "purchase",
            "purchase_date",
            "car_make",
            "car_model",
            "car_year",
        ]

        if any(field not in data for field in required_fields):
            return JsonResponse(
                {"status": 400, "error": "Missing required fields"},
                status=400,
            )

        # Analyze the review sentiment before saving it.
        from .restapis import analyze_review_sentiments, post_review

        sentiment_result = analyze_review_sentiments(data["review"])
        data["sentiment"] = sentiment_result.get("sentiment", "unknown")

        # Save the review through the existing Node backend.
        post_review(data)

        return JsonResponse({"status": 200})

    except Exception:
        logger.exception("Unable to submit dealership review")
        return JsonResponse(
            {"status": 502, "error": "Unable to submit review"},
            status=502,
        )
