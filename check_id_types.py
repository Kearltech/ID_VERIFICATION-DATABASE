"""Quick script to check ID type keys"""
from id_field_mappings import ID_TYPE_REGISTRY

print("Available ID types:")
for key in ID_TYPE_REGISTRY.keys():
    print(f"  - {key}")
