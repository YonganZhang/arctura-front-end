"""Fix SVG text z-ordering: move all <text> elements to the end of their
parent group so they render on top of rectangles/lines/circles.

Usage:
    python fix_svg_text_zorder.py [file_or_dir]

    # Fix one file
    python fix_svg_text_zorder.py studio-demo/arch-mvp/arch-11/floor-F2.svg

    # Fix all SVGs under a directory (recursive)
    python fix_svg_text_zorder.py studio-demo/
"""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# SVG namespace
NS = {"svg": "http://www.w3.org/2000/svg"}
ET.register_namespace("", "http://www.w3.org/2000/svg")
ET.register_namespace("inkscape", "http://www.inkscape.org/namespaces/inkscape")
ET.register_namespace("sodipodi", "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd")


def fix_text_zorder(svg_path: Path) -> bool:
    """Move all <text> elements to the end of their parent <g> group.

    Returns True if any reordering was done.
    """
    tree = ET.parse(str(svg_path))
    root = tree.getroot()
    changed = False

    # Process all group elements (and root if it directly contains text)
    containers = [root] + list(root.iter("{http://www.w3.org/2000/svg}g")) + list(root.iter("g"))

    for parent in containers:
        children = list(parent)
        text_elements = []
        non_text_elements = []

        for child in children:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag == "text":
                text_elements.append(child)
            else:
                non_text_elements.append(child)

        if not text_elements:
            continue

        # Check if text is already all at the end
        first_text_idx = next(
            i for i, c in enumerate(children)
            if (c.tag.split("}")[-1] if "}" in c.tag else c.tag) == "text"
        )
        last_non_text_idx = max(
            (i for i, c in enumerate(children)
             if (c.tag.split("}")[-1] if "}" in c.tag else c.tag) != "text"),
            default=-1,
        )

        if first_text_idx > last_non_text_idx:
            continue  # text is already on top, no fix needed

        # Reorder: non-text first, then text
        for child in children:
            parent.remove(child)
        for child in non_text_elements:
            parent.append(child)
        for child in text_elements:
            parent.append(child)
        changed = True

    if changed:
        # Write back with XML declaration
        tree.write(str(svg_path), encoding="unicode", xml_declaration=True)

    return changed


def main():
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("studio-demo/")

    if target.is_file():
        svg_files = [target]
    else:
        svg_files = sorted(target.rglob("*.svg"))

    fixed = 0
    skipped = 0
    for svg_path in svg_files:
        try:
            if fix_text_zorder(svg_path):
                print(f"  FIXED  {svg_path}")
                fixed += 1
            else:
                skipped += 1
        except Exception as e:
            print(f"  ERROR  {svg_path}: {e}")

    print(f"\nDone. Fixed: {fixed}, Already OK: {skipped}, Total: {fixed + skipped}")


if __name__ == "__main__":
    main()
