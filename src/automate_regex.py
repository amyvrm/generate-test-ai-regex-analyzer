import boto3
import os
import json
from langchain_community.document_loaders import PyPDFLoader
# from lib.pdf import read_pdf_section
from prompt import read_prompt_string
from langchain_aws.bedrock_llm import BedrockLLM
import logging
import random
import time
from botocore.exceptions import ClientError
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Use INFO for less verbose output
    format='%(asctime)s [%(levelname)s] %(module)s %(funcName)s : %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


def get_credential(access_key, secret_key):
    # Assume the role in Account A
    sts_client = boto3.client('sts',
                              aws_access_key_id=access_key,
                              aws_secret_access_key=secret_key)
    assumed_role = sts_client.assume_role(
                    RoleArn="arn:aws:iam::276646173734:role/bedrock_access_amit",
                    RoleSessionName="BedrockAccessSession")

    # Use the temporary credentials to create a Bedrock client
    credentials = assumed_role['Credentials']
    return credentials['AccessKeyId'], credentials['SecretAccessKey'], credentials['SessionToken']


def get_bedrock_agent(access_key, secret_key, session_token):
    """Initialize the Bedrock client."""
    return BedrockLLM(
        credentials_profile_name="default",
        provider="mistral",
        client=boto3.client('bedrock-runtime', 
                            aws_access_key_id=access_key,
                            aws_secret_access_key=secret_key,
                            aws_session_token=session_token,
                            region_name='us-east-1'),
                            model_id="arn:aws:bedrock:us-east-1:276646173734:imported-model/oshi2wtlhpxr",
                            model_kwargs={"max_tokens": 4096, "top_p": 0.9, "stop": [], "temperature": 1, "top_k": 50},
    )

def read_pdf_section(pdf_text, start, end):
    """Extract text between two sections in the PDF."""
    try:
        content = ""
        capture = False

        # Split the text into lines and process line by line
        for line in pdf_text.splitlines():
            if start in line:
                capture = True
            if capture:
                content += line + "\n"
            if end in line:
                break

        return content.strip()
    except Exception as e:
        print(f"Error processing PDF text: {e}")
        return None

def extract_pdf_sections(pdf_file_path):
    """Extract specific sections from the PDF."""
    loader = PyPDFLoader(pdf_file_path)
    documents = loader.load()

    # Combine the text content of all pages into a single string
    pdf_text = "\n".join([doc.page_content for doc in documents])

    # Log the extracted text for debugging
    logger.debug(f"Extracted PDF text: {pdf_text[:500]}")  # Log the first 500 characters

    # Extract specific sections
    mechanism = read_pdf_section(pdf_text, '4.1. Technical Mechanism', '4.2. Source Code Walkthrough')
    detection = read_pdf_section(pdf_text, '6.1. Remote Detection of Generic Attacks', '6.2. Remote Detection of Known Exploits')

    if not mechanism or not detection:
        logger.error("The uploaded file is not a valid VRS report. Please choose the correct one!")
        return None

    return mechanism + '\n' + detection

def prompt_file_path(file_name):
    """Get the file path for the prompt."""
    curr_path = os.getcwd()
    logger.info(f"Current working directory: {curr_path}")
    prompt_path = os.path.join(curr_path, 'prompts')
    # Check if the prompt directory exists
    if not os.path.exists(prompt_path):
        raise FileNotFoundError(f"Prompt path does not exist: {prompt_path}")
    # Check if the prompt file exists
    prompt_file = os.path.join(prompt_path, file_name)
    if os.path.exists(prompt_file):
        logger.info(f"Prompt path already exists: {prompt_file}")
        return prompt_file
    raise FileNotFoundError(f"Prompt file not found: {prompt_file}")

