import requests
import json
from .models import CarDealer, DealerReview
from requests.auth import HTTPBasicAuth
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson import NaturalLanguageUnderstandingV1
from ibm_watson.natural_language_understanding_v1 import Features, SentimentOptions
import time


# Create a `get_request` to make HTTP GET requests
def get_request(url, **kwargs):

    # If argument contain API KEY
    api_key = kwargs.get("api_key")
    print("GET from {} ".format(url))

    try:
        if api_key:
            params = dict()
            params["text"] = kwargs["text"]
            params["version"] = kwargs["version"]
            params["features"] = kwargs["features"]
            params["return_analyzed_text"] = kwargs["return_analyzed_text"]
            response = requests.get(url, params=params, headers={'Content-Type': 'application/json'},
                                    auth=HTTPBasicAuth('apikey', api_key))
        else:
            # Call get method of requests library with URL and parameters
            response = requests.get(
                url, headers={'Content-Type': 'application/json'}, params=kwargs)
    except:
        # If any error occurs
        print("Network exception occurred")

    status_code = response.status_code
    print("With status {} ".format(status_code))
    json_data = json.loads(response.text)
    return json_data


# Create a `post_request` to make HTTP POST requests
def post_request(url, payload, **kwargs):
    print("------------------------------------------------------\n")
    print("restapis --- post_request kwargs ---", kwargs)
    print("------------------------------------------------------\n")
    print("POST to {} ".format(url))
    print("------------------------------------------------------\n")
    print("restapis --- post_request payload ---", payload)
    print("------------------------------------------------------\n")

    response = requests.post(url, params=kwargs, json=payload)
    status_code = response.status_code

    print("With status {} ".format(status_code))
    json_data = json.loads(response.text)
    return json_data


# Create a get_dealers_from_cf method to get dealers from a cloud function
def get_dealers_from_cf(url, **kwargs):
    results = []
    state = kwargs.get("state")
    if state:
        json_result = get_request(url, state=state)
    else:
        json_result = get_request(url)

    if json_result:
        # Get the row list in JSON as dealers
        print("------------------------------------------------------\n")
        print("restapis --- get_dealesr_from_cf --- Dealers", json_result)
        print("------------------------------------------------------\n")
        dealers = json_result

        for dealer in dealers:
            dealer_doc = dealer["doc"]
            dealer_obj = CarDealer(
                address=dealer_doc["address"],
                city=dealer_doc["city"],
                full_name=dealer_doc["full_name"],
                id=dealer_doc["id"],
                lat=dealer_doc["lat"],
                long=dealer_doc["long"],
                short_name=dealer_doc["short_name"],
                st=dealer_doc["st"],
                zip=dealer_doc["zip"])
            results.append(dealer_obj)

    return results


# Create a get_dealer_by_id_from_cf method to get dealers from the cloud function by dpecific parameter
def get_dealer_by_id_from_cf(url, id):
    json_result = get_request(url, id=id)
    print("------------------------------------------------------\n")
    print("restapis --- get_dealer_by_id_from_cf --- GET", json_result)
    print("------------------------------------------------------\n")

    if json_result:
        dealers = json_result

        dealer_doc = dealers[0]
        dealer_obj = CarDealer(address=dealer_doc["address"],
                               city=dealer_doc["city"], id=dealer_doc["id"],
                               lat=dealer_doc["lat"], long=dealer_doc["long"], full_name=dealer_doc[
                                   "full_name"], short_name=dealer_doc["short_name"], st=dealer_doc["st"],
                               zip=dealer_doc["zip"])

    return dealer_obj


# Create a get_dealer_reviews_from_cf method to get reviews by dealer id from a cloud function
def get_dealer_reviews_from_cf(url, **kwargs):
    results = []
    id = kwargs.get("id")
    if id:
        json_result = get_request(url, id=id)
    else:
        json_result = get_request(url)
    print("------------------------------------------------------\n")
    print("restapis --- get_dealer_reviews_from_cf --- json_results ---", json_result)
    print("------------------------------------------------------\n")
    if json_result:
        reviews = json_result["data"]["docs"]
        print("------------------------------------------------------\n")
        print("restapis --- get_dealer_reviews_from_cf --- json_results ---", reviews)
        print("------------------------------------------------------\n")
        for review in reviews:
            if review["purchase"]:
                review_obj = DealerReview(
                    dealership=review["dealership"],
                    name=review["name"],
                    purchase=review["purchase"],
                    review=review["review"],
                    purchase_date=review["purchase_date"],
                    car_make=review["car_make"],
                    car_model=review["car_model"],
                    car_year=review["car_year"],
                    sentiment=analyze_review_sentiments(review["review"]),
                    id=review['id']
                )
            else:
                review_obj = DealerReview(
                    dealership=review["dealership"],
                    name=review["name"],
                    purchase=review["purchase"],
                    review=review["review"],
                    purchase_date=None,
                    car_make=None,
                    car_model=None,
                    car_year=None,
                    sentiment=analyze_review_sentiments(review["review"]),
                    id=review['id']
                )

            print("------------------------------------------------------\n")
            print(
                "restapis --- get_dealer_reviews_from_cf --- review_obj.sentiment ---", review_obj.sentiment)
            print("------------------------------------------------------\n")
            results.append(review_obj)
    return results


# Create an `analyze_review_sentiments` method to call Watson NLU and analyze text
def analyze_review_sentiments(text):
    url = "https://api.us-south.natural-language-understanding.watson.cloud.ibm.com/instances/b580571e-dc5f-4057-9c7b-47b69ad7640a"
    api_key = "XrCQufGwS5JWH9IkWCNBJxuNgDD5jorJze3uKAj6MKve"
    authenticator = IAMAuthenticator(api_key)
    natural_language_understanding = NaturalLanguageUnderstandingV1(
        version='2021-08-01', authenticator=authenticator)
    natural_language_understanding.set_service_url(url)

    response = natural_language_understanding.analyze( text=text,features=Features(sentiment=SentimentOptions())).get_result()
    #label=json.dumps(response, indent=2)
    label = response['sentiment']['document']['label']

    print("------------------------------------------------------\n")
    print("restapis --- analyze_review_sentiments --- label ---", label)
    print("------------------------------------------------------\n")
    return label
