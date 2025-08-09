import locale
import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn import metrics
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render


def home(request):
    return render(request, "home.html")


def predict(request):
    return render(request, "predict.html")


def result(request):
    data = pd.read_csv("./108.csv")

    # Encode categorical variables
    city_mapping = {city: idx for idx, city in enumerate(data['City'].unique())}
    furnishing_mapping = {"Unfurnished": 0, "Semi-furnished": 1, "Fully furnished": 2}

    data['City'] = data['City'].map(city_mapping)
    data['Furnishing Status'] = data['Furnishing Status'].map(furnishing_mapping)

    X = data.drop(['Price'], axis=1)
    Y = data['Price']
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.24, random_state=42)
    model = LinearRegression()
    model.fit(X_train, Y_train)

    var1 = float(request.GET['J1'])  # Purchase Budget
    var2 = float(request.GET['J2'])  # House Age
    var3 = float(request.GET['J3'])  # BHK
    var4 = float(request.GET['J4'])  # Population
    city = request.GET['J5']         # City (string)
    furnishing = request.GET['J6']   # Furnishing Status (string)

    # Validate Purchase Budget based on BHK
    bhk_min_budget = {
        1: 1500000,
        1.5: 2200000,
        2: 2800000,
        2.5: 3400000,
        3: 4000000,
        3.5: 4600000,
        4: 5200000,
        4.5: 5800000,
        5: 6900000
    }

    min_required_budget = bhk_min_budget.get(var3, None)
    if min_required_budget is None or var1 < min_required_budget:
        error_message = "Enter valid amount in Purchase Budget"
        return render(request, "predict.html", {"result2": error_message})
    
    # Validate House Age
    if var2 < 0 or var2 > 15:
        error_message = "House Age must be between 0 and 15 years."
        return render(request, "predict.html", {"result2": error_message})

    # Encode city and furnishing status
    city_encoded = city_mapping.get(city, -1)  # default -1 if not found
    furnishing_encoded = furnishing_mapping.get(furnishing, -1)

    # Validate encoding
    if city_encoded == -1 or furnishing_encoded == -1:
        price = "Invalid city or furnishing status selected."
        return render(request, "predict.html", {"result2": price})

    # Predict
    features = np.array([var1, var2, var3, var4, city_encoded, 0]).reshape(1, -1)
    base_pred = model.predict(features)[0]

    # Adjust based on furnishing
    if furnishing == "Fully furnished":
        final_pred = base_pred + 300000
    elif furnishing == "Semi-furnished":
        final_pred = base_pred + 150000
    else:
        final_pred = base_pred

    pred = round(final_pred)

    locale.setlocale(locale.LC_ALL, 'en_IN.UTF-8')  # Set locale for Indian number formatting
    pred_Bharat = locale.format_string("%d", pred, grouping=True)
    if pred < 0:
        price = "You have entered invalid data"
    else:   
        price = "The Predicted Price is ₹" + pred_Bharat
        current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Save the prediction to a file
        with open("predictions.txt", "a") as file:
            file.write(f"{var1},{var2},{var3},{var4},{city},{furnishing},{pred},{current_date}\n")

    return render(request, "predict.html", {"result2": price})


def prediction_history(request):
    history = []
    try:
        with open("predictions.txt", "r") as file:
            lines = file.readlines()
            last_20 = lines[-20:]
            for line in last_20:
                parts = line.strip().split(',')
                if len(parts) == 8:
                    var1, var2, var3, var4, city, furnishing, pred, date = parts
                    try:
                        date_obj = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
                        date_1 = date_obj.strftime("%B %d, %Y at %I:%M %p")
                    except ValueError:
                        date_1 = date
                    history.append({
                        "budget": f"₹{var1}",
                        "age": f"{var2} years",
                        "bedrooms": var3,
                        "population": var4,
                        "city": city,
                        "furnishing_status": furnishing,
                        "prediction": f"₹{pred}",
                        "date": date_1
                    })
    except FileNotFoundError:
        history = []

    return render(request, "history.html", {"history": history})

