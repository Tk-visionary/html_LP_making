"""
Image cropping and background removal utilities for extracting regions from screenshots.
"""
import base64
import io
import os
import re
import uuid
from pathlib import Path
from typing import Optional, Tuple, List, Dict
from PIL import Image
from rembg import remove, new_session

# Pre-load rembg sessions for different models
_rembg_sessions = {}

def get_rembg_session(model_name: str):
    """Get or create a rembg session for the specified model."""
    if model_name not in _rembg_sessions:
        print(f"[REMBG] Loading model: {model_name}")
        _rembg_sessions[model_name] = new_session(model_name)
    return _rembg_sessions[model_name]


# Directory for storing cropped images
CROPPED_IMAGES_DIR = Path(__file__).parent.parent / "static" / "cropped"


def ensure_cropped_dir(session_id: str) -> Path:
    """Ensure the directory for cropped images exists."""
    session_dir = CROPPED_IMAGES_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir


def decode_base64_image(data_url: str) -> Tuple[Image.Image, str]:
    """
    Decode a base64 data URL into a PIL Image.
    
    Args:
        data_url: Base64 data URL (e.g., "data:image/png;base64,...")
        
    Returns:
        Tuple of (PIL Image, media_type)
    """
    # Extract media type and base64 data
    match = re.match(r'data:([^;]+);base64,(.+)', data_url)
    if not match:
        raise ValueError("Invalid data URL format")
    
    media_type = match.group(1)
    base64_data = match.group(2)
    image_bytes = base64.b64decode(base64_data)
    
    img = Image.open(io.BytesIO(image_bytes))
    return img, media_type


def crop_image(
    image: Image.Image,
    left: int,
    top: int,
    width: int,
    height: int,
) -> Image.Image:
    """
    Crop an image to the specified region.
    
    Args:
        image: PIL Image to crop
        left: X coordinate of top-left corner
        top: Y coordinate of top-left corner
        width: Width of the crop region
        height: Height of the crop region
        
    Returns:
        Cropped PIL Image
    """
    # Ensure coordinates are within bounds
    left = max(0, left)
    top = max(0, top)
    right = min(image.width, left + width)
    bottom = min(image.height, top + height)
    
    return image.crop((left, top, right, bottom))


def save_cropped_image(
    image: Image.Image,
    session_id: str,
    index: int,
    format: str = "PNG",
) -> str:
    """
    Save a cropped image to a file.
    
    Args:
        image: PIL Image to save
        session_id: Session ID for organizing files
        index: Index of the image (for unique naming)
        format: Image format (PNG, JPEG, etc.)
        
    Returns:
        URL path to the saved image (relative to static root)
    """
    session_dir = ensure_cropped_dir(session_id)
    
    # Generate unique filename
    filename = f"crop_{index}_{uuid.uuid4().hex[:8]}.{format.lower()}"
    filepath = session_dir / filename
    
    # Convert to RGB if saving as JPEG and image has alpha
    if format.upper() == "JPEG" and image.mode in ("RGBA", "LA", "P"):
        image = image.convert("RGB")
    
    image.save(filepath, format=format)
    
    # Return full URL path with backend host for iframe preview
    # TODO: Get this from environment variable in production
    backend_url = os.environ.get("BACKEND_URL", "http://localhost:7003")
    return f"{backend_url}/static/cropped/{session_id}/{filename}"


def remove_background(image: Image.Image, image_type: str = "general") -> Image.Image:
    """
    Remove background from an image using rembg.
    
    Args:
        image: PIL Image to process
        image_type: 'human' for u2net_human_seg, 'general' for isnet-general-use
        
    Returns:
        PIL Image with transparent background
    """
    # Select model based on image type
    if image_type == "human":
        model_name = "u2net_human_seg"
    else:
        model_name = "isnet-general-use"
    
    print(f"[REMBG] Removing background with model: {model_name}")
    
    # Get cached session
    session = get_rembg_session(model_name)
    
    # Remove background
    result = remove(image, session=session)
    
    return result


