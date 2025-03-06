import base64
import json
import re
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
# from together import Together
from langchain.chat_models import init_chat_model
import getpass
import os
from dotenv import load_dotenv
from IPython.display import Markdown
from langgraph.graph import START, StateGraph, END, MessagesState
from langgraph.checkpoint.memory import MemorySaver

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
                    "text" : f"""Thats good. Now do the same on this image. Provide the results in a JSON object like {details}. 
                                Do not include explanations, extra text, or formatting characters."""
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

def init(document):
    try:
        # Ensure document is at start position
        if hasattr(document, 'seek'):
            document.seek(0)

        labels = [
            "SSN", "Mobile Number", "First Name", "Last Name", "Sex","Passport Number","Permanent Account Number", "Nationality",
            "Date of Birth", "Place of Birth", "Date of Issue", "Date of Expiration"
        ]
        details = ", ".join(labels)
        model , messages = zero_shot_learning(details)
        raw_response = get_response(model, messages, document , details)
        processed_data = jsonification(raw_response)
        if "error" in processed_data:
            return processed_data    
        return processed_data
        # return json.loads(response)
    except Exception as e:
        return {"error": f"Processing failed: {str(e)}"}

# Initialize memory and graph
memory = MemorySaver()
workflow = StateGraph(state_schema=MessagesState)

def call_model(state: MessagesState):
    # Your existing model invocation
    chat_model = init_chat_model("meta-llama/Llama-Vision-Free", model_provider="together")
    response = chat_model.invoke(state["messages"])
    return {"messages": response}

# Build workflow
workflow.add_edge(START, "model")
workflow.add_node("model", call_model)
# workflow.set_entry_point("model")
# workflow.add_edge("model", END)
app = workflow.compile(checkpointer=memory)

def chatbot(user_message: str, thread_id: str = "default"):
    with open("context.txt","r") as f:
        context=f.read()
    system = SystemMessage(
        content=[
            {
                "type" : "text",
                "text" : f"""You are an amazing and helpful AI assistant in financial sector.
                Now you are being used by Wells Fargo as their Apply Assistant who helps customers in 
                auto filling forms based on the documents they upload.
                So now you should also answer about Wells Fargo specific questions like questions about their products,
                how to use autofill feature, what documents the user can upload.
                You follow these basic rules of operations.
                They are: 
                    1) You can greet them and tell them about yourself. When telling them about yourself,
                    your response should like "Hi, I'm a Wells Fargo AI assitant here to help you." Then you can tell them about
                    your "new" feature i.e., "Auto Filling" user forms, products of Wells Fargo you on which can provide info.
                    2) Can offer help in answering queries related to financial sector.
                    3) Can't offer help in answering queries unrelated to financial sector. If such query is asked you 
                       should respond by saying "Sorry this query is out of scope for me".
                You dont have to greet the customer for every query. 

                You can use below context for your reference while answering Wells Fargo specific questions.
                Context: {context}. This context is only for your reference. You should make and give your own responses to user.
                As you are an assisstant of highly esteemed bank, all your responses should be grammatically correct"""
            }
        ]
    )

    # messages = [system, human]

    # chat_model = init_chat_model("meta-llama/Llama-Vision-Free", model_provider="together")
    # response = chat_model.invoke(messages)
    # return response.content

    input_message = HumanMessage(
        content=[
            {
                "type" : "text", 
                "text" : user_message + ". Answer in 50 words. If its a greeting keep it to 30 words."
            }
        ]
    )
    
    # Add system message for new threads
    if not memory.get_tuple(config={"configurable": {"thread_id": thread_id}}):
        input_message = [system, input_message]
    else:
        input_message = [input_message]

    # Invoke with persistence
    config = {"configurable": {"thread_id": thread_id}}
    result = app.invoke(
        {"messages": input_message},
        config=config
    )
    
    return result["messages"][-1].content