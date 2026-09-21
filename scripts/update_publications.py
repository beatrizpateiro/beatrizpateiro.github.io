import json
import os
import re
import unicodedata
import urllib.request
import urllib.error
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
    """Convierte un valor en una cadena adecuada para usar en URLs."""
    value = str(value or "")

    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii")

    value = re.sub(r"[^a-zA-Z0-9]+", "-", value)
    return value.strip("-").lower()


def publication_category(tipo):
    """
    Clasifica la publicación según el campo 'tipo'.
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


# =========================================================
# LEER JSON
# =========================================================

print(f"Leyendo publicaciones desde: {PUBLICATIONS_URL}")

request = urllib.request.Request(
    PUBLICATIONS_URL,
    headers={
        "User-Agent": (
            "Mozilla/5.0 "
            "(compatible; BeatrizPateiroPublications/1.0)"
        ),
        "Accept": "application/json,text/plain,*/*",
    },
)


try:

    with urllib.request.urlopen(request, timeout=30) as response:

        status = response.status
        final_url = response.geturl()
        content_type = response.headers.get("Content-Type", "")

        raw_content = response.read()

except urllib.error.HTTPError as error:

    raise RuntimeError(
        f"Error HTTP al descargar las publicaciones: "
        f"{error.code} {error.reason}"
    ) from error

except urllib.error.URLError as error:

    raise RuntimeError(
        f"No se pudo conectar con {PUBLICATIONS_URL}: "
        f"{error.reason}"
    ) from error


print(f"HTTP status: {status}")
print(f"URL final: {final_url}")
print(f"Content-Type: {content_type}")
print(f"Bytes recibidos: {len(raw_content)}")


# ---------------------------------------------------------
# Comprobar que la respuesta no está vacía
# ---------------------------------------------------------

if not raw_content.strip():
    raise RuntimeError(
        "El servidor ha devuelto una respuesta vacía."
    )


# ---------------------------------------------------------
# Convertir respuesta a texto
#
# utf-8-sig elimina automáticamente un posible BOM UTF-8
# ---------------------------------------------------------

try:
    content = raw_content.decode("utf-8")
except UnicodeDecodeError as error:
    raise RuntimeError(
        "La respuesta del servidor no está codificada en UTF-8."
    ) from error

# Eliminar BOM y posibles espacios/saltos de línea al principio
content = content.lstrip("\ufeff \t\r\n")


# ---------------------------------------------------------
# Interpretar JSON
# ---------------------------------------------------------

try:
    publicaciones = json.loads(content)

except json.JSONDecodeError as error:

    preview = content[:500].replace("\n", " ")

    raise RuntimeError(
        "La respuesta recibida no es JSON válido.\n"
        f"URL final: {final_url}\n"
        f"Content-Type: {content_type}\n"
        f"Primeros caracteres recibidos:\n{preview}"
    ) from error


if not isinstance(publicaciones, list):
    raise ValueError(
        "El JSON debe contener una lista de publicaciones."
    )


print(f"Publicaciones recibidas: {len(publicaciones)}")


# =========================================================
# PREPARAR CARPETA
# =========================================================

OUTPUT_DIR.mkdir(exist_ok=True)

# Borramos solo los archivos generados automáticamente.
for file in OUTPUT_DIR.glob("auto-*.md"):
    file.unlink()


# =========================================================
# GENERAR PUBLICACIONES
# =========================================================

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
        "authors:",
    ]

    if isinstance(autores, list):

        for autor in autores:
            lines.append(f"  - {yaml_string(autor)}")

    else:

        # Por si algún registro devuelve autores como texto
        lines.append(f"  - {yaml_string(autores)}")

    lines += [
        "---",
        "",
    ]

    filename.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


print(f"Generadas {len(publicaciones)} publicaciones.")
