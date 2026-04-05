# Design System Specification: The Luminous Journal

## 1. Overview & Creative North Star
**Creative North Star: The Living Heirloom**
This design system rejects the cold, sterile efficiency of healthcare applications in favor of a "Living Heirloom"—a digital space that feels as tactile and cherished as a linen-bound journal. We are moving away from the "app" feel toward an editorial sanctuary.

To achieve this, the system breaks the standard rigid grid through **Intentional Asymmetry**. Large serif headlines should feel "placed" rather than "slotted," and elements should use overlapping layers to create a sense of physical depth. We treat the screen not as a flat plane, but as a series of parchment sheets illuminated by a soft, warm hearth.

---

### 2. Colors & Surface Philosophy
The palette is rooted in the earth (Forest) and the hearth (Amber), set against a foundation of aged paper (Cream).

*   **Primary (`#456255`):** Reserved for moments of grounding and authority. Use for primary actions and deep-toned sections.
*   **Secondary (`#8a5100`):** Our "Amber" spark. Use sparingly for highlights, active states, or moments of "memory clarity."
*   **Surface Hierarchy:**
    *   `surface-container-lowest`: Use for the main background "page."
    *   `surface-container-low` to `high`: Use to create nested "nooks" of information.

**The "No-Line" Rule**
Traditional 1px borders are strictly prohibited. To separate a card from the background, shift the surface token (e.g., a `surface-container-low` card on a `surface` background). Structure must be felt through tonal shifts, never through drawn lines.

**Signature Textures & Glows**
Avoid flat color blocks. Use the `tertiary-container` (`#c5a85d`) with a high-radius radial blur to create "Luminous Halos" behind key content. This mimics bioluminescence, guiding the user’s eye naturally without the harshness of a spotlight.

---

### 3. Typography
We use a high-contrast typographic scale to evoke the feeling of a premium wellness publication.

*   **Display & Headlines (Newsreader/Playfair Display):** These are our "Voice." Large, serif, and authoritative. Use `display-lg` for landing moments and `headline-md` for section titles. Let them breathe; use generous leading.
*   **Body & Titles (Manrope/DM Sans):** Our "Guide." These sans-serifs provide the clarity needed for cognitive support. They should always be set in `on-surface-variant` or `on-surface` to ensure maximum legibility against the cream backgrounds.
*   **The Narrative Scale:** Typography should never be "crowded." If a headline is `headline-lg`, ensure the surrounding white space is at least `spacing-12` to maintain the editorial cadence.

---

### 4. Elevation & Depth
In this system, depth is organic, not synthetic.

*   **The Layering Principle:** Stack surfaces like sheets of fine paper. A "floating" action button or a modal shouldn't just sit on top; it should feel like it has been placed there.
*   **Ambient Shadows:** If a shadow is required for a floating element, use a multi-layered blur: 
    *   `box-shadow: 0 10px 30px rgba(29, 28, 21, 0.05), 0 4px 8px rgba(29, 28, 21, 0.03);`
    *   The shadow must be tinted with the `on-surface` color (`#1d1c15`), never pure black.
*   **The "Ghost Border" Fallback:** If accessibility requires a container edge, use the `outline-variant` token at **15% opacity**. It should be a suggestion of a border, not a hard stop.

---

### 5. Components

*   **Buttons:**
    *   *Primary:* Solid `primary` (`#456255`) with `on-primary` text. Use `rounded-lg` (1rem). 
    *   *Secondary:* `secondary-container` background. These should feel like "warm highlights."
    *   *Tertiary:* Text only, using `primary` color with an underline that appears only on hover.
*   **Cards & Memory Tiles:**
    *   No borders. Use `surface-container-low` for the card body. 
    *   Apply a soft `tertiary-fixed-dim` glow behind cards that contain "active" memories or reminders.
*   **Input Fields:**
    *   Use a "Minimalist Journal" style: A background of `surface-container-highest` with a slightly darker `outline-variant` bottom edge. 
    *   Focus state: The bottom edge glows with the `secondary` (Amber) token.
*   **Progress Indicators:**
    *   Avoid circular "spinners." Use a slow-expanding "Luminous Pulse" (a soft amber radial gradient that fades in and out).
*   **Additional Component: The "Memory Beacon":**
    *   A specialized chip for dementia care. A `secondary-fixed` background with a soft glow, used to highlight the most important piece of information on a page (e.g., a loved one's name or a time of day).

---

### 6. Do's and Don'ts

**Do:**
*   **Do** use intentional white space. If in doubt, add `spacing-8`.
*   **Do** use "Slow Reveal" motion. Elements should float upward by 10px as they fade in over 800ms.
*   **Do** use the `secondary` (Amber) color to signify "Hope" and "Success."

**Don't:**
*   **Don't** use pure black (`#000000`) or pure white (`#FFFFFF`). Use the system's cream and dark forest tones.
*   **Don't** use sharp corners. Everything must have a minimum of `rounded-md` to feel approachable and "soft."
*   **Don't** use dividers. If you feel the need for a line, try using a `spacing-10` gap instead.
*   **Don't** use rapid, "snappy" animations. We are building for cognitive calm; 200ms transitions are too aggressive for this experience. Use 600ms minimum.

---

### 7. Motion & Interaction
Motion is the "breath" of this design system. 
*   **The "Float" Reveal:** When a page loads, elements should stagger their entrance. The header arrives at 0ms, the main content at 200ms, and action buttons at 400ms.
*   **Duration:** All transitions must sit between **600ms and 900ms** with a `cubic-bezier(0.22, 1, 0.36, 1)` easing curve for a graceful, decelerating finish.