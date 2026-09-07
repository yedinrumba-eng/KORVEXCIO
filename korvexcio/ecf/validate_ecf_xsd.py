"""Validate ECF XML templates against official DGII XSD schemas.

FASE 4.3: Preparación para validación XSD oficial DGII.
Uso: python validate_ecf_xsd.py --xsd-dir /ruta/xsd --xml-dir korvexcio/ecf/templates

Requiere: lxml (ya en requirements de Frappe)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from lxml import etree


def load_xsd_schemas(xsd_dir: Path) -> dict[str, etree.XMLSchema]:
    """Carga todos los archivos .xsd de un directorio y retorna dict {nombre: schema}.

    Args:
        xsd_dir: Directorio con archivos XSD oficiales DGII

    Returns:
        Dict mapeando nombre de archivo (sin .xsd) -> XMLSchema compilado
    """
    schemas = {}
    for xsd_file in xsd_dir.glob("*.xsd"):
        try:
            with open(xsd_file, "rb") as f:
                schema_doc = etree.parse(f)
                schema = etree.XMLSchema(schema_doc)
                schemas[xsd_file.stem] = schema
                print(f"✓ Cargado XSD: {xsd_file.name}")
        except etree.XMLSchemaParseError as e:
            print(f"✗ Error parseando XSD {xsd_file.name}: {e}", file=sys.stderr)
        except Exception as e:
            print(f"✗ Error cargando XSD {xsd_file.name}: {e}", file=sys.stderr)
    return schemas


def validate_xml_against_schema(xml_path: Path, schema: etree.XMLSchema) -> tuple[bool, list[str]]:
    """Valida un archivo XML contra un XMLSchema.

    Args:
        xml_path: Ruta al archivo XML a validar
        schema: XMLSchema compilado

    Returns:
        Tupla (es_valido, lista_de_errores)
    """
    errors = []
    try:
        with open(xml_path, "rb") as f:
            xml_doc = etree.parse(f)
        schema.assertValid(xml_doc)
        return True, []
    except etree.DocumentInvalid as e:
        # Extraer errores de validación
        for error in schema.error_log:
            errors.append(f"  Línea {error.line}, Col {error.column}: {error.message}")
        return False, errors
    except etree.XMLSyntaxError as e:
        errors.append(f"  Error de sintaxis XML: {e}")
        return False, errors
    except Exception as e:
        errors.append(f"  Error inesperado: {e}")
        return False, errors


def find_matching_schema(xml_path: Path, schemas: dict[str, etree.XMLSchema]) -> etree.XMLSchema | None:
    """Encuentra el schema apropiado para un XML basado en el nombre o contenido.

    Busca coincidencias por:
    1. Nombre de archivo (ecf.xml -> schema 'ecf' o 'E32')
    2. Elemento raíz del XML (e.g., <e-CF>, <RFCE>)
    """
    xml_name = xml_path.stem.lower()

    # Mapeo conocido DGII
    known_mapping = {
        "ecf": ["ecf", "e32", "e31", "e34", "factura", "nota_credito"],
        "rfce": ["rfce", "resumen", "summary"],
    }

    for schema_name, keywords in known_mapping.items():
        if schema_name in schemas:
            for kw in keywords:
                if kw in xml_name:
                    return schemas[schema_name]

    # Fallback: buscar por elemento raíz
    try:
        with open(xml_path, "rb") as f:
            root = etree.parse(f).getroot()
        root_tag = etree.QName(root).localname.lower()
        for schema_name in schemas:
            if schema_name.lower() in root_tag or root_tag in schema_name.lower():
                return schemas[schema_name]
    except Exception:
        pass

    # Último recurso: primer schema disponible
    if schemas:
        return next(iter(schemas.values()))

    return None


def main():
    parser = argparse.ArgumentParser(
        description="Validate ECF/RFCE XML templates against DGII XSD schemas"
    )
    parser.add_argument(
        "--xsd-dir",
        type=Path,
        required=True,
        help="Directorio con archivos XSD oficiales DGII (.xsd)",
    )
    parser.add_argument(
        "--xml-dir",
        type=Path,
        default=Path("korvexcio/ecf/templates"),
        help="Directorio con plantillas XML a validar (default: korvexcio/ecf/templates)",
    )
    parser.add_argument(
        "--xml-files",
        nargs="+",
        type=Path,
        help="Archivos XML específicos a validar (opcional, si no se da valida todo --xml-dir)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit code 1 si hay cualquier error de validación",
    )

    args = parser.parse_args()

    # Cargar schemas
    if not args.xsd_dir.exists():
        print(f"✗ Directorio XSD no existe: {args.xsd_dir}", file=sys.stderr)
        return 1

    schemas = load_xsd_schemas(args.xsd_dir)
    if not schemas:
        print("✗ No se pudo cargar ningún XSD válido", file=sys.stderr)
        return 1

    print(f"\n--- Validando XMLs ---\n")

    # Determinar archivos a validar
    if args.xml_files:
        xml_files = args.xml_files
    else:
        if not args.xml_dir.exists():
            print(f"✗ Directorio XML no existe: {args.xml_dir}", file=sys.stderr)
            return 1
        xml_files = list(args.xml_dir.glob("*.xml"))

    if not xml_files:
        print("✗ No se encontraron archivos XML para validar", file=sys.stderr)
        return 1

    all_valid = True
    results = []

    for xml_file in xml_files:
        print(f"Validando: {xml_file.name}")
        schema = find_matching_schema(xml_file, schemas)
        if schema is None:
            print(f"  ⚠ No hay schema coincidente, saltando")
            results.append((xml_file.name, False, ["No matching schema"]))
            all_valid = False
            continue

        valid, errors = validate_xml_against_schema(xml_file, schema)
        if valid:
            print(f"  ✓ VÁLIDO contra schema '{schema}'")
            results.append((xml_file.name, True, []))
        else:
            print(f"  ✗ INVÁLIDO:")
            for err in errors:
                print(f"    {err}")
            results.append((xml_file.name, False, errors))
            all_valid = False

    # Resumen
    print(f"\n--- Resumen ---")
    valid_count = sum(1 for _, v, _ in results if v)
    total = len(results)
    print(f"Válidos: {valid_count}/{total}")

    if args.strict and not all_valid:
        return 1

    return 0 if all_valid else 0  # 0 siempre salvo --strict


if __name__ == "__main__":
    sys.exit(main())