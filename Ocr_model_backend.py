import base64
import json
import re
import getpass
import os
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, tool
import pdfplumber
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
from IPython.display import Markdown
from PIL import Image
import PyPDF2

load_dotenv()

FIELD_MAPPING = {
    "SSN": ("SSN", "SSN"),
    "MobileNumber": ("Mobile Number", "MobileNumber"),
    "FirstName": ("First Name", "FirstName"),
    "LastName": ("Last Name", "LastName"),
    "Sex": ("Sex", "Sex"),
    "PassportNumber": ("Passport Number", "PassportNumber"),
    "PermanentAccountNumber": ("Permanent Account Number", "PermanentAccountNumber"),
    "Nationality": ("Nationality", "Nationality"),
    "DateofBirth": ("Date of Birth", "DateofBirth"),
    "PlaceofBirth": ("Place of Birth", "PlaceofBirth"),
    "DateofIssue": ("Date of Issue", "DateofIssue"),
    "DateofExpiration": ("Date of Expiration", "DateofExpiration")
}

def get_human_label(field):
    """Get human-readable label for a field"""
    return FIELD_MAPPING.get(field, (field,))[0]

def get_form_field_id(field):
    """Get form field ID for a backend field"""
    return FIELD_MAPPING.get(field, (None, field))[1]

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

def prompt_message(details):
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
                                "SSN": "NOT FOUND",
                                "Mobile Number": "NOT FOUND",
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
    
def get_response_image(model, messages, document , details):
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
            # return json.loads(json_str)
        else:
            return {"error": "Could not extract JSON from response."}
        
        # Convert human-readable keys to backend keys
        temp_data = json.loads(json_str)
        converted_data = {}

        for human_key, value in temp_data.items():
            matched = False
            for backend_key, (label, _) in FIELD_MAPPING.items():
                if human_key.lower() == label.lower():
                    converted_data[backend_key] = value
                    break
            else:  # If no match found
                converted_data[human_key] = value
                
        return converted_data
    except Exception as e:
        return {"error": str(e)}

def get_human_readable_labels(fields):
    """Convert backend keys to human-readable labels"""
    return [FIELD_MAPPING.get(field, (field,))[0] for field in fields]


def is_pdf_or_image(file_obj):
    try:
        # Check if it's a PDF
        pdf_reader = PyPDF2.PdfReader(file_obj)
        if pdf_reader.pages:
            return "PDF"
    except Exception:
        pass  # Not a PDF

    try:
        # Check if it's an Image
        file_obj.seek(0)  # Reset file pointer after PDF check
        with Image.open(file_obj) as img:
            img.verify()  # Verify image file integrity
            return "Image"
    except Exception:
        pass  # Not an Image

    return "Unknown"


def extract_text_from_pdf(file_obj):
    """Extracts text from a PDF using pdfplumber."""
    text = ""
    with pdfplumber.open(file_obj) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text.strip()

def init(document):
    try:
        labels = [
        "SSN", "Mobile Number", "First Name", "Last Name", "Sex","Passport Number","Permanent Account Number", "Nationality",
        "Date of Birth", "Place of Birth", "Date of Issue", "Date of Expiration"
        ]
        details = ", ".join(labels)
        # Figure out if the file is an image or a document
        file_type = is_pdf_or_image(document)
        # logic for pdf and image goes here
        model , messages = zero_shot_learning(details)
        raw_response = get_response_image(model, messages, document , details)
        processed_data = jsonification(raw_response)
        if "error" in processed_data:
            return processed_data    
        return processed_data
        # return json.loads(response)
    except Exception as e:
        return {"error": f"Processing failed: {str(e)}"}