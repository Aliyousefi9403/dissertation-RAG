from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from mitreattack.stix20 import MitreAttackData
from stix2 import Filter, MemoryStore


# ------------------------------------------------------------------
# Paths
# ------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

MAPPING_FILE = (
    PROJECT_ROOT
    / "app"
    / "kb_builder"
    / "source_mapping.yaml"
)

ATTACK_STIX_FILE = (
    PROJECT_ROOT
    / "data"
    / "external"
    / "enterprise-attack.json"
)

CAPEC_STIX_FILE = (
    PROJECT_ROOT
    / "data"
    / "external"
    / "stix-capec.json"
)


# ------------------------------------------------------------------
# Configuration loading
# ------------------------------------------------------------------

def load_mapping() -> dict[str, Any]:
    """Load and validate the source-mapping YAML file."""

    if not MAPPING_FILE.exists():
        raise FileNotFoundError(
            f"Source mapping was not found:\n{MAPPING_FILE}"
        )

    with MAPPING_FILE.open("r", encoding="utf-8") as file:
        mapping = yaml.safe_load(file)

    if not isinstance(mapping, dict):
        raise ValueError(
            "source_mapping.yaml must contain a YAML dictionary."
        )

    attacks = mapping.get("attacks")

    if not isinstance(attacks, dict) or not attacks:
        raise ValueError(
            "source_mapping.yaml must contain a non-empty "
            "'attacks' dictionary."
        )

    return mapping


# ------------------------------------------------------------------
# ATT&CK loading
# ------------------------------------------------------------------

def load_attack_data() -> MitreAttackData:
    """Load the MITRE Enterprise ATT&CK STIX bundle."""

    if not ATTACK_STIX_FILE.exists():
        raise FileNotFoundError(
            f"MITRE ATT&CK STIX file was not found:\n"
            f"{ATTACK_STIX_FILE}"
        )

    return MitreAttackData(
        stix_filepath=str(ATTACK_STIX_FILE)
    )


def get_attack_id(attack_mapping: dict[str, Any]) -> str | None:
    """
    Find the Enterprise ATT&CK ID in either the primary source
    or supporting sources.
    """

    primary = attack_mapping.get("primary_source", {})

    if primary.get("system") == "MITRE_ATTACK_ENTERPRISE":
        return primary.get("id")

    for source in attack_mapping.get("supporting_sources", []):
        if source.get("system") == "MITRE_ATTACK_ENTERPRISE":
            return source.get("id")

    return None


def get_attack_technique(
    attack_data: MitreAttackData,
    attack_id: str,
):
    """Retrieve an active ATT&CK technique by external ATT&CK ID."""

    technique = attack_data.get_object_by_attack_id(
        attack_id,
        "attack-pattern",
    )

    if technique is None:
        raise ValueError(
            f"No active Enterprise ATT&CK technique was found "
            f"for {attack_id}."
        )

    return technique


# ------------------------------------------------------------------
# CAPEC loading
# ------------------------------------------------------------------

def load_capec_store() -> MemoryStore:
    """Load the official CAPEC STIX bundle into an in-memory store."""

    if not CAPEC_STIX_FILE.exists():
        raise FileNotFoundError(
            f"CAPEC STIX file was not found:\n{CAPEC_STIX_FILE}"
        )

    with CAPEC_STIX_FILE.open("r", encoding="utf-8") as file:
        bundle = json.load(file)

    objects = bundle.get("objects")

    if not isinstance(objects, list):
        raise ValueError(
            "The CAPEC STIX file does not contain an objects list."
        )

    return MemoryStore(stix_data=objects)


def get_capec_id(attack_mapping: dict[str, Any]) -> str | None:
    """Find the mapped CAPEC identifier."""

    primary = attack_mapping.get("primary_source", {})

    if primary.get("system") == "CAPEC":
        return primary.get("id")

    for source in attack_mapping.get("supporting_sources", []):
        if source.get("system") == "CAPEC":
            return source.get("id")

    return None


