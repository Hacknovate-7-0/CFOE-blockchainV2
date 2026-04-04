"""
Registry Agent - Entity registry validation and lookup
"""

# Mock registry database (in production, this would be an API call)
ENTITY_REGISTRY = {
    "REFOE001MP": {
        "name": "Midwest Petroleum Refinery",
        "sector": "refinery",
        "status": "active",
        "registration_date": "2023-01-15"
    },
    "TXTOE007PB": {
        "name": "Pacific Basin Textiles",
        "sector": "textiles",
        "status": "active",
        "registration_date": "2023-03-22"
    },
    "ALMOE003EU": {
        "name": "European Aluminium Corp",
        "sector": "aluminium",
        "status": "active",
        "registration_date": "2023-02-10"
    },
    "PETOE009AS": {
        "name": "Asia Petrochemicals Ltd",
        "sector": "petrochemicals",
        "status": "active",
        "registration_date": "2023-04-05"
    }
}

def validate_registry_id(registry_id: str) -> dict:
    """
    Validate entity registry ID and return entity info.
    
    Args:
        registry_id: Entity registration ID (e.g., REFOE001MP)
    
    Returns:
        dict with validation status and entity info
    """
    if not registry_id or registry_id.strip() == "":
        return {
            "valid": False,
            "error": "Registry ID is required",
            "entity": None
        }
    
    registry_id = registry_id.strip().upper()
    
    if registry_id in ENTITY_REGISTRY:
        entity = ENTITY_REGISTRY[registry_id]
        return {
            "valid": True,
            "registry_id": registry_id,
            "entity": entity,
            "error": None
        }
    else:
        return {
            "valid": False,
            "error": f"Registry ID '{registry_id}' not found in entity database",
            "entity": None,
            "suggestion": "Please verify the registration number format (e.g., REFOE001MP, TXTOE007PB)"
        }

def get_entity_info(registry_id: str) -> dict:
    """
    Get entity information by registry ID.
    
    Args:
        registry_id: Entity registration ID
    
    Returns:
        Entity information or None
    """
    result = validate_registry_id(registry_id)
    return result.get("entity") if result.get("valid") else None
