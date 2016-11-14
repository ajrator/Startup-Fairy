"""
Serves all the routes for the application
"""
import json
import subprocess
# import requests
from os import listdir
from flask import Blueprint, Flask
from flask import render_template, abort, request
from flask_sqlalchemy import SQLAlchemy
from models import *
from collections import defaultdict
import string

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://sweteam:sweteamajmal@localhost/startupfairydb5"
db.init_app(app)

ALT_NAMES = {
    'financialorgs': 'Financial Organizations',
    'companies': 'Companies',
    'cities': 'Cities',
    'people': 'People'
}

@app.route('/')
@app.route('/index')
def index():
    """
    Serve the home/index page
    """
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return "LOl"

def format_query(query_string):
    '''
        Format the query string for search so that we can
        parse the tokens easily. Here we replace the "+"
        characters with spaces, and remove all punctuation.
    '''
    query_string = query_string.replace("+"," ")
    translator = str.maketrans({key: None for key in string.punctuation})
    print(query_string)
    return query_string.translate(translator)

@app.route('/search/<query_string>')
def search(query_string):
    query_string = format_query(query_string)
    query_words = set(query_string.split())
    # For the "and" results.
    and_model_to_words = defaultdict(lambda: defaultdict(set))
    # For the "or" results.
    or_model_to_words = defaultdict(lambda: defaultdict(set))
    # Map of the following form:
    # <model id, dictionary> where the dictionary is of the form:
    # <"type": "<model type>"
    # <"words">: "<words from our query that appear in this model>"
    for word in query_words:
        print(word)
        word_index = db.session.query(Index).filter_by(token = word).one()
        models = json.loads(word_index.models)
        if models is not None:
            for model in models:
                model_type = model["model"]
                model_id = model["id"]
                or_model_to_words[model_id]["type"] = model_type
                or_model_to_words[model_id]["words"].add(word_index.token)
    for key, value in or_model_to_words.items():
        # If this result contains ALL of the words in our search, add
        # it to the AND results.
        if query_words.issubset(value["words"]):
            and_model_to_words[key] = value
            # Cast words to list so that we can serialize with JSON.
            and_model_to_words[key]["words"] = list(and_model_to_words[key]["words"])
        value["words"] = list(value["words"])
    return json.dumps([and_model_to_words, or_model_to_words])

@app.route('/about')
def about():
    """
    Serve the about page
    """
    return render_template('about.html', alt_title='About')


@app.route('/category/<app_category>', methods=['GET'])
def category(app_category):
    print(app_category)
    """Render table template"""
    if app_category == 'people':
        data = api_people()
    elif app_category == 'cities':
        data = api_cities()
    elif app_category == 'companies':
        data = api_companies()
    elif app_category == 'financialorgs':
        data = api_financialorgs()
    else:
        print("Category does not exist")
        data = []
    return render_template('category.html',
                           alt_title=ALT_NAMES.get(app_category, None),
                           title=app_category, data=data)


@app.route('/category/<app_category>/<entity>', methods=['GET'])
def details(app_category, entity):
    """
    Serve the an entity's page
    """
    if app_category == 'people':
        data = api_people(entity)
    elif app_category == 'cities':
        data = api_cities()
    elif app_category == 'companies':
        data = api_companies()
    elif app_category == 'financialorgs':
        data = api_financialorgs(entity)
    else:
        print("Category does not exist")
        # data = []
    print (data)
    return render_template('details.html', data=json.loads(data), category=app_category)


@app.route('/api/people', methods=['GET'])
def api_people(entity=None):
    try:
        person_id = request.args.get('id')
        if entity is None and person_id is None:
            data = db.session.query(Person).all()
            return json.dumps(list(map(lambda d: d.dictionary(), data)))
        else:
            if entity is not None:
                data = db.session.query(Person).filter_by(
                    person_id=entity).one()
            else:
                data = db.session.query(Person).filter_by(
                    person_id=person_id).one()
            return json.dumps(data.dictionary())
    except:
        print("Get people failed")
        abort(404)


@app.route('/api/companies', methods=['GET'])
def api_companies(entity=None):
    try:
        company_id = request.args.get('id')
        if entity is None and company_id is None:
            data = db.session.query(Company).all()
            return json.dumps(list(map(lambda d: d.dictionary(), data)))
        else:
            if entity is not None:
                data = db.session.query(Company).filter_by(company_id=entity).one()
            else:
                data = db.session.query(Company).filter_by(
                    company_id=company_id).one()
            return json.dumps(data.dictionary())
    except:
        print("Get companies failed")
        abort(404)


@app.route('/api/financialorgs', methods=['GET'])
def api_financialorgs(entity=None):
    try:
        finorg_id = request.args.get('id')
        if entity is None and finorg_id is None:
            data = db.session.query(FinancialOrg).all()
            return json.dumps(list(map(lambda d: d.dictionary(), data)))
        else:
            if entity is not None:
                data = db.session.query(FinancialOrg).filter_by(
                    financial_org_id=entity).one()
            else:
                data = db.session.query(FinancialOrg).filter_by(
                    financial_org_id=finorg_id).one()
        return json.dumps(data.dictionary())
    except:
        print("Get financial orgs failed")
        abort(404)


@app.route('/api/cities', methods=['GET'])
def api_cities(entity=None):
    try:
        city_id = request.args.get('id')
        if entity is None and city_id is None:
            data = db.session.query(City).all()
            return json.dumps(list(map(lambda d: d.dictionary(), data)))
        else:
            if entity is not None:
                data = db.session.query(City).filter_by(city_id=entity).one()
            else:
                data = db.session.query(City).filter_by(city_id=city_id).one()
            return json.dumps(data.dictionary())
    except:
        print("Get cities failed")
        abort(404)

@app.route('/run_tests')
def run_tests():
    output = subprocess.getoutput("python startupfairy/tests_about.py")
    return json.dumps({'test_results': str(output)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)
