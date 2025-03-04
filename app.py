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
    if 'files' not in request.files:
        return jsonify({"response": "No file uploaded"}), 400
    
    files = request.files.getlist('files')
    if not files:
        return jsonify({"response": "No selected files"}), 400
    
    accumulated_data = {}
    conflicts = {}

    for file in files[:5]:  # Process max 5 files
        if file.filename == '':
            continue

        try:
            # Get raw extracted data from model
            file_data = bk.init(file)  
            
            # Conflict check logic
            for key, value in file_data.items():
                if value in ["NOT FOUND", "Not Found"]:
                    continue  # Skip invalid values
                if key in accumulated_data:
                    if accumulated_data[key] != value:
                        conflicts[key] = [accumulated_data[key], value]
                else:
                    accumulated_data[key] = value
        except Exception as e:
            return jsonify({"response": f"Error processing {file.filename}: {str(e)}"}), 500

    # filename = file.filename
    # if filename == '':
    #     return jsonify({"response": "No selected file"}), 400
    
    # botresponse = bk.init(file)
    # print(botresponse)
    human_conflicts = {}
    for field, values in conflicts.items():
        human_label = bk.get_human_label(field)
        human_conflicts[human_label] = values

    return jsonify({
        "data": accumulated_data,
        "conflicts":human_conflicts if human_conflicts else None
    })

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