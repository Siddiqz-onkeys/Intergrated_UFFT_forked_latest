from flask import Flask, request, render_template, redirect, url_for, session,flash,make_response , Request, Response
from Expense.app import expense_bp
from user_reg.main import user_reg_bp
from Saving.app import saving_bp
from data_visualization.app import data_visualization_bp
from budgets.app import budget_bp 



def create_app():
    app = Flask(__name__)

    app = Flask(__name__)
    app.secret_key = 'ProjectUFFT'

    @app.route('/')
    def home():
            return render_template('home1.html')
       

    app.register_blueprint(expense_bp, url_prefix='/expense')
    app.register_blueprint(user_reg_bp, url_prefix='/user_reg')
    app.register_blueprint(saving_bp, url_prefix='/saving')
    app.register_blueprint(data_visualization_bp, url_prefix='/data_visualization')
    app.register_blueprint(budget_bp, url_prefix='/budget') 


    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True,port=8000)