def get_external_id(stix_object: Any) -> str | None:
    """Read the first external identifier from a STIX object."""

    for reference in getattr(
        stix_object,
        "external_references",
        [],
    ):
        external_id = reference.get("external_id")

        if external_id:
            return external_id

    return None


def get_capec_pattern(
    capec_store: MemoryStore,
    capec_id: str,
):
    """Retrieve a CAPEC attack pattern by CAPEC identifier."""

    patterns = capec_store.query(
        [Filter("type", "=", "attack-pattern")]
    )

    for pattern in patterns:
        if get_external_id(pattern) == capec_id:
            return pattern

    raise ValueError(
        f"No CAPEC attack pattern was found for {capec_id}."
    )


# ------------------------------------------------------------------
# Markdown helpers
# ------------------------------------------------------------------

def normalise_items(value: Any) -> list[str]:
    """
    Convert STIX custom-property values into readable text items.
    """

    if value is None:
        return []

    if isinstance(value, str):
        return [value]

    if isinstance(value, list):
        items: list[str] = []

        for item in value:
            if isinstance(item, str):
                items.append(item)
            elif isinstance(item, dict):
                items.append(
                    "; ".join(
                        f"{key}: {item_value}"
                        for key, item_value in item.items()
                    )
                )
            else:
                items.append(str(item))

        return items

    if isinstance(value, dict):
        return [
            "; ".join(
                f"{key}: {item_value}"
                for key, item_value in value.items()
            )
        ]

    return [str(value)]


def append_section(
    lines: list[str],
    heading: str,
    values: list[str],
) -> None:
    """Append a Markdown section only when content exists."""

    cleaned = [
        value.strip()
        for value in values
        if value and value.strip()
    ]

    if not cleaned:
        return

    lines.extend([f"## {heading}", ""])

    if len(cleaned) == 1:
        lines.extend([cleaned[0], ""])
        return

    for value in cleaned:
        lines.append(f"- {value}")

    lines.append("")


def format_source_reference(source: dict[str, Any]) -> str:
    """Convert one YAML source entry into a readable reference."""

    system = source.get("system", "Unknown source")
    identifier = source.get("id") or source.get("document", "")
    role = source.get("role", "supporting_source")
    required = source.get("required", False)

    requirement = "required" if required else "optional"

    return (
        f"{system}: {identifier} "
        f"— role: {role}; {requirement}"
    )


# ------------------------------------------------------------------
# Markdown generation
# ------------------------------------------------------------------

