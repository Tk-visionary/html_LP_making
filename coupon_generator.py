import os
from PIL import Image, ImageDraw, ImageFont, ImageOps

class CouponRenderer:
    def __init__(self, template_dir='assets/templates/coupon', font_path='assets/fonts/NotoSansJP-Bold.otf'):
        self.template_dir = template_dir
        self.font_path = font_path
        self.default_font_size = 40
        
        # Color palettes for auto-styling
        self.palettes = {
            'gold': {
                'amount_color': '#FF0000', # Red for amount
                'title_color': '#333333',  # Dark text
                'text_color': '#555555',
                'target_bg': '#cc0000',    # Dark red bg for target
                'target_text': '#FFFFFF'   # White text
            },
            'pink': {
                'amount_color': '#FF69B4', # Pink for amount
                'title_color': '#555555',
                'text_color': '#777777',
                'target_bg': '#FF69B4',
                'target_text': '#FFFFFF'
            },
            'blue': {
                'amount_color': '#000080', # Navy for amount
                'title_color': '#333333',
                'text_color': '#555555',
                'target_bg': '#000080',
                'target_text': '#FFFFFF'
            }
        }

    def _get_font(self, size):
        try:
            return ImageFont.truetype(self.font_path, size)
        except OSError:
            # Fallback to default if font not found
            return ImageFont.load_default()

    def auto_style(self, template_id, element_type):
        """Returns default style for an element based on template."""
        palette = self.palettes.get(template_id, self.palettes['gold'])
        if element_type == 'amount':
            return {'color': palette['amount_color'], 'size': 150}
        elif element_type == 'title':
            return {'color': palette['title_color'], 'size': 60}
        elif element_type == 'target':
            return {'color': palette['target_text'], 'bg_color': palette['target_bg'], 'size': 40}
        else:
            return {'color': palette['text_color'], 'size': 30}

    def _apply_mask(self, image, shape_type='rounded', radius=30):
        """Applies a shape mask to the image for transparency."""
        mask = Image.new("L", image.size, 0)
        draw = ImageDraw.Draw(mask)
        w, h = image.size
        
        if shape_type == 'rounded':
            draw.rounded_rectangle((0, 0, w, h), radius=radius, fill=255)
        elif shape_type == 'ticket':
            # Draw rounded rect first
            draw.rounded_rectangle((0, 0, w, h), radius=radius, fill=255)
            # Cut out circles on sides
            cut_radius = 40
            cy = h // 2
            draw.ellipse((-cut_radius, cy - cut_radius, cut_radius, cy + cut_radius), fill=0) # Left
            draw.ellipse((w - cut_radius, cy - cut_radius, w + cut_radius, cy + cut_radius), fill=0) # Right
            
        output = ImageOps.fit(image, mask.size, centering=(0.5, 0.5))
        output.putalpha(mask)
        return output

    def generate(self, coupon_data, output_path):
        """
        Generates a coupon image based on data.
        coupon_data: dict containing 'template' and 'elements'
        output_path: where to save the image
        """
        template_id = coupon_data.get('template', 'gold')
        bg_path = os.path.join(self.template_dir, f"{template_id}.png")
        
        if not os.path.exists(bg_path):
            print(f"Warning: Template {template_id} not found. Falling back to gold.")
            bg_path = os.path.join(self.template_dir, "gold.png")
            template_id = 'gold'
            if not os.path.exists(bg_path):
                 print("Error: Base templates not found.")
                 return False

        # Open Background
        try:
            image = Image.open(bg_path).convert("RGBA")
            draw = ImageDraw.Draw(image)
            width, height = image.size
        except Exception as e:
            print(f"Error loading template: {e}")
            return False

        elements = coupon_data.get('elements', {}).copy()
        
        # Robustness: Check for misplaced elements at the top level
        # If user accidentally puts 'amount' or 'target' outside 'elements', capture them.
        known_keys = ['title', 'subtitle', 'target', 'amount', 'unit', 'off', 'message', 'condition', 'logo', 'description']
        for k, v in coupon_data.items():
             if k in known_keys and k not in elements and isinstance(v, dict):
                 print(f"Auto-repair: Found misplaced element '{k}' at top level. Merging into elements.")
                 elements[k] = v
        
        # Draw each element
        # Supported elements: text, image
        
        # -------------------------------------------------------------
        # Auto-Layout: Center Group (Amount + Unit)
        # -------------------------------------------------------------
        # If both 'amount' and 'unit' exist and don't have explicit custom positioning overrides that prevent this,
        # we calculate their total width and center them together.
        if 'amount' in elements and 'unit' in elements:
             # Check if we should auto-center (only if user hasn't forced weird positions)
             # We assume if they are close in Y, they are a group.
             amt_y = elements['amount'].get('y', 0.5)
             unit_y = elements['unit'].get('y', 0.5)
             
             # If they are roughly on the same line...
             if abs(amt_y - unit_y) < 0.2: 
                 print("Auto-Layout: Detected Amount + Unit group. Calculating centered position...")
                 
                 # 1. Measure Amount
                 amt_defaults = self.auto_style(template_id, 'amount')
                 amt_font = self._get_font(elements['amount'].get('size', amt_defaults['size']))
                 amt_bbox = draw.textbbox((0, 0), elements['amount']['text'], font=amt_font)
                 amt_w = amt_bbox[2] - amt_bbox[0]
                 
                 # 2. Measure Unit
                 unit_defaults = self.auto_style(template_id, 'unit')
                 unit_font = self._get_font(elements['unit'].get('size', unit_defaults['size']))
                 unit_bbox = draw.textbbox((0, 0), elements['unit']['text'], font=unit_font)
                 unit_w = unit_bbox[2] - unit_bbox[0]
                 
                 # 3. Calculate Total Width + Spacing
                 spacing = 20 # px
                 total_w = amt_w + spacing + unit_w
                 
                 # 4. Calculate Starting X
                 start_x = (width - total_w) // 2
                 
                 # 5. Update Elements with Calculated Absolute X and Align='left'
                 # We convert percentage X to absolute X by saving as integer, suppressing later calc
                 elements['amount']['x'] = start_x
                 elements['amount']['align'] = 'left' # Force left align relative to start_x
                 
                 elements['unit']['x'] = start_x + amt_w + spacing
                 elements['unit']['align'] = 'left'
                 
                 # Adjust Y to align baselines if needed (simple approach: keep existing relative Y)
                 # Or align centers? Let's trust the Y config for now but maybe nudge unit down?
                 # Often unit is smaller and needs to sit on baseline. 
                 # For now, we trust the JSON's Y relative positioning for vertical alignment.

        # -------------------------------------------------------------
        
        for key, config in elements.items():
            element_type = config.get('type', 'text')
            
            if element_type == 'image':
                # Image Compositing
                img_path = config.get('path', '')
                if not img_path or not os.path.exists(img_path):
                    print(f"Warning: Image element {key} path not found: {img_path}")
                    continue
                
                try:
                    overlay = Image.open(img_path).convert("RGBA")
                    
                    # Resize if needed
                    if 'width' in config and 'height' in config:
                        overlay = overlay.resize((config['width'], config['height']), Image.Resampling.LANCZOS)
                    elif 'scale' in config:
                         new_size = (int(overlay.width * config['scale']), int(overlay.height * config['scale']))
                         overlay = overlay.resize(new_size, Image.Resampling.LANCZOS)

                    # Position
                    img_w, img_h = overlay.size
                    
                    # Y Position
                    if 'y' in config:
                        if isinstance(config['y'], float):
                            y = int(height * config['y'])
                        else:
                            y = int(config['y'])
                    else:
                        y = 0

                    # X Position
                    if 'x' in config:
                        if isinstance(config['x'], float):
                            x = int(width * config['x'])
                        else:
                            x = int(config['x'])
                        
                        align = config.get('align', 'center')
                        if align == 'center':
                            x = x - int(img_w / 2)
                        elif align == 'right':
                            x = x - img_w
                    else:
                        x = int((width - img_w) / 2)
                        
                    image.alpha_composite(overlay, (x, y))
                    
                except Exception as e:
                    print(f"Error drawing image element {key}: {e}")
                
                continue

            # Text Rendering
            text = config.get('text', '')
            if not text: continue

            # Determine Style
            defaults = self.auto_style(template_id, key)
            color = config.get('color', defaults.get('color'))
            bg_color = config.get('bg_color', defaults.get('bg_color'))
            size = config.get('size', defaults.get('size'))
            
            font = self._get_font(size)
            
            # Measure text
            # textbbox returns (left, top, right, bottom)
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            # Position
            # Default Y positions based on logical order if not specified
            if 'y' in config:
                if isinstance(config['y'], float):
                    y = int(height * config['y'])
                else:
                    y = int(config['y'])
            else:
                # Basic auto-layout based on key name
                if key == 'title': y = int(height * 0.25)
                elif key == 'amount': y = int(height * 0.5)
                elif key == 'target': y = int(height * 0.15)
                else: y = int(height * 0.8)

            # X Position
            if 'x' in config:
                if isinstance(config['x'], float):
                    x = int(width * config['x'])
                else:
                    x = int(config['x'])
                
                # Handling Alignment when X is specified
                align = config.get('align', 'center')
                if align == 'center':
                    x = x - int(text_width / 2)
                elif align == 'right':
                    x = x - text_width
                # if 'left', x is already correct
            else:
                # Default Center
                x = int((width - text_width) / 2)
            
            # Background (e.g. for Target badge)
            if bg_color:
                padding = 15
                bg_box = [
                    x - padding, 
                    y - padding, 
                    x + text_width + padding, 
                    y + text_height + padding
                ]
                draw.rectangle(bg_box, fill=bg_color, outline=None)
            
            # Draw Text
            draw.text((x, y), text, font=font, fill=color)

        # Apply Shape Mask if requested
        shape = coupon_data.get('shape')
        if shape:
            image = self._apply_mask(image, shape_type=shape)

        # Save
        image.save(output_path)
        print(f"Coupon generated at {output_path}")
        return True

if __name__ == "__main__":
    # Test run
    renderer = CouponRenderer()
    data = {
        "template": "gold",
        "elements": {
            "title": {"text": "OFF Coupon", "y": 0.3},
            "amount": {"text": "¥3,000", "y": 0.45},
            "target": {"text": "First Time Users", "y": 0.15},
            "condition": {"text": "Valid until 12/31", "y": 0.75, "size": 30}
        }
    }
    renderer.generate(data, "test_coupon.png")
