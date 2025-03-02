from flask import Flask, request, jsonify, render_template, session, url_for , redirect
from flask_session import Session
import backend as bk
import databasemodel as dbm
import os
import json

app = Flask(__name__,
    template_folder='Frontend',
    static_folder='Frontend',  # Add this line
    static_url_path=''         # Add this line
)

@app.route('/' , methods=['GET' , 'POST'])
def index():            
    return render_template('landing_page.html')

@app.route('/savings-options')
def savings_options():
    return render_template('savings_options.html')

@app.route('/form' , methods=['GET' , 'POST'])
def form_page():
    return render_template('form_page.html')

@app.route('/chatbot', methods=['POST'])
def chatbot():
    data = request.json
    user_message = data.get("message")
    bot_response = {"response": "The Chat facility is under development! So, you can upload the document based on the form displayed"} # Replace with actual chatbot logic
    
    return jsonify(bot_response)

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({"response": "No file uploaded"}), 400
    
    file = request.files['file']
    filename = file.filename
    if filename == '':
        return jsonify({"response": "No selected file"}), 400
    
    botresponse = bk.init(file)
    print(botresponse)
    return jsonify(botresponse)

@app.route('/submit', methods=['POST'])
def db_submit():
    data = request.json
    print(data)
    result = dbm.form_data_submit(data)
    print(result)
    return jsonify(result)

@app.route('/success')
def success_page():
    return render_template('success.html')

# @app.route('/chatbot', methods=['POST'])
# def chatbot():
#     data = request.json
#     user_message = data.get("message").lower()
    
#     # Basic response logic
#     responses = {
#         "hello": "Hello! How can I assist you today?",
#         "help": "I can help with form filling using document uploads. Try sending a passport image!",
#         "default": "The chat facility is under development. Please use document upload for form filling."
#     }
    
#     bot_response = responses.get(user_message, responses["default"])
#     return jsonify({"response": bot_response})

if __name__ == '__main__':
    app.run(debug=True)