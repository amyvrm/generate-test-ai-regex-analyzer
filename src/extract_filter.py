import re
import argparse
import os
import json


def extract_xml_from_file(filepath):
    """
    Extract the XML content under the "Step 3: Crafting the Filter"

    Args:
        file_path (str): Path to the file containing the filter content.

    Returns:
        str: Extracted XML content, or None if not found.
    """
    with open(filepath, 'r', encoding='utf-8') as file:
        content = file.read()

    # Find section starting with "### Step 3: Crafting the Filter"
    section_start = re.search(r"### Step 3: Crafting the Filter", content)
    if not section_start:
        print("Section not found in the file.")
        return None

    # Extract everything after the section header
    post_section = content[section_start.end():]

    # Use regex to extract content between triple backticks ```xml ... ```
    xml_match = re.search(r"```xml(.*?)```", post_section, re.DOTALL)
    if xml_match:
        xml_content = xml_match.group(1).strip()
        return xml_content
    else:
        print("No XML block found after the section.")
        return None

# Function to load configuration from a JSON file
def load_config(config_file):
    """Load configuration from a JSON file."""
    with open(config_file, 'r') as f:
        return json.load(f)

def main():
    parser = argparse.ArgumentParser(description="Extract XML regex from AI report for one or more TSL IDs.")
    parser.add_argument("--tsl_id", required=True, help="Comma-separated TSL IDs to process.")
    parser.add_argument("--ai_report_dir", default="report/ai_report", help="Directory containing AI report files.")
    parser.add_argument("--config_file", default="config/config.json", help="Path to the configuration file.")
    args = parser.parse_args()
    config = load_config(args.config_file)
    ai_report_dir = args.ai_report_dir
    tsl_ids = [tid.strip() for tid in args.tsl_id.split(',') if tid.strip()]
    for tsl_id in tsl_ids:
        ai_report = os.path.join(ai_report_dir, f"{tsl_id}.txt")
        if not os.path.exists(ai_report):
            print(f"File not found: {ai_report}, skipping.")
            continue
        report_name = tsl_id
        file_path_config = config["ai_regex_path"]
        os.makedirs(file_path_config, exist_ok=True)
        file_path = f"{file_path_config}/{report_name}.txt"
        xml_content = extract_xml_from_file(ai_report)
        if xml_content:
            print(f"Extracted XML Content for {tsl_id}:")
            print(xml_content)
            with open(file_path, "w") as output_file:
                output_file.write(xml_content)
            print(f"XML content saved to: {file_path}")
        else:
            print(f"Failed to extract XML content for {tsl_id}.")


if __name__ == "__main__":
    main()