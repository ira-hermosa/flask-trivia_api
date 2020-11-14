#------------------------------------------------#
#Imports
#------------------------------------------------#

import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

#-------------------------------------------------#
# Pagination
#-------------------------------------------------#

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions

#--------------------------------------------------#
# App config
#--------------------------------------------------#


def create_app(test_config=None):
    app = Flask(__name__)
    setup_db(app)

    # Set up CORS
    CORS(app)

    # After_request decorator to set Access-Control-Allow
    @app.after_request
    def after_request(response):
        response.headers.add(
            'Access-Control-Allow-Headers',
            'Content-Type, Authorization, true')
        response.headers.add(
            'Access-Control-Allow-Methods',
            'GET, PUT, POST, DELETE, OPTIONS')
        return response


#-----------------------------------------------------#
# API Endpoints
#-----------------------------------------------------#

    # Gets all categories in the db

    @app.route('/categories')
    def get_catgories():
        categories = Category.query.order_by(Category.type).all()

        if len(categories) == 0:
            abort(404)

        return jsonify({'success': True, 'categories': {
                       category.id: category.type for category in categories}})

    # Gets a list questions from the db and number of total questions

    @app.route('/questions')
    def get_questions():
        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)

        if len(current_questions) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(Question.query.all())
        })

    # Deletes a question in the db by question id

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter(
                Question.id == question_id).one_or_none()

            question.delete()
            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)

            return jsonify({
                'success': True,
                'deleted': question_id,
                'questions': current_questions,
                'total_questions': len(Question.query.all())
            })

        except BaseException:
            abort(422)

    # Creates a question in the db
    # Requires question and answer text, category and difficulty level

    @app.route('/questions', methods=['POST'])
    def create_question():
        body = request.get_json()

        new_question = body.get('question', None)
        new_answer = body.get('answer', None)
        new_category = body.get('category', None)
        new_difficulty = body.get('difficulty', None)

        if not(
                'question' in body and 'answer' in body and 'difficulty' in body and 'category' in body):
            abort(422)

        try:
            question = Question(
                question=new_question,
                answer=new_answer,
                category=new_category,
                difficulty=new_difficulty)
            question.insert()
            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)

            return jsonify({
                'success': True,
                'created': question.id,
                'questions': current_questions,
                'total_questions': len(Question.query.all())
            })

        except BaseException:
            abort(422)

    # Searches a question using a substring of the search term

    @app.route('/questions/search', methods=['POST'])
    def search_questions():
        body = request.get_json()
        search_term = body.get('searchTerm', None)

        try:
            questions = Question.query.filter(
                Question.question.ilike(f'%{search_term}%')).all()
            current_questions = paginate_questions(request, questions)

            if len(questions) == 0:
                abort(404)

            return jsonify({
                'success': True,
                'questions': current_questions,
                'total_questions': len(Question.query.all())
            })

        except BaseException:
            abort(404)

    # Gets a question based on a category

    @app.route('/categories/<int:id>/questions')
    def get_questions_by_category(id):

        try:
            category = Category.query.filter_by(id=id).one_or_none()

            if category is None:
                abort(404)

            questions = Question.query.filter_by(category=id).all()
            current_questions = paginate_questions(request, questions)

            return jsonify({
                'success': True,
                'questions': current_questions,
                'total_questions': len(questions),
                'current_category': category.type
            })

        except BaseException:
            abort(404)

    # Plays the quiz by taking category and previous question parameters
    # Returns a random question within the given category.

    @app.route('/quizzes', methods=['POST'])
    def play_quiz():

        body = request.get_json()
        quiz_category = body.get('quiz_category')
        previous_questions = body.get('previous_questions')

        if ((quiz_category is None) or (previous_questions is None)):
            abort(400)

        if (quiz_category['id'] == 0):
            questions = Question.query.filter(
                Question.id.notin_((previous_questions))).all()

        else:
            questions = Question.query.filter_by(
                category=quiz_category['id']).filter(
                Question.id.notin_(
                    (previous_questions))).all()

        next_question = questions[random.randrange(
            0, len(questions))].format() if len(questions) > 0 else None

        return jsonify({
            'success': True,
            'question': next_question
        })


#-------------------------------------------------------------------------#
# Error handlers
#-------------------------------------------------------------------------#

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "resource not found"
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable"
        }), 422

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "bad request"
        }), 400

    return app
