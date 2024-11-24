from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import re
from urllib.parse import urlencode

import cloudscraper
import marko
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request
from openai import OpenAI

load_dotenv()

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@app.route("/")
def render_home():
    return render_template("page1.html")

@app.route("/form")
def form():
    return render_template("form.html")

@app.route("/display")
def display():
    ingredients = request.args.get("ingredients")
    instructions = request.args.get("instructions")
    name = request.args.get("name")
    checklist = request.args.get("checklist")
    save_ingredients = request.args.get("save_ingredients")
    save_instructions = request.args.get("save_instructions")
    serving = request.args.get("serving")
    return render_template(
        "display.html",
        ingredients=ingredients,
        instructions=instructions,
        name=name,
        checklist=checklist,
        save_ingredients=save_ingredients,
        save_instructions=save_instructions,
        serving=serving,
    )

@app.route("/recipe_submission", methods=["GET", "POST"])
def recipe_submission():
    if request.json and not request.json.get("recipeLink", None):
        ingredients_html = request.json.get("saved_ingredients")
        soup = BeautifulSoup(ingredients_html, "html.parser")
        instructions_html = request.json.get("saved_instructions")
        serving_size = request.json.get("servings")
        unwanted_ingredients = ", ".join(request.json.get("banned_ingredients"))
        response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=
            [
                {
                    "role": "system",
                    "content": "You're a chef and here is a recipe that you need to modify. You need to remove the following ingredients: " + unwanted_ingredients + ". You also need to adjust the recipe to serve " + serving_size + " people. Please make the necessary changes to the recipe. Thank you! " + ingredients_html + instructions_html
                },
                {
                    "role": "user",
                    "content": "Please produce a recipe according to the above guidelines. Please put it in the format of a recipe card with the name at the top. Please don't write anything except the recipe and the instructions. Thank you! Also, please make the title of the dish lowercase and use markdown to describe the list of ingredients (unordered list) and instructions (ordered list). Thanks!",
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

        final_output = ""
        for i, ingre in enumerate(ingredients_list_no_format):
            label = "'label" + str(i) + "'"
            a = f'<label for="ingredient{i}" class="hover:text-gray-500 p-4 rounded-lg bg-green max-w-fit border-2 border-green inline-block mr-2 my-2 cursor-pointer transition-colors duration-250" id={label} onclick="toggleStrikeThrough(event, {label})"><input type="checkbox" name="ingredient{i}" id="ingredient{i}" class="hidden">{ingre}</label>'
            final_output = final_output + a
        
        save_ingredient_values = '<input type="text" id="ingredientshtml" name="ingredientshtml" value="' + ingredients_list + '">'
        save_instruction_values = '<input type="text" id="instructionshtml" name="instructionshtml" value="' + instructions_list + '">'
        serving_size = str(serving_size)
        serving_size = f'<input class="bg-green p-4 mb-6 rounded-lg border-2 border-green" type="number" id="servings" name="servings" min="1" placeholder="number of servings" value="{serving_size}" required>'
    
        query_params = urlencode({
            "ingredients": ingredients_list,
            "instructions": instructions_list,
            "name": name_of_recipe,
            "checklist": final_output,
            "save_ingredients": save_ingredient_values,
            "save_instructions": save_instruction_values,
            "serving": serving_size,
        })
        return redirect(f"/display?{query_params}")
    
    recipe_url = request.json.get("recipeLink")
    number_of_people = request.json.get("servings")
    dietary_restrictions = request.json.get("dietaryRestrictions")
    
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
                "content": "Please produce a recipe according to the above guidelines. Please put it in the format of a recipe card. Please don't write anything except the recipe and the instructions. Thank you! Also, please make the title of the dish in lowercase and use markdown to describe the list of ingredients (unordered list) and instructions (ordered list). Thanks!",
            },
        ],
    )

    gpt_response = response.choices[0].message.content
    formatted_html = marko.convert(gpt_response)
    if "<ul>" in formatted_html:
        ingredients_list = formatted_html.split("<ul>")[1].split("</ul>")[0]
    if "<ol>" in formatted_html:
        instructions_list = formatted_html.split("<ol>")[1].split("</ol>")[0]
    name_of_recipe = formatted_html.split("\n")[0]
    name_of_recipe = re.sub(r"<[^>]+>", "", name_of_recipe)

    soup = BeautifulSoup(ingredients_list, "html.parser")
    ingredients_list_no_format = [li.get_text(strip=True) for li in soup.find_all("li")]

    final_output = ""
    name = "ingredient"
    
    
    for i, ingre in enumerate(ingredients_list_no_format):
        label = "'label" + str(i) + "'"
        a = f'<label for="ingredient{i}" class="hover:text-gray-500 p-4 rounded-lg bg-green max-w-fit border-2 border-green inline-block mr-2 my-2 cursor-pointer transition-colors duration-250" id={label} onclick="toggleStrikeThrough(event, {label})"><input type="checkbox" name="ingredient{i}" id="ingredient{i}" class="hidden">{ingre}</label>'
        final_output = final_output + a

    save_ingredient_values = '<input type="text" id="ingredientshtml" name="ingredientshtml" value="' + ingredients_list + '">'
    save_instruction_values = '<input type="text" id="instructionshtml" name="instructionshtml" value="' + instructions_list + '">'
    serving_size = f'<input class="bg-green border-2 p-4 mb-6 border-green rounded-lg" type="number" id="servings" name="servings" min="1" placeholder="number of servings" value="{str(number_of_people)}" required>'
    query_params = urlencode({
            "ingredients": ingredients_list,
            "instructions": instructions_list,
            "name": name_of_recipe,
            "checklist": final_output,
            "save_ingredients": save_ingredient_values,
            "save_instructions": save_instruction_values,
            "serving": serving_size,
        })
    return redirect(f"/display?{query_params}")
if __name__ == "__main__":
    app.run(debug=True, port=8080)
