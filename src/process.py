from models import FormDoc
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI
import logging
import json
import re
import os

def clean_and_parse_response(response_text):
    cleaned_text = re.sub(r"```json|```", "", response_text).strip()
    try:
        return json.loads(cleaned_text)
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse JSON data: {e}")
        return None

def process_medical_information(extracted_text):
    preamble = ("You are provided with text extracted from a medical" +
                "form, which contains various data fields related to patient" + 
                "information, diagnoses, treatments, and outcomes." +
                "Your task is to analyze this text and extract relevant data" +
                "into a structured JSON format that matches the predefined schema." + 
                "Ensure that only valid JSON is returned, with all fields populated" +
                "according to the extracted information. Use null for any missing" + 
                "data.")
    postamble = ("Only return the JSON data in a structured format" +
                 "that matches the schema. Do not include any additional" +
                 "text, comments, or explanations")

    system_template = "{preamble}"
    human_template = "{format_instructions}\n\nExtracted Text:\n{extracted_text}\n\n{postamble}"
    
    system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)
    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

    parser = PydanticOutputParser(pydantic_object=FormDoc)
    chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])
    
    request = chat_prompt.format_prompt(
        preamble=preamble,
        format_instructions=parser.get_format_instructions(),
        extracted_text=extracted_text,
        postamble=postamble
    ).to_messages()

    chat = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)

    try:
        response = chat.invoke(request)
        return clean_and_parse_response(response.content)
    except Exception as e:
        logging.exception(f"Error processing medical information: {e}")
        raise RuntimeError("Error processing medical information.")

def process_screening_data(form_text, lab_text=None):
    """
    Process the screening form data and lab results to extract structured information.
    
    :param form_text: Text extracted from the screening form
    :param lab_text: Text extracted from lab results (optional)
    :return: Structured data in JSON format
    """
    combined_text = form_text
    if lab_text:
        combined_text += "\n\n=== LABORATORY RESULTS ===\n\n" + lab_text
    
    preamble = (
        "You are a medical data extraction assistant specialized in kidney disease screening. "
        "You will be provided with text extracted from a screening form and possibly laboratory results. "
        "Your task is to extract relevant data and organize it into a structured JSON format following the "
        "specified schema. The data should be organized in the exact order specified in the schema. "
        "Pay special attention to extracting numerical values correctly and identifying the patient's "
        "screening information and laboratory results."
    )
    
    postamble = (
        "Only return the JSON data in a structured format that matches the schema. Do not include any "
        "additional text, comments, or explanations. If certain fields are missing in the input data, "
        "use null or appropriate default values as specified in the schema."
    )

    system_template = "{preamble}"
    human_template = "{format_instructions}\n\nExtracted Text:\n{extracted_text}\n\n{postamble}"
    
    system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)
    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

    parser = PydanticOutputParser(pydantic_object=FormDoc)
    chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])
    
    request = chat_prompt.format_prompt(
        preamble=preamble,
        format_instructions=parser.get_format_instructions(),
        extracted_text=combined_text,
        postamble=postamble
    ).to_messages()

    # Use an environment variable to determine the model (allows for testing with different models)
    model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    chat = ChatOpenAI(model=model_name, temperature=0.0)

    try:
        response = chat.invoke(request)
        return clean_and_parse_response(response.content)
    except Exception as e:
        logging.exception(f"Error processing screening data: {e}")
        raise RuntimeError("Error processing screening data.")
