import json
import os
import sys
import shutil
from jinja2 import Environment, FileSystemLoader

# Configuration
OUTPUT_DIR = 'output'
TEMPLATE_DIR = 'templates'
STATIC_DIR = 'static'

def load_data(filepath):
    """Loads the JSON planning document."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {filepath} not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {filepath}.")
        sys.exit(1)

def nl2br(value):
    """Custom filter to replace newlines with <br>."""
    if isinstance(value, str):
        return value.replace('\n', '<br>')
    return value

def sync_directories(src_dir, dst_dir):
    """Recursively copies files from src_dir to dst_dir if they are newer or missing."""
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)
    
    count_updated = 0
    count_skipped = 0
    
    for root, dirs, files in os.walk(src_dir):
        rel_path = os.path.relpath(root, src_dir)
        dest_root = os.path.join(dst_dir, rel_path)
        
        if not os.path.exists(dest_root):
            os.makedirs(dest_root)
            
        for file in files:
            src_file = os.path.join(root, file)
            dst_file = os.path.join(dest_root, file)
            
            should_copy = False
            if not os.path.exists(dst_file):
                should_copy = True
            else:
                if os.stat(src_file).st_mtime > os.stat(dst_file).st_mtime:
                    should_copy = True
            
            if should_copy:
                shutil.copy2(src_file, dst_file)
                count_updated += 1
            else:
                count_skipped += 1
                
    print(f"Sync complete: {count_updated} updated, {count_skipped} skipped.")

def generate_site(input_file, style="standard"):
    # 1. Load Data
    print(f"Loading data from {input_file}...")
    data = load_data(input_file)
    
    # Inject default 'legal' data if missing (Safety for legal footer)
    if 'legal' not in data:
        data['legal'] = {
            'price_min': '880円',
            'price_max': '12,000円',
            'price_regular_min': '4,000円',
            'price_regular_max': '15,000円',
            'contact_email': 'info@latrico.jp',
            'company_name': '株式会社ラトリコ',
            'company_address': '東京都港区赤坂8-4-14'
        }

    # 2. Setup Jinja2 Environment with Style Support
    # Search paths: specific style -> common -> base
    template_paths = [
        os.path.join(TEMPLATE_DIR, style),
        os.path.join(TEMPLATE_DIR, 'common'),
        TEMPLATE_DIR
    ]
    print(f"Style: {style}")
    print(f"Template paths: {template_paths}")
    
    env = Environment(loader=FileSystemLoader(template_paths))
    env.filters['nl2br'] = nl2br
    
    try:
        template = env.get_template('index.html')
    except Exception as e:
        print(f"Error loading template 'index.html' for style '{style}': {e}")
        return

    # 2.5 Generate Coupon Image (Before Rendering)
    # We need to know output paths ahead of time or use temporary
    # Actually, we need to know the target style output dir for proper relative paths?
    # But wait, 'output_static_dir' isn't defined yet in the original code flow...
    # We can define it early.

    plan_name = os.path.splitext(os.path.basename(input_file))[0]
    target_output_dir = os.path.join(OUTPUT_DIR, plan_name, style)
    if not os.path.exists(target_output_dir):
        os.makedirs(target_output_dir)
    output_static_dir = os.path.join(target_output_dir, 'static')
        
    if 'coupon' in data:
        print("Generating Coupon Image...")
        try:
            from coupon_generator import CouponRenderer
            renderer = CouponRenderer()
            
            # Ensure images/generated/{plan_name} exists
            output_img_dir = os.path.join(output_static_dir, f"images/generated/{plan_name}")
            if not os.path.exists(output_img_dir):
                os.makedirs(output_img_dir)
            
            output_coupon_path = os.path.join(output_img_dir, 'coupon.png')
            success = renderer.generate(data['coupon'], output_coupon_path)
            
            if success:
                # Calculate relative path for HTML use
                rel_path = f"static/images/generated/{plan_name}/coupon.png"
                print(f"Coupon generated successfully at {output_coupon_path}")
                
                # Update campaign image URL in data object (In-memory update for Jinja)
                found_campaign = False
                
                # Strategy 1: Top-level 'campaign' key (if used)
                if 'campaign' in data:
                    data['campaign']['image_url'] = rel_path
                    found_campaign = True
                
                # Strategy 2: 'sections' list (standard/manga structure)
                if 'sections' in data:
                    for section in data['sections']:
                        if section['type'] == 'campaign_box' or section['type'] == 'campaign':
                            section['data']['image_url'] = rel_path
                            found_campaign = True
                            
                if found_campaign:
                    print(f"Updated campaign image URL to: {rel_path}")
                else:
                    print("Warning: Generated coupon but could not find a campaign section to attach it to.")
        except Exception as e:
            print(f"Error generating coupon: {e}")

    # 3. Render HTML
    print("Rendering HTML...")
    output_html = template.render(**data)

    # 4. Write Output
    # Extract plan name from filename (e.g., input/busy_mom_plan.json -> busy_mom_plan)
    plan_name = os.path.splitext(os.path.basename(input_file))[0]
    
    # New Structure: output/{plan_name}/{style_name}/
    target_output_dir = os.path.join(OUTPUT_DIR, plan_name, style)

    if not os.path.exists(target_output_dir):
        os.makedirs(target_output_dir)
    
    output_file_path = os.path.join(target_output_dir, 'index.html')
    with open(output_file_path, 'w', encoding='utf-8') as f:
        f.write(output_html)
    print(f"HTML generated at {output_file_path}")

    # 5. Render CSS (Dynamic Style)
    # We look for style.css in the style folder context first
    print("Rendering CSS...")
    try:
        # Check if style-specific CSS template exists, otherwise fall back to common or skip
        # For now, we assume style.css might be in templates/css/style.css (legacy) or templates/standard/css/style.css
        # Current file structure: 
        # templates/standard/components... 
        # templates/base.html (in common)
        # static/css/style.css (this is the SOURCE of the CSS structure usually, but we have a jinja template?)
        # Wait, the previous code loaded 'css/style.css'. 
        # Let's check where 'css/style.css' is now.
        # It was likely in `templates/css/style.css`.
        # I did `mv templates/components templates/standard/`.
        # I did `mv templates/index.html templates/standard/`.
        # I did `mv templates/base.html templates/common/`.
        # I did NOT move `templates/css`. So it checks `templates/css/style.css`.
        # Using FileSystemLoader(template_paths), 'css/style.css' will be searched in:
        # [templates/standard, templates/common, templates]
        # So 'templates/css/style.css' matches 'templates' + 'css/style.css'. It should still be found if I keep TEMPLATE_DIR in paths.
        
        css_template = env.get_template('css/style.css')
        output_css = css_template.render(**data)

    except Exception as e:
        print(f"Warning: Could not render dynamic CSS ({e}). Skipping. Continuing with asset sync...")

    # 6. Copy Static Assets (Incremental) and Write CSS
    print("Syncing static assets...")
    output_static_dir = os.path.join(target_output_dir, 'static')
    
    # Incremental Copy instead of Full Delete
    if os.path.exists(STATIC_DIR):
        sync_directories(STATIC_DIR, output_static_dir)
    else:
        print("Warning: No static directory found to copy.")
        if not os.path.exists(output_static_dir):
            os.makedirs(output_static_dir)

    # Ensure css dir exists
    output_css_dir = os.path.join(output_static_dir, 'css')
    if not os.path.exists(output_css_dir):
        os.makedirs(output_css_dir)

    # Write dynamic style.css (Always overwrite as it depends on JSON plan)
    if 'output_css' in locals():
        css_file_path = os.path.join(output_css_dir, 'style.css')
        with open(css_file_path, 'w', encoding='utf-8') as f:
            f.write(output_css)
        print(f"CSS generated at {css_file_path}")

    # 7. Generate Coupon Image (If configured)
    if 'coupon' in data:
        print("Generating Coupon Image...")
        try:
            from coupon_generator import CouponRenderer
            renderer = CouponRenderer()
            
            # Ensure images/generated/{plan_name} exists
            output_img_dir = os.path.join(output_static_dir, f"images/generated/{plan_name}")
            if not os.path.exists(output_img_dir):
                os.makedirs(output_img_dir)
            
            output_coupon_path = os.path.join(output_img_dir, 'coupon.png')
            success = renderer.generate(data['coupon'], output_coupon_path)
            
            if success:
                # Calculate relative path for HTML use
                # output_static_dir is .../static
                # we saved to .../static/images/generated/{plan_name}/coupon.png
                # relative path: static/images/generated/{plan_name}/coupon.png
                rel_path = f"static/images/generated/{plan_name}/coupon.png"
                print(f"Coupon generated successfully at {output_coupon_path}")
                
                # Update campaign image URL in data object (In-memory update for Jinja)
                # Structure varies by plan/template. We attempt to find a 'campaign' or 'campaign_box' section.
                found_campaign = False
                
                # Strategy 1: Top-level 'campaign' key (if used)
                if 'campaign' in data:
                    data['campaign']['image_url'] = rel_path
                    found_campaign = True
                
                # Strategy 2: 'sections' list (standard/manga structure)
                if 'sections' in data:
                    for section in data['sections']:
                        if section['type'] == 'campaign_box' or section['type'] == 'campaign':
                            section['data']['image_url'] = rel_path
                            found_campaign = True
                            
                if found_campaign:
                    print(f"Updated campaign image URL to: {rel_path}")
                else:
                    print("Warning: Generated coupon but could not find a campaign section to attach it to.")
                    
        except Exception as e:
            print(f"Error generating coupon: {e}")

    print("Success! LP generation complete.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='LP Generator')
    parser.add_argument('input_file', nargs='?', default='input/sample_plan.json', help='Path to input JSON plan')
    parser.add_argument('--style', default='standard', help='Style to use (standard, manga, etc.)')
    args = parser.parse_args()
    
    generate_site(args.input_file, style=args.style)
