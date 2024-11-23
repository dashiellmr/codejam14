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
    
    if not request.form.get("recipeLink"):
        ingredients_html = request.form.get("ingredientshtml")
        soup = BeautifulSoup(ingredients_html, "html.parser")
        ingredients_list_notformed = [li.get_text(strip=True) for li in soup.find_all("li")]

        instructions_html = request.form.get("instructionshtml")
        serving_size = request.form.get("servings")
        unwanted_ingredients = []

        for i, ingreds in enumerate(ingredients_list_notformed):
            if request.form.get('ingredient' + str(i)) == "on":
                unwanted_ingredients.append(ingreds)

        unwanted_ingredients = ", ".join(unwanted_ingredients)

        print(ingredients_html)
        print("\n")
        print(unwanted_ingredients)
        print("\n")
        print(instructions_html)
        print("\n")
        print(serving_size)


        response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=
            [
                {
                    "role": "system",
                    "content": "You're a chef and here is a recipe that you need to modify. You need to remove the following ingredients: " + unwanted_ingredients + ". You also need to adjust the recipe to serve " + serving_size + " people. Please make the necessary changes to the recipe. Thank you! " + ingredients_html + instructions_html,
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

        soup = BeautifulSoup(ingredients_list, "html.parser")
        ingredients_list_no_format = [li.get_text(strip=True) for li in soup.find_all("li")]

        label_start = '<label><input type="checkbox" name="'
        label_end = '</label>'
        final_output = ""
        name = "ingredient"
        for ind, ingre in enumerate(ingredients_list_no_format):
            final_output = final_output + label_start + name + str(ind) + '">' + ingre + label_end
    
        save_ingredient_values = '<input type="text" id="ingredientshtml" name="ingredientshtml" value="' + ingredients_list + '">'
        save_instruction_values = '<input type="text" id="instructionshtml" name="instructionshtml" value="' + instructions_list + '">'
        serving_size = '<input type="number" id="servings" name="servings" min="1" value="' + str(serving_size) + '">'
    
        return render_template("display.html", ingredients=ingredients_list, instructions=instructions_list, name=name_of_recipe, checklist=final_output, save_ingredients=save_ingredient_values, save_instructions=save_instruction_values, serving=serving_size)
    
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

    if "otherAllergy" in request.form:
        other_allergy = request.form.get('otherAllergyText', '').strip()
        if other_allergy:
            dietary_restrictions.append(other_allergy)
    
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

    soup = BeautifulSoup(ingredients_list, "html.parser")
    ingredients_list_no_format = [li.get_text(strip=True) for li in soup.find_all("li")]

    label_start = '<label><input type="checkbox" name="'
    label_end = '</label>'
    final_output = ""
    name = "ingredient"
    
    for ind, ingre in enumerate(ingredients_list_no_format):
        final_output = final_output + label_start + name + str(ind) + '">' + ingre + label_end

    save_ingredient_values = '<input type="text" id="ingredientshtml" name="ingredientshtml" value="' + ingredients_list + '">'
    save_instruction_values = '<input type="text" id="instructionshtml" name="instructionshtml" value="' + instructions_list + '">'
    serving_size = '<input type="number" id="servings" name="servings" min="1" value="' + str(number_of_people) + '">'

    return render_template("display.html", ingredients=ingredients_list, instructions=instructions_list, name=name_of_recipe, checklist=final_output, save_ingredients=save_ingredient_values, save_instructions=save_instruction_values, serving=serving_size)

if __name__ == "__main__":
    app.run(debug=True, port=8080)
