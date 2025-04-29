import os
import re

def convert_wiki_to_structured(input_file, output_file):
    """
    Converts regex patterns from a simplified format to the structured format.
    """
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        for line in infile:
            line = line.strip()
            if not line or line.startswith("#"):  # Skip empty lines or comments
                continue

            # Match the key and regex pattern
            match = re.match(r"(\w+(\.\w+)*)(?:\s*[~|=]\s*\{(.+?)\})?", line)
            if match:
                key = match.group(1)  # e.g., ip.saddr, tcp.sport
                regex_pattern = match.group(3)  # e.g., .* or specific regex

                # Determine the type of match (regex or literal)
                if regex_pattern:
                    if regex_pattern.startswith("<") and regex_pattern.endswith(">"):
                        # Literal match
                        outfile.write(f"<{key}>\n  <strmatch/>\n  <pstring>{regex_pattern[1:-1]}</pstring>\n</{key}>\n")
                    else:
                        # Regex match
                        outfile.write(f"<{key}>\n  <regex offset=\"0\" depth=\"-1\" nocase=\"0\"/>\n  <pstring>{regex_pattern}</pstring>\n</{key}>\n")
                else:
                    # Default to match any value if no regex is provided
                    outfile.write(f"<{key}>\n  <regex offset=\"0\" depth=\"-1\" nocase=\"0\"/>\n  <pstring>.*</pstring>\n</{key}>\n")
            else:
                print(f"Unrecognized line format: {line}")

def main():
    input_file = "report/ai_regex/TSL20230504-07-wiki.txt"
    output_file = "report/ai_regex/TSL20230504-07-converted.txt"
    
    if not os.path.exists(input_file):
        print(f"Input file {input_file} does not exist.")
        return
    
    convert_wiki_to_structured(input_file, output_file)
    print(f"Converted regex patterns saved to {output_file}")

if __name__ == "__main__":
    main()
