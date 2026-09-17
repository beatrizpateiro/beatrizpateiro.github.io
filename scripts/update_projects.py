import json
import os
import re
import unicodedata
import urllib.request
from pathlib import Path
from datetime import datetime


PROJECTS_URL = os.environ["PROJECTS_URL"]

OUTPUT_DIR = Path("_projects")


def yaml_string(value):
    """Devuelve una cadena segura para YAML."""
    if value is None:
        value = ""
    return json.dumps(str(value), ensure_ascii=False)


def slugify(value):
    value = str(value or "")

    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii")

    value = re.sub(r"[^a-zA-Z0-9]+", "-", value)

    return value.strip("-").lower()


def normalize_date(value):
    """
    Acepta YYYY-MM-DD o DD-MM-YYYY
    y devuelve YYYY-MM-DD.
    """

    value = str(value or "").strip()

    if not value:
        return ""

    # Ya viene en formato ISO
    if re.match(r"^\d{4}-\d{2}-\d{2}$", value):
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return value
        except ValueError:
            return ""

    # DD-MM-YYYY
    try:
        return datetime.strptime(
            value,
            "%d-%m-%Y"
        ).strftime("%Y-%m-%d")

    except ValueError:
        return ""


# ---------------------------------------------------------
# Leer JSON
# ---------------------------------------------------------

with urllib.request.urlopen(PROJECTS_URL) as response:
    proyectos = json.load(response)


if not isinstance(proyectos, list):
    raise ValueError("El JSON debe contener una lista de proyectos.")


# ---------------------------------------------------------
# Preparar carpeta
# ---------------------------------------------------------

OUTPUT_DIR.mkdir(exist_ok=True)

# Eliminamos únicamente los proyectos generados automáticamente.
for file in OUTPUT_DIR.glob("auto-*.md"):
    file.unlink()


# ---------------------------------------------------------
# Generar proyectos
# ---------------------------------------------------------

for proyecto in proyectos:

    project_id = proyecto.get("id", "")
    titulo = proyecto.get("titulo", "")
    referencia = proyecto.get("referencia", "")
    entidad = proyecto.get("entidad", "")
    tipo = proyecto.get("tipo", "")
    desde = proyecto.get("desde", "")
    hasta = proyecto.get("hasta", "")

    # Preferimos las fechas ISO que vienen del PHP.
    desde_iso = proyecto.get("desde_iso", "")
    hasta_iso = proyecto.get("hasta_iso", "")

    # Por seguridad, si no vienen, las calculamos.
    if not desde_iso:
        desde_iso = normalize_date(desde)

    if not hasta_iso:
        hasta_iso = normalize_date(hasta)

    identificador = slugify(project_id)

    # Si por algún motivo no hubiese ID
    if not identificador:
        identificador = slugify(titulo)[:60]

    filename = OUTPUT_DIR / f"auto-{identificador}.md"

    lines = [
        "---",
        f"title: {yaml_string(titulo)}",
        "collection: projects",
        f"project_id: {yaml_string(project_id)}",
        f"reference: {yaml_string(referencia)}",
        f"funding_entity: {yaml_string(entidad)}",
        f"project_type: {yaml_string(tipo)}",
        f"from: {yaml_string(desde)}",
        f"until: {yaml_string(hasta)}",
        f"start_date: {yaml_string(desde_iso)}",
        f"end_date: {yaml_string(hasta_iso)}",
        "---",
        ""
    ]

    filename.write_text(
        "\n".join(lines),
        encoding="utf-8"
    )


print(f"Generados {len(proyectos)} proyectos.")
