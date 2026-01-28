TEMPLATE_CREATION_PROMPT = """
You are an expert Frontend Developer and UI/UX Designer.
You will be given multiple screenshots of a website (sections of a Landing Page).
Your goal is to create a reusable HTML/Tailwind CSS template that captures the COMMON layout structure and design system used across these screenshots.

# Instructions

1.  **Analyze the Design System**: Identify the color palette, typography (fonts, sizes), spacing system (padding/margin), and border radius used consistently.
2.  **Identify Common Components**: Look for recurring patterns like:
    *   Section containers (width, padding)
    *   Headers / Navigation bars (if visible)
    *   Typography styles (H1, H2, body text classes)
    *   Button styles
3.  **Ignore Specific Content**: Do NOT copy the specific text, images, or unique content of the screenshots. Instead, use placeholders.
    *   Use `Lorem ipsum` for text.
    *   Use `https://placehold.co/600x400` for images.
4.  **Create the Skeleton**: Write the HTML structure using Tailwind CSS classes that represents the *base layout* for these sections.
    *   Include a `<style>` block for any custom animations or fonts if needed (though Tailwind is preferred).
    *   Ensure the template is responsive.

# Output Format

Return ONLY the HTML code.
The code should be a complete `<html>` document (or a robust `<div>` wrapper if better) that can be used as a starting point for generating new sections.
"""

TEMPLATE_CREATION_SYSTEM_PROMPT = "You are an expert Tailwind developer. You extract design systems and layouts from screenshots to create reusable templates."