def parse_image_region_comments(html: str) -> List[Dict]:
    """
    Parse image region comments from HTML.
    
    Expected format: /* Image region: top:XXpx, left:XXpx, width:XXpx, height:XXpx, type:human */
    
    Args:
        html: HTML string with image region comments
        
    Returns:
        List of dicts with keys: top, left, width, height, type, comment_text
    """
    # Pattern matches both CSS /* */ and HTML <!-- --> comments
    css_pattern = r'/\*\s*Image region:\s*top:\s*(\d+)px?,?\s*left:\s*(\d+)px?,?\s*width:\s*(\d+)px?,?\s*height:\s*(\d+)px?(?:,?\s*type:\s*(\w+))?\s*\*/'
    html_pattern = r'<!--\s*Image region:\s*top:\s*(\d+)px?,?\s*left:\s*(\d+)px?,?\s*width:\s*(\d+)px?,?\s*height:\s*(\d+)px?(?:,?\s*type:\s*(\w+))?\s*-->'
    
    regions = []
    
    # Match CSS-style comments
    for match in re.finditer(css_pattern, html, re.IGNORECASE):
        image_type = match.group(5) if match.group(5) else "general"
        regions.append({
            "top": int(match.group(1)),
            "left": int(match.group(2)),
            "width": int(match.group(3)),
            "height": int(match.group(4)),
            "type": image_type.lower(),
            "comment_text": match.group(0),
        })
    
    # Match HTML-style comments
    for match in re.finditer(html_pattern, html, re.IGNORECASE):
        image_type = match.group(5) if match.group(5) else "general"
        regions.append({
            "top": int(match.group(1)),
            "left": int(match.group(2)),
            "width": int(match.group(3)),
            "height": int(match.group(4)),
            "type": image_type.lower(),
            "comment_text": match.group(0),
        })
    
    return regions


def process_image_regions(
    html: str,
    screenshot_data_url: str,
    session_id: str,
) -> str:
    """
    Process HTML to extract image regions, crop them from the screenshot,
    save as files, and replace URLs in HTML.
    
    Args:
        html: Generated HTML with image region comments
        screenshot_data_url: Base64 data URL of the original screenshot
        session_id: Session ID for organizing cropped files
        
    Returns:
        Updated HTML with image URLs replaced
    """
    regions = parse_image_region_comments(html)
    
    print(f"[IMAGE CROPPING] Found {len(regions)} image regions to process")
    print(f"[IMAGE CROPPING] Screenshot URL length: {len(screenshot_data_url) if screenshot_data_url else 0}")
    
    updated_html = html
    
    if regions:
        try:
            screenshot, _ = decode_base64_image(screenshot_data_url)
            print(f"[IMAGE CROPPING] Screenshot size: {screenshot.width}x{screenshot.height}")
        except Exception as e:
            print(f"[IMAGE CROPPING] Failed to decode screenshot: {e}")
            # Fallback: just replace all __SCREENSHOT_URL__ with the data URL
            updated_html = updated_html.replace("__SCREENSHOT_URL__", screenshot_data_url)
            return updated_html
        
        for idx, region in enumerate(regions):
            try:
                # Crop the region
                cropped = crop_image(
                    screenshot,
                    left=region["left"],
                    top=region["top"],
                    width=region["width"],
                    height=region["height"],
                )
                
                # Remove background based on type
                image_type = region.get("type", "general")
                print(f"[IMAGE PROCESSING] Region {idx}: type={image_type}")
                
                try:
                    cropped = remove_background(cropped, image_type)
                    print(f"[IMAGE PROCESSING] Background removed for region {idx}")
                except Exception as bg_error:
                    print(f"[IMAGE PROCESSING] Background removal failed for region {idx}: {bg_error}")
                    # Continue with original cropped image
                
                # Save to file (PNG for transparency support)
                image_url = save_cropped_image(cropped, session_id, idx, format="PNG")
                
                print(f"[IMAGE CROPPING] Saved crop {idx}: {region['width']}x{region['height']} -> {image_url}")
                
                # Find the element after this comment and replace its src/background-image
                comment = region["comment_text"]
                comment_pos = updated_html.find(comment)
                
                if comment_pos != -1:
                    # Search within the next 1000 characters after the comment
                    search_start = comment_pos + len(comment)
                    search_end = min(search_start + 1000, len(updated_html))
                    section = updated_html[search_start:search_end]
                    
                    replaced = False
                    
                    # Try replacing __SCREENSHOT_URL__ first
                    if "__SCREENSHOT_URL__" in section:
                        updated_section = section.replace("__SCREENSHOT_URL__", image_url, 1)
                        updated_html = updated_html[:search_start] + updated_section + updated_html[search_end:]
                        print(f"[IMAGE CROPPING] Replaced __SCREENSHOT_URL__ for region {idx}")
                        replaced = True
                    
                    # If not found, try replacing base64 data URL in src attribute
                    if not replaced:
                        # Pattern to find src="data:image/..." or src='data:image/...'
                        base64_pattern = r'src=["\']data:image/[^"\']+["\']'
                        match = re.search(base64_pattern, section)
                        if match:
                            new_src = f'src="{image_url}"'
                            updated_section = section[:match.start()] + new_src + section[match.end():]
                            updated_html = updated_html[:search_start] + updated_section + updated_html[search_end:]
                            print(f"[IMAGE CROPPING] Replaced base64 src for region {idx}")
                            replaced = True
                    
                    if not replaced:
                        print(f"[IMAGE CROPPING] Warning: No image URL found to replace for region {idx}")
                
            except Exception as e:
                print(f"[IMAGE CROPPING] Error processing region {idx}: {e}")
                continue
    
    # Fallback: Replace any remaining __SCREENSHOT_URL__ with the original screenshot data URL
    remaining_count = updated_html.count("__SCREENSHOT_URL__")
    if remaining_count > 0:
        print(f"[IMAGE CROPPING] Replacing {remaining_count} remaining __SCREENSHOT_URL__ with original")
        updated_html = updated_html.replace("__SCREENSHOT_URL__", screenshot_data_url)
    
    return updated_html


