"""
Generate a TOML configuration file from the Pydantic Settings model.

!!!WARNING!!!
This code was mostly written by Kagi Code Assistant, it's inefficient and will likely break a lot.

Chat log: https://gist.github.com/aceat64/8e54e271df02b0275fe700d0a2f62531
"""

from typing import Any


def toml_serialize_value(value: Any) -> str:
    """
    Serialize a value to TOML format.
    """
    if value is None:
        return "null"
    elif isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, int | float):
        return str(value)
    elif isinstance(value, str):
        # Escape special characters and wrap in quotes
        escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t")
        return f'"{escaped}"'
    elif isinstance(value, list):
        # Handle empty list
        if not value:
            return "[]"

        # Check if all items are of the same simple type (str, int, float, bool)
        all_simple = all(isinstance(item, str | int | float | bool) for item in value)

        # For simple types, use inline array format
        if all_simple:
            items = []
            for item in value:
                if isinstance(item, str):
                    # Escape special characters in strings
                    escaped = item.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t")
                    items.append(f'"{escaped}"')
                elif isinstance(item, bool):
                    items.append("true" if item else "false")
                else:
                    items.append(str(item))

            # For string arrays, add extra space after commas for readability
            return f"[{', '.join(items)}]"

        # For complex types (nested arrays, objects), use multiline format
        else:
            result = ["["]
            for item in value:
                serialized = toml_serialize_value(item)
                # Indent each line of the serialized item
                indented = "  " + serialized.replace("\n", "\n  ")
                result.append(indented + ",")
            result.append("]")
            return "\n".join(result)

    # For unsupported types, just use string representation
    return f'"{value!s}"'


