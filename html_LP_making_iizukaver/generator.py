import json
import os
import sys
import shutil
from jinja2 import Environment, FileSystemLoader

# Configuration
# Default to sample_plan.json if not specified
INPUT_FILE = sys.argv[1] if len(sys.argv) > 1 else 'input/sample_plan.json'
OUTPUT_DIR = 'output'
TEMPLATE_DIR = 'templates'
STATIC_DIR = 'static'

def load_data(filepath):
    """Loads the JSON planning document."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def nl2br(value):
    """Custom filter to replace newlines with <br>."""
    if isinstance(value, str):
        return value.replace('\n', '<br>')
    return value

def generate_site():
    # 1. Load Data
    print(f"Loading data from {INPUT_FILE}...")
    try:
        data = load_data(INPUT_FILE)
    except FileNotFoundError:
        print(f"Error: Could not find {INPUT_FILE}")
        return

    # 2. Setup Jinja2 Environment
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    env.filters['nl2br'] = nl2br
    
    # Use hybrid template if input is hybrid_lp_plan.json or similar
    if 'hybrid_v2' in INPUT_FILE:
        template_name = 'hybrid_v2.html'
    elif 'hybrid' in INPUT_FILE:
        template_name = 'hybrid_index.html'
    else:
        template_name = 'index.html'
    
    template = env.get_template(template_name)

    # 3. Render HTML
    print("Rendering HTML...")
    output_html = template.render(**data)

    # 4. Write Output
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    output_file_path = os.path.join(OUTPUT_DIR, 'index.html')
    with open(output_file_path, 'w', encoding='utf-8') as f:
        f.write(output_html)
    print(f"HTML generated at {output_file_path}")

    # 5. Copy Static Assets
    print("Copying static assets...")
    output_static_dir = os.path.join(OUTPUT_DIR, 'static')
    if os.path.exists(output_static_dir):
        shutil.rmtree(output_static_dir)
    
    if os.path.exists(STATIC_DIR):
        shutil.copytree(STATIC_DIR, output_static_dir)
        print(f"Static assets copied to {output_static_dir}")
    else:
        print("Warning: No static directory found to copy.")

    print("Success! LP generation complete.")

if __name__ == "__main__":
    generate_site()
