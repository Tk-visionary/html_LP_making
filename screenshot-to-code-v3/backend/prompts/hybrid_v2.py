USER_PROMPT = """You are an expert Frontend Developer.
You are processing ONE SECTION of a larger landing page design.
Your goal is to fully RECREATE this section in HTML/Tailwind CSS.

### CRITICAL INSTRUCTIONS:
1.  **Full Reconstruction**: 
    -   Do **NOT** use the input image as a background image for the whole section.
    -   You MUST convert all text in the image to real HTML text.
    -   You MUST create real HTML buttons, forms, and layouts using Tailwind classes.
    -   The input image is a REFERENCE for the design (colors, spacing, layout), not an asset to be embedded.

2.  **Visual Accuracy**:
    -   Match the background color, text color, font sizes, and padding exactly.
    -   Use the exact **text color** from the screenshot.
    -   ALSO, pay attention to the background color of the text. If the text is white or light, the background MUST be dark or colored. Match the text+background combination exactly.
    -   If the section has a specific background color, apply it to the `<section>` tag.

3.  **Images**:
    -   For photos or illustrations inside the section: Use CSS `background-image` with `background-position` and `background-size` to clip and display ONLY that region from the original screenshot. The original image URL will be provided as `__SCREENSHOT_URL__`. Output a comment like `/* Image region: top:XXpx, left:XXpx, width:XXpx, height:XXpx */` before the element.
    -   Extract exact background colors from the screenshot (e.g., `#f0f0f0`). Do NOT guess colors.

4.  **Output Format**:
    -   Return a single `<section>` element containing the code.
    -   Do not include `<html>`, `<head>`, or `<body>` tags.
    -   Do not output markdown backticks.

5.  **Animation**:
    -   Add a subtle floating animation to the main CTA button using Tailwind: `animate-bounce` (modified) or standard CSS.
    -   Or use this class if available: `.animate-float`.

Recreate the section pixel-perfectly using Tailwind CSS.
"""
