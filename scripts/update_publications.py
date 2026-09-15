import json
import os
import re
import shutil
import unicodedata
import urllib.request
from pathlib import Path
from datetime import datetime


PUBLICATIONS_URL = os.environ["PUBLICATIONS_URL"]

OUTPUT_DIR = Path("_publications")


def yaml_string(value):
    """Devuelve una cadena válida para YAML."""
    if value is None:
        value = ""
    return json.dumps(str(value), ensure_ascii=False)


def normalize_date(value):
    """
    Convierte la fecha de la BBDD a YYYY-MM-DD.
    """
    value = str(value or "").strip()

    if re.match(r"^\d{4}-\d{2}-\d{2}", value):
        candidate = value[:10]
        try:
            datetime.strptime(candidate, "%Y-%m-%d")
            return candidate
        except ValueError:
            pass

    if re.match(r"^\d{4}$", value):
        return f"{value}-01-01"

    return "1900-01-01"


def slugify(value):
    value = str(value)

    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii")

    value = re.sub(r"[^a-zA-Z0-9]+", "-", value)
    return value.strip("-").lower()


def publication_category(tipo):
    """
    Adapta esto a los valores reales de tipopubli de tu BBDD.
    """
    tipo = str(tipo or "").lower()

    if "libro" in tipo or "book" in tipo:
        return "books"

    if (
        "congreso" in tipo
        or "conference" in tipo
        or "proceeding" in tipo
    ):
        return "conferences"

    return "manuscripts"


# ---------------------------------------------------------
# Leer JSON
# ---------------------------------------------------------

with urllib.request.urlopen(PUBLICATIONS_URL) as response:
    publicaciones = json.load(response)


if not isinstance(publicaciones, list):
    raise ValueError("El JSON debe contener una lista de publicaciones.")


# ---------------------------------------------------------
# Preparar carpeta
# ---------------------------------------------------------

OUTPUT_DIR.mkdir(exist_ok=True)

# Borramos solo los archivos generados automáticamente.
for file in OUTPUT_DIR.glob("auto-*.md"):
    file.unlink()


# ---------------------------------------------------------
# Generar publicaciones
# ---------------------------------------------------------

for pub in publicaciones:

    pub_id = pub.get("id", "")
    titulo = pub.get("titulo", "")
    autores = pub.get("autores", [])
    tipo = pub.get("tipo", "")
    revista = pub.get("revista", "")
    volumen = pub.get("volumen", "")
    paginas = pub.get("paginas", "")
    editorial = pub.get("editorial", "")
    enlace = pub.get("enlace", "")
    issn = pub.get("issn", "")

    fecha = normalize_date(pub.get("fecha"))

    category = publication_category(tipo)

    identificador = slugify(pub_id)

    if not identificador:
        identificador = slugify(titulo)[:60]

    filename = OUTPUT_DIR / f"auto-{fecha}-{identificador}.md"

    permalink = f"/publication/{fecha}-{identificador}/"

    lines = [
        "---",
        f"title: {yaml_string(titulo)}",
        "collection: publications",
        f"category: {category}",
        f"permalink: {yaml_string(permalink)}",
        f"date: {fecha}",
        f"venue: {yaml_string(revista)}",
        f"volume: {yaml_string(volumen)}",
        f"pages: {yaml_string(paginas)}",
        f"publisher: {yaml_string(editorial)}",
        f"paperurl: {yaml_string(enlace)}",
        f"issn: {yaml_string(issn)}",
        f"publication_type: {yaml_string(tipo)}",
        "authors:"
    ]

    for autor in autores:
        lines.append(f"  - {yaml_string(autor)}")

    lines += [
        "---",
        ""
    ]

    filename.write_text(
        "\n".join(lines),
        encoding="utf-8"
    )

print(f"Generadas {len(publicaciones)} publicaciones.")
