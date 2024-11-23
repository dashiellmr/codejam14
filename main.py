from openai import OpenAI
from flask import Flask, request, jsonify, render_template
from bs4 import BeautifulSoup
import requests as req
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

@app.route('/')
def home():
    return render_template('form.html')

@app.route('/recipe_submission', methods=['POST'])

@app.route('/recipe_submission', methods=['POST'])
def recipe_submission():
    data = request.get_json()

    recipe_link = data.get('url', '')
    dietary_restrictions = data.get('dietary_restrictions', [])
    number_of_people = data.get('number_of_people', '')

    print("Recipe Link:", recipe_link)
    print("Dietary Restrictions:", dietary_restrictions)
    print("Number of People:", number_of_people)

    website_data = BeautifulSoup(recipe_link, 'html.parser')
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",        
        messages=[
                    {   
                        "role": "system", 
                        "content": 
                        f"Here is a set of data for a website relating to cooking recipes, 
                        I would like you to find the recipe that is involved and update the recipe to match the preferences of the user. 
                        There are dietary restricts that must be followed in the updated recipe: {dietary_restrictions}.
                        Additionally, you will need to make the recipe ratios work for the given number of people: {number_of_people}.
                        Thank you!
                        {website_data}",
                    }, 
                    {
                        "role": "user",
                        "content": 
                        "Please produce a recipe according to the above guidelines. Please put it in the format of a recipe card.",
                    }
                ]
            )
    return jsonify(response)







