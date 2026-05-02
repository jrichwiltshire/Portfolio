import json
import sys
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

TEMPLATES_DIR = Path(__file__).parent / "templates"


def generate(data: dict, output_path: str, template_name: str = "resume.html"):
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template(template_name)
    html_content = template.render(**data)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html_content).write_pdf(output_path)
    print(f"PDF written to {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: pdf_generator.py <data.json> <output.pdf> [template.html]")
        sys.exit(1)

    template_name = sys.argv[3] if len(sys.argv) > 3 else "resume.html"

    with open(sys.argv[1]) as f:
        data = json.load(f)

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template(template_name)
    html_content = template.render(**data)
    Path(sys.argv[2]).parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html_content).write_pdf(sys.argv[2])
    print(f"PDF written to {sys.argv[2]}")