def generate_markdown(
    attack_key: str,
    attack_mapping: dict[str, Any],
    capec_pattern: Any | None,
    attack_technique: Any | None,
    capec_id: str | None,
    attack_id: str | None,
) -> str:
    """Generate one structured, source-grounded knowledge document."""

    lines: list[str] = [
        f"# {attack_mapping['display_name']}",
        "",
        "## Metadata",
        "",
        f"- Attack key: `{attack_key}`",
        f"- Category: `{attack_mapping['category']}`",
        "- Origin: `clean`",
        "- Document status: `generated_from_authoritative_sources`",
    ]

    if capec_id:
        lines.append(f"- CAPEC ID: `{capec_id}`")

    if attack_id:
        lines.append(f"- ATT&CK ID: `{attack_id}`")

    lines.append("")

    if capec_pattern is not None:
        append_section(
            lines,
            "Attack description",
            normalise_items(
                getattr(capec_pattern, "description", None)
            ),
        )

        append_section(
            lines,
            "Execution flow",
            normalise_items(
                getattr(
                    capec_pattern,
                    "x_capec_execution_flow",
                    None,
                )
            ),
        )

        append_section(
            lines,
            "Prerequisites",
            normalise_items(
                getattr(
                    capec_pattern,
                    "x_capec_prerequisites",
                    None,
                )
            ),
        )

        append_section(
            lines,
            "Required resources",
            normalise_items(
                getattr(
                    capec_pattern,
                    "x_capec_resources_required",
                    None,
                )
            ),
        )

        append_section(
            lines,
            "Required skills",
            normalise_items(
                getattr(
                    capec_pattern,
                    "x_capec_skills_required",
                    None,
                )
            ),
        )

        append_section(
            lines,
            "Consequences",
            normalise_items(
                getattr(
                    capec_pattern,
                    "x_capec_consequences",
                    None,
                )
            ),
        )

        append_section(
            lines,
            "CAPEC mitigations",
            normalise_items(
                getattr(
                    capec_pattern,
                    "x_capec_mitigations",
                    None,
                )
            ),
        )

    if attack_technique is not None:
        lines.extend([
            "## ATT&CK adversary context",
            "",
            f"**Technique:** {attack_technique.name}",
            "",
            attack_technique.description,
            "",
        ])

        platforms = normalise_items(
            getattr(
                attack_technique,
                "x_mitre_platforms",
                None,
            )
        )

        append_section(
            lines,
            "Affected platforms",
            platforms,
        )

    lines.extend([
        "## Detection indicators",
        "",
        (
            "Detection content is not automatically inferred. "
            "It must be added from an explicitly mapped "
            "authoritative detection source and reviewed before "
            "experimental use."
        ),
        "",
        "## Prevention and mitigation",
        "",
        (
            "Mitigation guidance in this document is limited to "
            "content explicitly present in the mapped CAPEC or "
            "ATT&CK sources. OWASP, NIST, CISA, or other guidance "
            "must be ingested separately before being represented "
            "as source-derived content."
        ),
        "",
        "## Source mapping",
        "",
    ])

    primary_source = attack_mapping.get("primary_source")

    if isinstance(primary_source, dict):
        lines.append(
            f"- {format_source_reference(primary_source)}"
        )

    for source in attack_mapping.get("supporting_sources", []):
        lines.append(f"- {format_source_reference(source)}")

    lines.extend([
        "",
        "## Provenance",
        "",
        "- Generated automatically: yes",
        "- LLM-generated technical content: no",
        "- Human review required: yes",
        "- Source text preserved where supplied by STIX: yes",
        "",
    ])

    return "\n".join(lines)


# ------------------------------------------------------------------
# File output
# ------------------------------------------------------------------

def save_markdown(
    markdown: str,
    output_path: str,
) -> Path:
    """Write a generated Markdown document to disk."""

    output = PROJECT_ROOT / output_path

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        markdown,
        encoding="utf-8",
    )

    return output


# ------------------------------------------------------------------
# Build process
# ------------------------------------------------------------------

def main() -> None:
    mapping = load_mapping()
    attack_data = load_attack_data()
    capec_store = load_capec_store()

    attacks = mapping["attacks"]

    built = 0
    warnings = 0

    print(f"\nBuilding {len(attacks)} attack documents...\n")

    for attack_key, attack_mapping in attacks.items():
        display_name = attack_mapping["display_name"]

        print(f"Building {display_name}...")

        capec_id = get_capec_id(attack_mapping)
        attack_id = get_attack_id(attack_mapping)

        capec_pattern = None
        attack_technique = None

        if capec_id:
            try:
                capec_pattern = get_capec_pattern(
                    capec_store,
                    capec_id,
                )
            except ValueError as error:
                warnings += 1
                print(f"  Warning: {error}")

        if attack_id:
            try:
                attack_technique = get_attack_technique(
                    attack_data,
                    attack_id,
                )
            except ValueError as error:
                warnings += 1
                print(f"  Warning: {error}")

        if capec_pattern is None and attack_technique is None:
            warnings += 1
            print(
                "  Skipped: no usable CAPEC or ATT&CK "
                "source was found."
            )
            continue

        markdown = generate_markdown(
            attack_key=attack_key,
            attack_mapping=attack_mapping,
            capec_pattern=capec_pattern,
            attack_technique=attack_technique,
            capec_id=capec_id,
            attack_id=attack_id,
        )

        output = save_markdown(
            markdown,
            attack_mapping["output_path"],
        )

        built += 1
        print(f"  Saved: {output}")

    print("\nKnowledge-base build complete.")
    print(f"Built: {built}")
    print(f"Warnings: {warnings}")


if __name__ == "__main__":
    main()