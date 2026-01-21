from bs4 import BeautifulSoup
import json
import os

def extract_images(html_file):
    if not os.path.exists(html_file):
        print(f"File not found: {html_file}")
        return

    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()

    soup = BeautifulSoup(content, 'html.parser')
    
    images = []
    
    # Standard img tags
    for img in soup.find_all('img'):
        src = img.get('src')
        if src:
            images.append({'type': 'img', 'src': src, 'alt': img.get('alt', '')})
            
    # Next.js images often use style or other attributes, but let's check standard first
    # Also check for background images in inline styles if possible, though harder.
    
    # Check for OpenGraph image
    og_image = soup.find('meta', property='og:image')
    if og_image:
        images.append({'type': 'og:image', 'src': og_image.get('content')})

    print(json.dumps(images, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    extract_images('bihadado_markup.html')
