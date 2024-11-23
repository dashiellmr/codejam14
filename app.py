from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import re

import cloudscraper
import marko
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask
from flask import jsonify
from flask import render_template
from flask import request
from openai import OpenAI

load_dotenv()

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/")
def render_home():
    return render_template("form.html")

@app.route("/recipe_submission", methods=["POST"])
def recipe_submission():
    
    recipe_url = request.form.get("recipeLink")
    number_of_people = request.form.get("servings")
    dietary_restrictions = []
    if request.form.get('nutAllergy') == "on":
        dietary_restrictions.append("Nut Allergy")
    if request.form.get('glutenFree') == "on":
        dietary_restrictions.append("Gluten Free")
    if request.form.get('lactoseFree') == "on":
        dietary_restrictions.append("Lactose Free")
    if request.form.get('vegetarian') == "on":
        dietary_restrictions.append("Vegetarian")
    if request.form.get('vegan') == "on":
        dietary_restrictions.append("Vegan")

    print(recipe_url)
    print(number_of_people)

    if "otherAllergy" in request.form:
        other_allergy = request.form.get('otherAllergyText', '').strip()
        if other_allergy:
            dietary_restrictions.append(other_allergy)

    print(dietary_restrictions)
    
    website_data = cloudscraper.create_scraper().get(recipe_url).text
    soup = BeautifulSoup(website_data, "html.parser")
    ingredients, instructions = soup.find(
        "div", class_=re.compile(r".*ingredients.*")
    ), soup.find("div", class_=re.compile(r".*instructions.*"))

    cleaned_html = "".join([str(ingredients), str(instructions)])

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": f"Here is a set of data for a website relating to cooking recipes, I would like you to find the recipe that is involved and update the recipe to match the preferences of the user. There are dietary restricts that must be followed in the updated recipe: {dietary_restrictions}. Additionally, you will need to make the recipe ratios work for the given number of people: {number_of_people}. Thank you! {cleaned_html}",
            },
            {
                "role": "user",
                "content": "Please produce a recipe according to the above guidelines. Please put it in the format of a recipe card. Please don't write anything except the recipe and the instructions. Thank you!",
            },
        ],
    )

    gpt_response = response.choices[0].message.content
    formatted_html = marko.convert(gpt_response)
    ingredients_list = formatted_html.split("<ul>")[1].split("</ul>")[0]
    instructions_list = formatted_html.split("<ol>")[1].split("</ol>")[0]
    name_of_recipe = formatted_html.split("\n")[0]
    name_of_recipe = re.sub(r"<[^>]+>", "", name_of_recipe)

    return render_template("display.html", ingredients=ingredients_list, instructions=instructions_list, name=name_of_recipe)

@app.route("/change_recipe")
def change_recipe():
    return render_template("change.html")

if __name__ == "__main__":
    app.run(debug=True, port=8080)