def process_manual_regions(
    screenshot_data_url: str,
    regions: List[Dict],
    session_id: str,
) -> Dict[str, str]:
    """
    Process manually specified regions from the frontend.
    
    Args:
        screenshot_data_url: Base64 data URL of the screenshot
        regions: List of dicts with keys: id, top, left, width, height, type
        session_id: Session ID for organizing cropped files
        
    Returns:
        Dict mapping region ID to cropped image URL
    """
    print(f"[MANUAL REGIONS] Processing {len(regions)} regions")
    
    if not regions:
        return {}
    
    try:
        screenshot, _ = decode_base64_image(screenshot_data_url)
        print(f"[MANUAL REGIONS] Screenshot size: {screenshot.width}x{screenshot.height}")
    except Exception as e:
        print(f"[MANUAL REGIONS] Failed to decode screenshot: {e}")
        return {}
    
    result = {}
    
    for idx, region in enumerate(regions):
        try:
            region_id = region.get("id", f"region_{idx}")
            region_type = region.get("type", "general")
            
            # Map frontend type to backend type
            type_mapping = {
                "human": "human",
                "hero": "general",
                "coupon": "general", 
                "illustration": "general",
            }
            image_type = type_mapping.get(region_type, "general")
            
            # Crop the region
            cropped = crop_image(
                screenshot,
                left=int(region["left"]),
                top=int(region["top"]),
                width=int(region["width"]),
                height=int(region["height"]),
            )
            
            print(f"[MANUAL REGIONS] Cropped region {region_id}: {region['width']}x{region['height']}, type={region_type}")
            
            # Remove background
            try:
                cropped = remove_background(cropped, image_type)
                print(f"[MANUAL REGIONS] Background removed for {region_id}")
            except Exception as bg_error:
                print(f"[MANUAL REGIONS] Background removal failed for {region_id}: {bg_error}")
            
            # Save to file
            image_url = save_cropped_image(cropped, session_id, idx, format="PNG")
            result[region_id] = image_url
            
            print(f"[MANUAL REGIONS] Saved {region_id} -> {image_url}")
            
        except Exception as e:
            print(f"[MANUAL REGIONS] Error processing region {region.get('id', idx)}: {e}")
            continue
    
    return result
