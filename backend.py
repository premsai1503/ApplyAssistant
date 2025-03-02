import base64
import json
import re
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, tool
# from together import Together
from langchain.chat_models import init_chat_model
import getpass
import os
from dotenv import load_dotenv
from IPython.display import Markdown

load_dotenv()

if not os.environ.get("TOGETHER_API_KEY"):
  os.environ["TOGETHER_API_KEY"] = os.getenv("TOGETHER_API_KEY")

def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

def encode_image_from_file(image_file):
    return base64.b64encode(image_file.read()).decode('utf-8')

def load_image():
    image_path = "images/sample_usa_passport.jpg"
    img = encode_image(image_path)
    return img

def prompt_message(details,):
    img = load_image()    
    sys_msg = SystemMessage(
        content=[
            {
                "type" : "text",
                "text" : f"""You are an amazing and helpful AI assistant who helps in OCR(Optical Character Recognition) tasks.
                            Your task is to identify these details: {details} in the given image. """
            }
        ]
    )

    human_msg = HumanMessage(
        content=[
            {
                "type" : "text", 
                # "text": f"""Find these details {details} from the image and return an JSON object with these {details} as keys.\n
                #             Do not include any additional text or explanation. Output must be valid JSON only."""
                # "text": f"Describe the given image and accurately extract any text present in it. Then, find the specified details: {details}."  
                #         "If any details are not found, return them as `NOT FOUND`."
                "text" : "Provide the results as JSON object only."
            },
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{img}"},
            },
        ]
    )

    ai_msg = AIMessage(
        content=[
            {
                "type" : "text",
                "text" : """{
                                "FirstName": "Nicholas",
                                "LastName": "Burwell",
                                "Sex": "Male",
                                "PassportNumber": "426012744",
                                "PermanentAccountNumber": "NOT FOUND",
                                "Nationality": "United States of America",
                                "DateofBirth": "18 Oct 1978",
                                "PlaceofBirth": "California, USA",
                                "DateofIssue": "14 Dec 2017",
                                "DateofExpiration": "13 Dec 2027"
                        }"""
            }
        ]
    )
    messages = [sys_msg, human_msg, ai_msg]
    return messages
     

def zero_shot_learning(details):
    messages = prompt_message(details)
    model = init_chat_model("meta-llama/Llama-Vision-Free", model_provider="together")
    return model , messages
    
def get_response(model, messages, document , details):
    try:
        document = encode_image_from_file(document)
        prompt = HumanMessage(
            content=[
                {
                    "type" : "text", 
                    # "text": f"""Find these details {details} from the image and return an JSON object with these {details} as keys.\n
                    #             Do not include any additional text or explanation. Output must be valid JSON only."""
                    # "text": f"Describe the given image and accurately extract any text present in it. Then, find the specified details: {details}."  
                    #         "If any details are not found, return them as `NOT FOUND`."
                    "text" : f"Thats good. Now do the same on this image. Provide the results in a JSON object like {details}. Do not include explanations, extra text, or formatting characters."
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{document}"},
                },
            ]
        )

        messages.append(prompt)
        response = model.invoke(messages)
        print(response)
        return response.content
    except Exception as e:
        return {"response": f"Error processing file: {str(e)}"}

def jsonification(response):
    """Extracts and fixes the JSON content from a model response."""
    try:
    # Extract JSON from response (removes extra text)
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            # Extract JSON part
            json_str = match.group(0)  
            # Remove backslashes before `{}` if present
            json_str = json_str.replace("\\{", "{").replace("\\}", "}")
            # Fix formatting issues
            json_str = json_str.strip().replace("\n", "").replace("\'", "\"")
            # Convert to dictionary
            return json.loads(json_str)
        else:
            return {"error": "Could not extract JSON from response."}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON format."}

def init(document):
    try:
        labels = [
        "First Name", "Last Name", "Sex","Passport Number","Permanent Account Number", "Nationality",
        "Date of Birth", "Place of Birth", "Date of Issue", "Date of Expiration"
        ]
        details = ", ".join(labels)
        model , messages = zero_shot_learning(details)
        response = get_response(model, messages, document , details)
    except Exception as e:
        return {"error": f"Processing failed: {str(e)}"}
    return json.loads(response)
