from logging import error
import os
from types import MethodType
from unicodedata import category
from urllib import response
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS, cross_origin
import random

# from jmespath import search

# from sympy import N


from models import setup_db, Question, Category, db

QUESTIONS_PER_PAGE = 10
def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page -1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    """
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    """
   # CORS(app, resources={r"*/api/*": {"origins": "*"}})
    CORS(app)

    """
    @TODO: Use the after_request decorator to set Access-Control-Allow
    """
    @app.after_request
    def after_request(response):

      response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization,True')
      response.headers.add('Access-Control-Allow-Headers', 'GET, POST, PATCH, DELETE, OPTIONS')

      return response



    """
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    """
    @app.route('/')
    def hello():
        return jsonify({
            'message': 'HELLO WORLD WELCOME TO THE TRIVIA GAME'
        })
    @app.route('/categories')
    def retrieve_categories():
        all_cat = Category.query.order_by(Category.type).all()
        # for_cat = [category.format() for category in all_cat]

        if len(all_cat) == 0:
            abort(404)

        return jsonify({
            'success':True,
            'categories': {cat.id: cat.type for cat in all_cat},
            "total_categories":len(all_cat)
        })    




    """
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    """

    @app.route('/questions')
    def retrieve_question():
        selection = Question.query.order_by(Question.id).all()

        current_questions = paginate_questions(request, selection)
        
        category = Category.query.order_by(Category.type).all()

        if len(current_questions) == 0:
            abort(404)

        return jsonify({
            'success':True,
            'questions': current_questions,
            "total_questions":len(selection),
            "current_category": [],
            "categories": {cat.id: cat.type for cat in category}
        })    




    """
    @TODO:
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.
    """
    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
      error = False
      try:  
        question = Question.query.filter(Question.id==question_id).one_or_none()
        
        if question is None:
            abort(404)

        question.delete()
        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)

        return jsonify({
            'success':True,
            "deleted": question_id,
            'questions': current_questions,
            "total_questions":len(selection),
        })    
      except Exception:
          error = True,
          abort(422)
            

    """
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.
    """
    @app.route('/questions', methods=['POST'])
    def create_question():
        body = request.get_json()

        nquestion = body.get('question', None)
        nanswer = body.get('answer', None)
        ndifficulty = body.get('difficulty', None)
        ncategory = body.get('category', None)

        try:
            question= Question(question=nquestion, answer=nanswer, difficulty=ndifficulty,category=ncategory)
            # db.session.add(question)
            # db.session.commit()\
            question.insert()



            # selection = Question.query.order_by(Question.id).all()
            # current_questions = paginate_questions(request, selection)

            return jsonify({
                'success':True,
                # 'questions': current_questions,
                # "total_questions":len(selection),
            })    

        except Exception:
          abort(422)  






    """
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """
    @app.route('/questions/search', Methods=['POST'])
    def search_questions():
        body = request.get_json()

        search = body.get('searchTerm', None)

        if search:

           questions = Question.query.filter(Question.question.ilike(f'%(search)%')).all()
           current_questions = [question.format() for question in questions]

           return jsonify({
              'success': True,
              'questions': current_questions,
              'total_questions': len(current_questions)
          })  
    """
    @TODO:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """

    @app.route('/categories/<int:category_id>/questions')
    def category_questions(category_id):
        id = category_id + 1

        category = Category.query.filter(Category.id==id).first()

        selection = Question.query.order_by(Question.id).filter(Question.category==id).all()
        questions = paginate_questions(request, selection)

        if len(questions) == 0:
            abort(404)

        return jsonify({
            'success':True,
            'questions': questions,
            'total_questions':len(selection),
            'categories': [category.type for category in Category.query.all()],
            'current_category': category.format()

        })    


    """
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """
    @app.route('/quiz', methods=['POST'])
    def play_quiz():
        # try:
            body = request.get_json()
            prev_questions = body.get('prev_questions', None)
            quiz_category = body.get('quiz_category', None)
            id = quiz_category['id']

            if id == 0:
                selection = Question.query.filter(Question.id.in_(prev_questions)).all()

            else:
                selection = Question.query.filter(Question.id.in_(prev_questions),Question.category==id).all()

            question = None
            if(selection):

                questions = paginate_questions(request, selection)
                question = random.choice(questions)
                 
                print(random.choice(question))


                return jsonify({
                    'success':True,
                    'question': [question.format()]
                })        
        # except:
        #      abort(422)       

    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    # """
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "We currently can't processes your request try a different method"
        }), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "Page not found"
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "Sorry your request can't be processed"
        }), 422

    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({
            "success": False,
            "error": 500,
            "message": "There was an error on the server and the request could not be completed"
        }), 500


    return app

