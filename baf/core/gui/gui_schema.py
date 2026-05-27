"""JSON Schema and validation utilities for the GUIModel format."""
import json


def validate_json(json_str: str) -> bool:
    """Validate a JSON string against the GUIModel JSON Schema.

    Requires the ``jsonschema`` package (``pip install jsonschema``).

    Args:
        json_str: JSON string to validate.

    Returns:
        ``True`` if valid, ``False`` otherwise.
    """
    try:
        import jsonschema
        data = json.loads(json_str)
        jsonschema.validate(instance=data, schema=get_json_schema())
        return True
    except Exception:
        return False


def get_json_schema() -> dict:
    """Return the JSON Schema for a serialized :class:`~besser.BUML.metamodel.gui.graphical_ui.GUIModel`.

    The schema is designed to be passed to an LLM as a generation constraint.
    All element types are discriminated by the ``"type"`` field.

    Returns:
        A ``dict`` containing a JSON Schema (draft-07) for the GUIModel format.
    """
    styling_schema = {
        "type": "object",
        "description": "Visual styling. All sub-properties are optional.",
        "properties": {
            "size": {
                "type": "object",
                "description": "Size/font CSS properties.",
                "properties": {
                    "width": {"type": "string", "examples": ["100%", "300px", "auto"]},
                    "height": {"type": "string", "examples": ["200px", "auto"]},
                    "min_width": {"type": "string"},
                    "max_width": {"type": "string"},
                    "min_height": {"type": "string"},
                    "max_height": {"type": "string"},
                    "padding": {"type": "string"},
                    "padding_top": {"type": "string"},
                    "padding_right": {"type": "string"},
                    "padding_bottom": {"type": "string"},
                    "padding_left": {"type": "string"},
                    "margin": {"type": "string"},
                    "margin_top": {"type": "string"},
                    "margin_right": {"type": "string"},
                    "margin_bottom": {"type": "string"},
                    "margin_left": {"type": "string"},
                    "font_size": {"type": "string", "examples": ["14px", "1rem"]},
                    "font_weight": {"type": "string", "examples": ["normal", "bold", "600"]},
                    "font_family": {"type": "string"},
                    "line_height": {"type": "string"},
                },
                "additionalProperties": True,
            },
            "position": {
                "type": "object",
                "description": "Positioning CSS properties.",
                "properties": {
                    "p_type": {"type": "string", "enum": ["static", "relative", "absolute", "fixed", "sticky"]},
                    "top": {"type": "string"},
                    "left": {"type": "string"},
                    "right": {"type": "string"},
                    "bottom": {"type": "string"},
                    "display": {"type": "string", "enum": ["flex", "grid", "block", "inline", "inline-block", "none"]},
                    "overflow": {"type": "string", "enum": ["visible", "hidden", "scroll", "auto"]},
                    "z_index": {"type": "integer"},
                    "visibility": {"type": "string", "enum": ["visible", "hidden"]},
                    "cursor": {"type": "string"},
                },
                "additionalProperties": True,
            },
            "color": {
                "type": "object",
                "description": "Color and border CSS properties.",
                "properties": {
                    "background_color": {"type": "string", "examples": ["#ffffff", "rgba(0,0,0,0.5)"]},
                    "text_color": {"type": "string"},
                    "border_color": {"type": "string"},
                    "border_radius": {"type": "string", "examples": ["4px", "50%"]},
                    "border_width": {"type": "string"},
                    "border_style": {"type": "string", "enum": ["solid", "dashed", "dotted", "none"]},
                    "border": {"type": "string", "examples": ["1px solid #ccc"]},
                    "opacity": {"type": "number", "minimum": 0, "maximum": 1},
                    "box_shadow": {"type": "string"},
                    "color_palette": {"type": "array", "items": {"type": "string"}},
                    "primary_color": {"type": "string"},
                    "fill_color": {"type": "string"},
                },
                "additionalProperties": True,
            },
            "layout": {
                "type": "object",
                "description": "Flexbox/Grid layout properties.",
                "properties": {
                    "layout_type": {"type": "string", "enum": ["flex", "grid", "block"]},
                    "flex_direction": {"type": "string", "enum": ["row", "column", "row-reverse", "column-reverse"]},
                    "justify_content": {"type": "string", "enum": ["flex-start", "flex-end", "center", "space-between", "space-around", "space-evenly"]},
                    "align_items": {"type": "string", "enum": ["flex-start", "flex-end", "center", "stretch", "baseline"]},
                    "flex_wrap": {"type": "string", "enum": ["nowrap", "wrap", "wrap-reverse"]},
                    "gap": {"type": "string", "examples": ["8px", "16px 8px"]},
                    "grid_template_columns": {"type": "string", "examples": ["repeat(3, 1fr)", "1fr 2fr"]},
                    "grid_gap": {"type": "string"},
                    "flex_grow": {"type": "number"},
                    "flex_shrink": {"type": "number"},
                    "flex_basis": {"type": "string"},
                    "flex": {"type": "string"},
                    "order": {"type": "integer"},
                    "align_self": {"type": "string"},
                },
                "additionalProperties": True,
            },
        },
        "additionalProperties": False,
    }

    series_schema = {
        "type": "object",
        "description": "A single data series for a chart.",
        "required": ["name"],
        "properties": {
            "name": {"type": "string", "description": "Series key, e.g. 'revenue'."},
            "label": {"type": "string", "description": "Human-readable legend label, e.g. 'Revenue 2024'."},
            "styling": styling_schema,
        },
    }

    column_schema = {
        "type": "object",
        "required": ["type", "label"],
        "properties": {
            "type": {"type": "string", "enum": ["Column", "FieldColumn", "LookupColumn", "ExpressionColumn"]},
            "label": {"type": "string"},
            "field": {"type": "string", "description": "Field name for FieldColumn/LookupColumn."},
            "path": {"type": "string", "description": "Lookup path attribute name for LookupColumn."},
            "expression": {"type": "string", "description": "Computed expression for ExpressionColumn."},
        },
    }

    base_props = {
        "name": {"type": "string", "description": "Unique element identifier."},
        "description": {"type": "string"},
        "component_id": {"type": "string", "description": "HTML id attribute."},
        "tag_name": {"type": "string", "description": "HTML tag override, e.g. 'div'."},
        "css_classes": {"type": "array", "items": {"type": "string"}},
        "custom_attributes": {"type": "object", "description": "Arbitrary extra attributes (values stored as JSON strings)."},
        "display_order": {"type": "number"},
        "styling": styling_schema,
        "type": {"type": "string"},
    }

    chart_props = {
        "title": {"type": "string"},
        "primary_color": {"type": "string"},
        "series": {
            "type": "array",
            "items": series_schema,
            "description": (
                "Data series definitions. To provide actual data points, set "
                "custom_attributes.series to a JSON-encoded array of objects "
                "where each object has string keys matching series names plus a "
                "'label' key for the x-axis, "
                "e.g. [{\"label\": \"Jan\", \"revenue\": 1200, \"cost\": 800}]."
            ),
        },
        "show_legend": {"type": "boolean", "default": True},
        "legend_position": {"type": "string", "enum": ["top", "bottom", "left", "right"], "default": "top"},
        "show_tooltip": {"type": "boolean", "default": True},
        "animate": {"type": "boolean", "default": True},
    }

    element_defs = {
        "ViewContainer": {
            "type": "object",
            "description": "A layout container that groups child elements.",
            "required": ["type", "name"],
            "properties": {
                **base_props,
                "type": {"type": "string", "const": "ViewContainer"},
                "layout": {
                    "type": "object",
                    "description": "Container layout configuration.",
                    "properties": {
                        "layout_type": {"type": "string", "enum": ["flex", "grid", "block"]},
                        "flex_direction": {"type": "string"},
                        "justify_content": {"type": "string"},
                        "align_items": {"type": "string"},
                        "gap": {"type": "string"},
                        "grid_template_columns": {"type": "string"},
                    },
                    "additionalProperties": True,
                },
                "view_elements": {"type": "array", "items": {"$ref": "#/$defs/ViewElement"}, "default": []},
            },
        },
        "Text": {
            "type": "object",
            "description": "A text or heading element.",
            "required": ["type", "name", "content"],
            "properties": {
                **base_props,
                "type": {"type": "string", "const": "Text"},
                "content": {"type": "string", "description": "Text content to display."},
            },
        },
        "Button": {
            "type": "object",
            "description": "A clickable button.",
            "required": ["type", "name", "label"],
            "properties": {
                **base_props,
                "type": {"type": "string", "const": "Button"},
                "label": {"type": "string"},
                "buttonType": {"type": "string", "enum": ["Raised Button", "Flat Button", "Icon Button", "FAB", "Stroked Button", "Toggle Button"], "default": "Raised Button"},
                "actionType": {"type": "string", "enum": ["navigate", "submit", "create", "update", "delete", "custom"], "default": "navigate"},
                "targetScreen": {"type": "string", "description": "Screen name to navigate to."},
                "confirmation_required": {"type": "boolean", "default": False},
                "confirmation_message": {"type": "string"},
            },
        },
        "Link": {
            "type": "object",
            "description": "A hyperlink element.",
            "required": ["type", "name"],
            "properties": {
                **base_props,
                "type": {"type": "string", "const": "Link"},
                "label": {"type": "string"},
                "url": {"type": "string"},
                "target": {"type": "string", "enum": ["_self", "_blank", "_parent", "_top"]},
                "rel": {"type": "string"},
            },
        },
        "Image": {
            "type": "object",
            "description": "An image element.",
            "required": ["type", "name"],
            "properties": {
                **base_props,
                "type": {"type": "string", "const": "Image"},
                "source": {"type": "string", "description": "Image URL or path."},
            },
        },
        "InputField": {
            "type": "object",
            "description": "A form input field.",
            "required": ["type", "name"],
            "properties": {
                **base_props,
                "type": {"type": "string", "const": "InputField"},
                "field_type": {"type": "string", "enum": ["text", "number", "email", "password", "date", "datetime", "time", "tel", "url", "checkbox", "radio", "select", "textarea", "file", "color"], "default": "text"},
                "validationRules": {"type": "object"},
            },
        },
        "Form": {
            "type": "object",
            "description": "A form grouping input fields.",
            "required": ["type", "name"],
            "properties": {
                **base_props,
                "type": {"type": "string", "const": "Form"},
                "inputFields": {"type": "array", "items": {"$ref": "#/$defs/ViewElement"}, "default": []},
            },
        },
        "Menu": {
            "type": "object",
            "description": "A navigation menu.",
            "required": ["type", "name"],
            "properties": {
                **base_props,
                "type": {"type": "string", "const": "Menu"},
                "menuItems": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["label"],
                        "properties": {
                            "label": {"type": "string"},
                            "url": {"type": "string"},
                            "target": {"type": "string"},
                            "rel": {"type": "string"},
                        },
                    },
                    "default": [],
                },
            },
        },
        "DataList": {
            "type": "object",
            "description": "A list bound to a data source.",
            "required": ["type", "name"],
            "properties": {**base_props, "type": {"type": "string", "const": "DataList"}},
        },
        "EmbeddedContent": {
            "type": "object",
            "description": "Embedded external content (iframe, video, etc.).",
            "required": ["type", "name"],
            "properties": {
                **base_props,
                "type": {"type": "string", "const": "EmbeddedContent"},
                "source": {"type": "string"},
                "content_type": {"type": "string", "enum": ["iframe", "video", "audio", "object", "embed"]},
                "extra_props": {"type": "object"},
            },
        },
        "LineChart": {
            "type": "object",
            "description": "A line chart.",
            "required": ["type", "name"],
            "properties": {
                **base_props,
                **chart_props,
                "type": {"type": "string", "const": "LineChart"},
                "line_width": {"type": "integer", "default": 2},
                "show_grid": {"type": "boolean", "default": True},
                "curve_type": {"type": "string", "enum": ["linear", "monotone", "step"], "default": "monotone"},
                "dot_size": {"type": "integer", "default": 4},
                "grid_color": {"type": "string"},
            },
        },
        "BarChart": {
            "type": "object",
            "description": "A bar/column chart.",
            "required": ["type", "name"],
            "properties": {
                **base_props,
                **chart_props,
                "type": {"type": "string", "const": "BarChart"},
                "bar_width": {"type": "integer", "default": 20},
                "orientation": {"type": "string", "enum": ["vertical", "horizontal"], "default": "vertical"},
                "show_grid": {"type": "boolean", "default": True},
                "stacked": {"type": "boolean", "default": False},
                "bar_gap": {"type": "integer", "default": 4},
                "grid_color": {"type": "string"},
            },
        },
        "PieChart": {
            "type": "object",
            "description": "A pie or donut chart. Set inner_radius > 0 for a donut.",
            "required": ["type", "name"],
            "properties": {
                **base_props,
                **chart_props,
                "type": {"type": "string", "const": "PieChart"},
                "show_labels": {"type": "boolean", "default": True},
                "label_position": {"type": "string", "enum": ["inside", "outside", "center"], "default": "outside"},
                "padding_angle": {"type": "number", "default": 0},
                "inner_radius": {"type": "number", "default": 0, "description": "Set > 0 for a donut chart."},
                "outer_radius": {"type": "number", "default": 80},
                "start_angle": {"type": "number", "default": 0},
                "end_angle": {"type": "number", "default": 360},
            },
        },
        "RadarChart": {
            "type": "object",
            "description": "A radar / spider chart.",
            "required": ["type", "name"],
            "properties": {
                **base_props,
                **chart_props,
                "type": {"type": "string", "const": "RadarChart"},
                "show_grid": {"type": "boolean", "default": True},
                "show_radius_axis": {"type": "boolean", "default": True},
                "dot_size": {"type": "integer", "default": 3},
                "grid_type": {"type": "string", "enum": ["polygon", "circle"], "default": "polygon"},
                "stroke_width": {"type": "integer", "default": 2},
            },
        },
        "RadialBarChart": {
            "type": "object",
            "description": "A radial bar chart.",
            "required": ["type", "name"],
            "properties": {
                **base_props,
                **chart_props,
                "type": {"type": "string", "const": "RadialBarChart"},
                "start_angle": {"type": "number", "default": 0},
                "end_angle": {"type": "number", "default": 360},
                "inner_radius": {"type": "number", "default": 30},
                "outer_radius": {"type": "number", "default": 80},
            },
        },
        "Table": {
            "type": "object",
            "description": "A data table with configurable columns.",
            "required": ["type", "name"],
            "properties": {
                **base_props,
                "type": {"type": "string", "const": "Table"},
                "title": {"type": "string"},
                "primary_color": {"type": "string"},
                "show_header": {"type": "boolean", "default": True},
                "striped_rows": {"type": "boolean", "default": False},
                "show_pagination": {"type": "boolean", "default": False},
                "rows_per_page": {"type": "integer", "default": 5},
                "columns": {"type": "array", "items": column_schema, "default": []},
                "action_buttons": {"type": "boolean", "default": False},
            },
        },
        "MetricCard": {
            "type": "object",
            "description": "A KPI / metric card.",
            "required": ["type", "name"],
            "properties": {
                **base_props,
                "type": {"type": "string", "const": "MetricCard"},
                "metric_title": {"type": "string", "default": "Metric Title"},
                "format": {"type": "string", "enum": ["number", "currency", "percentage", "time"], "default": "number"},
                "value_color": {"type": "string", "default": "#2c3e50"},
                "value_size": {"type": "integer", "default": 32},
                "show_trend": {"type": "boolean", "default": True},
                "positive_color": {"type": "string", "default": "#27ae60"},
                "negative_color": {"type": "string", "default": "#e74c3c"},
                "title": {"type": "string"},
                "primary_color": {"type": "string"},
            },
        },
        "AgentComponent": {
            "type": "object",
            "description": "Embeds a BESSER agent chat interface.",
            "required": ["type", "name"],
            "properties": {
                **base_props,
                "type": {"type": "string", "const": "AgentComponent"},
                "agent_name": {"type": "string", "description": "Name of the agent diagram to reference."},
                "agent_title": {"type": "string", "description": "Display title shown in the UI."},
            },
        },
    }

    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "GUIModel",
        "description": (
            "A BESSER GUI model describing screens and their view elements. "
            "Produced by gui_to_json() and accepted by json_to_gui()."
        ),
        "type": "object",
        "required": ["name", "modules"],
        "properties": {
            "name": {"type": "string", "description": "Model name."},
            "package": {"type": "string", "description": "Package identifier, e.g. 'com.example.app'."},
            "versionCode": {"type": "integer", "default": 1},
            "versionName": {"type": "string", "default": "1.0"},
            "description": {"type": "string"},
            "style_entries": {"type": "object", "description": "Global style overrides."},
            "modules": {
                "type": "array",
                "description": "Logical screen groups.",
                "items": {
                    "type": "object",
                    "required": ["name", "screens"],
                    "properties": {
                        "name": {"type": "string"},
                        "screens": {"type": "array", "items": {"$ref": "#/$defs/Screen"}},
                    },
                },
            },
        },
        "$defs": {
            "Styling": styling_schema,
            "Screen": {
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "screen_size": {"type": "string", "enum": ["Small", "Medium", "Large", "ExtraLarge"], "default": "Medium"},
                    "is_main_page": {"type": "boolean", "default": False},
                    "route_path": {"type": "string", "examples": ["/", "/dashboard", "/profile"]},
                    "x_dpi": {"type": "string"},
                    "y_dpi": {"type": "string"},
                    "component_id": {"type": "string"},
                    "tag_name": {"type": "string"},
                    "css_classes": {"type": "array", "items": {"type": "string"}},
                    "custom_attributes": {"type": "object"},
                    "layout": {
                        "type": "object",
                        "properties": {
                            "layout_type": {"type": "string", "enum": ["flex", "grid", "block"]},
                            "flex_direction": {"type": "string"},
                            "justify_content": {"type": "string"},
                            "align_items": {"type": "string"},
                            "gap": {"type": "string"},
                            "grid_template_columns": {"type": "string"},
                        },
                        "additionalProperties": True,
                    },
                    "styling": {"$ref": "#/$defs/Styling"},
                    "view_elements": {"type": "array", "items": {"$ref": "#/$defs/ViewElement"}, "default": []},
                },
            },
            "ViewElement": {
                "description": (
                    "Any view element — discriminated by the required 'type' field. "
                    "Valid types: ViewContainer, Text, Button, Link, Image, InputField, "
                    "Form, Menu, DataList, EmbeddedContent, LineChart, BarChart, PieChart, "
                    "RadarChart, RadialBarChart, Table, MetricCard, AgentComponent."
                ),
                "oneOf": [{"$ref": f"#/$defs/{k}"} for k in element_defs],
            },
            "Series": series_schema,
            "Column": column_schema,
            **element_defs,
        },
    }
