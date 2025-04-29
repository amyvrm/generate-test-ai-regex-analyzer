import os

def _read_prompt_file(file_name):
    
    script_dir = os.path.dirname(__file__)
    file_path = os.path.join(script_dir, file_name)

    try:
        with open(file_path, 'r') as file:
            content = file.read()
        return content
    except FileNotFoundError:
        return "File not found."
    except Exception as e:
        return f"An error occurred: {e}"

def read_prompt_string(base_file_path, procedure_prompt_path,report=""):
    system_prompt = _read_prompt_file(base_file_path)
    procedure_prompt = _read_prompt_file(procedure_prompt_path)

    prompt = (
        f"{system_prompt}\n"
        f"{report}\n"
        f"{procedure_prompt}\n"
    )
    return prompt

def main():
    prompt_string = read_prompt_string()
    print(prompt_string)

if __name__ == "__main__":
    main()