def craft_filter(pdf_file_path, dslabs_access_key, dslabs_secret_key):
    """Craft the regex filter from the VRS report."""
    # Extract relevant sections from the PDF
    logger.info(f"Extracting text from PDF: {pdf_file_path}")
    extracted_text = extract_pdf_sections(pdf_file_path)
    if not extracted_text:
        logger.error("Failed to extract valid text from the PDF.")
        return None

    base_prompt_path = prompt_file_path('base_prompt.txt')
    procedure_prompt_path = prompt_file_path('procedure_prompt.txt')
    # Read the prompt templates
    try:
        prompt_string = read_prompt_string(
            base_prompt_path,
            procedure_prompt_path,
            extracted_text
        )
    except Exception as e:
        logger.error(f"Error reading prompt templates: {e}")
        return None

    # Query the Bedrock model with retry logic
    logger.info("Querying the Bedrock model...")
    max_retries = 5
    base_delay = 150  # seconds, reduced for faster retry
    for attempt in range(max_retries):
        try:
            access_key, secret_key, session_token = get_credential(dslabs_access_key, dslabs_secret_key)
            bedrock_agent = get_bedrock_agent(access_key, secret_key, session_token)
            response = bedrock_agent.invoke(input=prompt_string)
            logger.info("Successfully generated the filter.")
            return response
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code in ['ModelNotReadyException', 'ThrottlingException']:
                logger.warning(f"{error_code}: Retrying in {base_delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(base_delay)
            else:
                logger.error(f"Error querying the Bedrock model: {e}")
                break
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            break
    logger.error("Failed to query the Bedrock model after multiple attempts.")
    return None

# Function to load configuration from a JSON file
def load_config(config_file):
    """Load configuration from a JSON file."""
    with open(config_file, 'r') as f:
        return json.load(f)

def get_cmd_line_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Automate regex filter generation from VRS report.")
    parser.add_argument("--pdf_file_path", help="Path to the PDF file.")
    parser.add_argument("--access_key", help="AWS access key ID.")
    parser.add_argument("--secret_key", help="AWS secret access key.")
    parser.add_argument("--config_file", default="config/config.json", help="Path to the configuration file.")
    return parser.parse_args()

def main():
    parser = argparse.ArgumentParser(description="Automate regex filter generation from VRS report.")
    parser.add_argument("--tsl_id", required=True, help="Comma-separated TSL IDs to process.")
    parser.add_argument("--pdf_dir", default="report/vrs", help="Directory containing VRS PDF files.")
    parser.add_argument("--access_key", help="AWS access key ID.")
    parser.add_argument("--secret_key", help="AWS secret access key.")
    parser.add_argument("--config_file", default="config/config.json", help="Path to the configuration file.")
    args = parser.parse_args()
    config = load_config(args.config_file)
    pdf_dir = args.pdf_dir
    access_key = args.access_key
    secret_key = args.secret_key
    tsl_ids = [tid.strip() for tid in args.tsl_id.split(',') if tid.strip()]
    for tsl_id in tsl_ids:
        # Find the PDF file for this TSL ID
        pdf_files = [f for f in os.listdir(pdf_dir) if f.startswith(tsl_id) and f.endswith('.pdf')]
        if not pdf_files:
            logger.error(f"No PDF found for {tsl_id} in {pdf_dir}, skipping.")
            continue
        pdf_file_path = os.path.join(pdf_dir, pdf_files[0])
        logger.info(f"Processing {tsl_id} with PDF: {pdf_file_path}")
        basename = os.path.basename(pdf_file_path)
        report_name = basename.split()[0] if basename and len(basename.split()) > 0 else tsl_id
        if not os.path.exists(pdf_file_path):
            logger.error(f"File not found: {pdf_file_path}")
            continue
        regex_filter = craft_filter(pdf_file_path, access_key, secret_key)
        if regex_filter:
            ai_report_path = config["ai_report_path"]
            output_file_path = f"{ai_report_path}/{tsl_id}.txt"
            with open(output_file_path, "w") as output_file:
                output_file.write(regex_filter)
            logger.info(f"Regex filter saved to: {output_file_path}")
        else:
            logger.error(f"Failed to generate the regex filter for {tsl_id}.")

if __name__ == "__main__":
    main()