def json_schema_to_toml(schema: dict[str, Any]) -> str:
    """
    Convert a JSON schema to TOML format.
    """
    result: list[str] = []

    # Store definitions for resolving references
    definitions: dict[str, Any] = {}
    if "$defs" in schema:
        definitions = schema["$defs"]

    def resolve_ref(ref: str) -> dict[str, Any] | None:
        """
        Resolve a JSON Schema reference.
        """
        if ref.startswith("#/$defs/"):
            ref_path = ref[len("#/$defs/") :].split("/")
            current = definitions
            for path_part in ref_path:
                if path_part in current:
                    current = current[path_part]
                else:
                    return None
            return current
        return None

    def normalize(text: str) -> str:
        """
        Normalize text for case-insensitive comparison by lowercasing and replacing spaces with underscores.
        """
        return text.lower().replace(" ", "_")

    def get_type_comment(prop: dict[str, Any]) -> list[str]:
        """
        Generate type and enum comments for a property.
        """
        comments: list[str] = []

        # Handle anyOf for multiple types
        if "anyOf" in prop:
            types: list[str] = []
            for type_option in prop["anyOf"]:
                if "type" in type_option:
                    prop_type = type_option["type"]
                    if prop_type == "array" and "items" in type_option:
                        items_type = type_option["items"].get("type", "Any")
                        types.append(f"list[{items_type}]")
                    else:
                        types.append(prop_type)
            if types:
                comments.append(f"# Type: {' | '.join(types)}")

        # Handle regular type
        elif "type" in prop:
            prop_type = prop["type"]
            if prop_type == "array" and "items" in prop:
                items_type = prop["items"].get("type", "Any")
                comments.append(f"# Type: list[{items_type}]")
            elif prop_type != "object":  # Skip type comments for objects
                comments.append(f"# Type: {prop_type}")

        # Handle enum values
        if prop.get("enum"):
            enum_values = prop["enum"]
            # Format enum values based on their type
            formatted_values = []
            for val in enum_values:
                if isinstance(val, str):
                    formatted_values.append(f'"{val}"')
                elif val is None:
                    formatted_values.append("None")
                else:
                    formatted_values.append(str(val))

            if formatted_values:
                comments.append(f"# Allowed values: [{', '.join(formatted_values)}]")

        return comments

    def get_example_comments(prop: dict[str, Any], name: str) -> list[str]:
        """
        Generate comments for example values.
        """
        comments: list[str] = []

        # Skip examples for objects
        if prop.get("type") == "object":
            return comments

        # Handle examples field (always a list)
        if "examples" in prop:
            examples = prop["examples"]
            if examples:  # Only add header if there are examples
                if len(examples) == 1:
                    comments.append("# Example:")
                else:
                    comments.append("# Examples:")

                for example in examples:
                    # Use custom serialization for consistent formatting
                    serialized_value = toml_serialize_value(example)
                    comments.append(f"# {name} = {serialized_value}")

        return comments

    def process_property(name: str, prop: dict[str, Any], parent_path: str = "") -> None:
        """
        Process a property and add it to the result.
        """
        # Handle references
        if "$ref" in prop:
            ref_value = prop["$ref"]
            resolved_prop = resolve_ref(ref_value)
            if resolved_prop:
                # Merge any properties from the original with the resolved reference
                merged_prop = {
                    **resolved_prop,
                    **{k: v for k, v in prop.items() if k != "$ref"},
                }
                process_property(name, merged_prop, parent_path)
                return
            else:
                # If reference can't be resolved, add a comment
                result.append(f"# Unresolved reference: {ref_value}")
                result.append(f"# {name} = null")
                return

        # Prepare title and description as comments
        title_comments = []
        description_comments = []

        # Only add title if it's different from the property name (case-insensitive, spaces as underscores)
        if "title" in prop and normalize(prop["title"]) != normalize(name):
            title_comments.append(f"# {prop['title']}")

        # Handle multi-line descriptions by commenting each line
        if "description" in prop:
            description = prop["description"]
            # Split description into lines and comment each line
            for line in description.split("\n"):
                description_comments.append(f"# {line}")

        # Get type and enum comments
        type_comments = get_type_comment(prop)

        # Get example comments
        example_comments = get_example_comments(prop, name)

        # Handle nested objects
        if prop.get("type") == "object" and "properties" in prop:
            # For objects, we need to create a section
            path = f"{parent_path}.{name}" if parent_path else name

            # Add section header for objects (except at root level)
            if name:  # Skip for root object
                result.append(f"[{path}]")
                # Add description comments after section header
                result.extend(description_comments)
                # Add blank line after description
                result.append("")
            else:
                # For root object, add all comments
                result.extend(title_comments)
                result.extend(description_comments)

            # Sort properties: non-objects first, then objects
            properties = prop["properties"]
            non_object_props = {
                k: v for k, v in properties.items() if not (v.get("type") == "object" and "properties" in v)
            }
            object_props = {k: v for k, v in properties.items() if v.get("type") == "object" and "properties" in v}

            # Process non-object properties first
            for sub_name, sub_prop in non_object_props.items():
                process_property(sub_name, sub_prop, path)

            # Then process object properties
            for sub_name, sub_prop in object_props.items():
                process_property(sub_name, sub_prop, path)

        # Handle arrays
        elif prop.get("type") == "array" and "items" in prop:
            # Combine comments
            comments = title_comments + description_comments + type_comments + example_comments
            result.extend(comments)

            if "default" in prop:
                default_value = prop["default"]
                if default_value is None:
                    # Only add commented null value if there are no examples
                    if "examples" not in prop:
                        result.append(f"# {name} = []")
                else:
                    serialized_value = toml_serialize_value(default_value)
                    result.append(f"{name} = {serialized_value}")
            else:
                result.append(f"{name} = []")

        # Handle primitive types
        else:
            # Combine comments
            comments = title_comments + description_comments + type_comments + example_comments
            result.extend(comments)

            if "default" in prop:
                default_value = prop["default"]

                # Comment out None/null values
                if default_value is None:
                    # Only add commented null value if there are no examples
                    if "examples" not in prop:
                        result.append(f"# {name} = null")
                else:
                    # Use custom serialization
                    serialized_value = toml_serialize_value(default_value)
                    result.append(f"{name} = {serialized_value}")
            else:
                # Add placeholder based on type
                type_map = {
                    "string": '""',
                    "integer": "0",
                    "number": "0.0",
                    "boolean": "false",
                    "null": "null",
                }

                # If type is null, comment out the line
                if prop.get("type") == "null":
                    # Only add commented null value if there are no examples
                    if "examples" not in prop:
                        result.append(f"# {name} = null")
                else:
                    # For enum, use the first value as default if available
                    if prop.get("enum"):
                        default_value = prop["enum"][0]
                        if default_value is not None:
                            serialized_value = toml_serialize_value(default_value)
                            result.append(f"{name} = {serialized_value}")
                        else:
                            # Only add commented null value if there are no examples
                            if "examples" not in prop:
                                result.append(f"# {name} = null")
                    # For anyOf, use the first type as default
                    elif "anyOf" in prop and prop["anyOf"] and "type" in prop["anyOf"][0]:
                        first_type = prop["anyOf"][0]["type"]
                        type_val = type_map.get(first_type, "null")
                        result.append(f"{name} = {type_val}")
                    else:
                        type_val = type_map.get(prop.get("type", "null"), "null")
                        result.append(f"{name} = {type_val}")

        result.append("")

    # Start processing from root
    if "properties" in schema:
        # Sort properties: non-objects first, then objects
        properties = schema["properties"]
        non_object_props = {
            k: v for k, v in properties.items() if not (v.get("type") == "object" and "properties" in v)
        }
        object_props = {k: v for k, v in properties.items() if v.get("type") == "object" and "properties" in v}
        # Process non-object properties first
        for prop_name, prop_schema in non_object_props.items():
            process_property(prop_name, prop_schema, "")

        # Then process object properties
        for prop_name, prop_schema in object_props.items():
            process_property(prop_name, prop_schema, "")

    return "\n".join(result)
