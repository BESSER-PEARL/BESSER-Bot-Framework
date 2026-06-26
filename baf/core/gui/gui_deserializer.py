"""Deserialization helpers: JSON string → GUIModel."""
import json
from types import SimpleNamespace

from baf.exceptions.logger import logger

try:
    from besser.BUML.metamodel.gui.graphical_ui import (
        GUIModel, Module, Screen,
        ViewElement, ViewContainer, ViewComponent,
        Button, Text, Image, InputField, Form, Menu, MenuItem,
        DataList, EmbeddedContent, Link,
        Alert, AlertSeverity, SelectOption,
    )
    from besser.BUML.metamodel.gui.style import Styling, Size, Position, Color, Layout
    from besser.BUML.metamodel.gui.dashboard import (
        LineChart, BarChart, PieChart, RadarChart, RadialBarChart,
        Table, MetricCard, AgentComponent, Series,
        Column, FieldColumn, LookupColumn, ExpressionColumn,
    )
except ImportError:
    logger.warning("besser dependencies in gui_deserializer.py could not be imported. You can install them with "
                   "'pip install --no-deps besser'")

# ─── Known parameter names for each style class ─────────────────────────────

_SIZE_PROPS = frozenset({
    'width', 'height', 'padding', 'margin', 'font_size', 'line_height', 'icon_size', 'unit_size',
    'font_weight', 'font_family', 'font_style', 'text_decoration', 'text_transform',
    'letter_spacing', 'word_spacing', 'white_space', 'word_break',
    'min_width', 'max_width', 'min_height', 'max_height',
    'padding_top', 'padding_right', 'padding_bottom', 'padding_left',
    'margin_top', 'margin_right', 'margin_bottom', 'margin_left',
})

_POSITION_PROPS = frozenset({
    'p_type', 'top', 'left', 'right', 'bottom', 'alignment', 'z_index', 'display',
    'overflow', 'overflow_x', 'overflow_y', 'visibility', 'cursor',
    'box_sizing', 'transform', 'transition', 'animation', 'filter',
})

_COLOR_PROPS = frozenset({
    'background_color', 'text_color', 'border_color', 'line_color', 'grid_color', 'axis_color',
    'bar_color', 'label_color', 'fill_color', 'opacity', 'color_palette', 'primary_color',
    'border_radius', 'border_width', 'border_style', 'border',
    'border_top', 'border_right', 'border_bottom', 'border_left',
    'box_shadow', 'text_shadow',
    'background_image', 'background_size', 'background_position', 'background_repeat',
})

_LAYOUT_PROPS = frozenset({
    'layout_type', 'orientation', 'padding', 'margin', 'gap', 'alignment', 'wrap',
    'flex_direction', 'justify_content', 'align_items', 'flex_wrap',
    'grid_template_columns', 'grid_template_rows', 'grid_gap', 'justify_items',
    'flex', 'flex_grow', 'flex_shrink', 'flex_basis', 'order', 'align_self',
})

_CATEGORY_KEYS = frozenset({'size', 'position', 'color', 'layout'})


def _normalize_styling_dict(d: dict) -> dict:
    """Normalize a styling dict from either nested or flat (LLM-generated) format.

    LLMs often produce flat styling like ``{"background_color": "#fff", "padding": "10px"}``
    instead of the expected nested format.  This function detects that pattern and
    groups properties into the correct ``size`` / ``color`` / ``position`` / ``layout``
    sub-objects so the rest of the deserializer can handle them uniformly.
    """
    if not d or any(k in d for k in _CATEGORY_KEYS):
        return d  # already nested (or empty)

    size_props, position_props, color_props, layout_props = {}, {}, {}, {}
    for k, v in d.items():
        if k in _SIZE_PROPS:
            size_props[k] = v
        elif k in _POSITION_PROPS:
            position_props[k] = v
        elif k in _COLOR_PROPS:
            color_props[k] = v
        elif k in _LAYOUT_PROPS:
            layout_props[k] = v

    result = {}
    if size_props:
        result['size'] = size_props
    if position_props:
        result['position'] = position_props
    if color_props:
        result['color'] = color_props
    if layout_props:
        result['layout'] = layout_props
    return result if result else d


def _deserialize_layout(d: dict) -> "Layout | None":
    if not d:
        return None
    return Layout(**{k: v for k, v in d.items() if k in _LAYOUT_PROPS})


def _deserialize_styling(d: dict) -> "Styling | None":
    if not d:
        return None
    d = _normalize_styling_dict(d)
    size = Size(**{k: v for k, v in d["size"].items() if k in _SIZE_PROPS}) if d.get("size") else None
    position = Position(**{k: v for k, v in d["position"].items() if k in _POSITION_PROPS}) if d.get("position") else None
    color = Color(**{k: v for k, v in d["color"].items() if k in _COLOR_PROPS}) if d.get("color") else None
    layout = _deserialize_layout(d.get("layout"))
    return Styling(size=size, position=position, color=color, layout=layout)


def _deserialize_series(d: dict) -> Series:
    return Series(
        name=d["name"],
        label=d.get("label"),
        data_binding=None,
        styling=_deserialize_styling(d.get("styling")),
    )


def _deserialize_column(d: dict) -> Column:
    t = d.get("type", "Column")
    label = d.get("label", "")
    if t == "FieldColumn":
        return FieldColumn(label=label, field=SimpleNamespace(name=d.get("field", "")))
    if t == "LookupColumn":
        return LookupColumn(
            label=label,
            path=SimpleNamespace(name=d.get("path", "")),
            field=SimpleNamespace(name=d.get("field", "")),
        )
    if t == "ExpressionColumn":
        return ExpressionColumn(label=label, expression=d.get("expression", ""))
    return Column(label=label)


def _deserialize_view_element(d: dict) -> ViewElement:
    t = d.get("type", "ViewComponent")
    base = {
        "name": d["name"],
        "description": d.get("description", ""),
        "styling": _deserialize_styling(d.get("styling")),
    }
    for opt in ("component_id", "tag_name", "css_classes", "custom_attributes"):
        if d.get(opt) is not None:
            base[opt] = d[opt]
    if d.get("display_order") is not None:
        base["display_order"] = d["display_order"]

    series_list = [_deserialize_series(s) for s in d.get("series", [])]

    if t == "AgentComponent":
        return AgentComponent(
            agent_name=d.get("agent_name"),
            agent_title=d.get("agent_title"),
            **base,
        )

    if t == "LineChart":
        el = LineChart(
            line_width=d.get("line_width", 2),
            show_grid=d.get("show_grid", True),
            show_legend=d.get("show_legend", True),
            show_tooltip=d.get("show_tooltip", True),
            curve_type=d.get("curve_type", "monotone"),
            animate=d.get("animate", True),
            legend_position=d.get("legend_position", "top"),
            grid_color=d.get("grid_color"),
            dot_size=d.get("dot_size", 4),
            title=d.get("title"),
            primary_color=d.get("primary_color"),
            **base,
        )
        el.series = series_list
        return el

    if t == "BarChart":
        el = BarChart(
            bar_width=d.get("bar_width", 20),
            orientation=d.get("orientation", "vertical"),
            show_grid=d.get("show_grid", True),
            show_legend=d.get("show_legend", True),
            show_tooltip=d.get("show_tooltip", True),
            stacked=d.get("stacked", False),
            animate=d.get("animate", True),
            legend_position=d.get("legend_position", "top"),
            grid_color=d.get("grid_color"),
            bar_gap=d.get("bar_gap", 4),
            title=d.get("title"),
            primary_color=d.get("primary_color"),
            **base,
        )
        el.series = series_list
        return el

    if t == "PieChart":
        el = PieChart(
            show_legend=d.get("show_legend", True),
            legend_position=d.get("legend_position", "top"),
            show_labels=d.get("show_labels", True),
            label_position=d.get("label_position", "outside"),
            padding_angle=d.get("padding_angle", 0),
            inner_radius=d.get("inner_radius", 0),
            outer_radius=d.get("outer_radius", 80),
            start_angle=d.get("start_angle", 0),
            end_angle=d.get("end_angle", 360),
            title=d.get("title"),
            primary_color=d.get("primary_color"),
            **base,
        )
        el.series = series_list
        return el

    if t == "RadarChart":
        el = RadarChart(
            show_grid=d.get("show_grid", True),
            show_tooltip=d.get("show_tooltip", True),
            show_radius_axis=d.get("show_radius_axis", True),
            show_legend=d.get("show_legend", True),
            legend_position=d.get("legend_position", "top"),
            dot_size=d.get("dot_size", 3),
            grid_type=d.get("grid_type", "polygon"),
            stroke_width=d.get("stroke_width", 2),
            title=d.get("title"),
            primary_color=d.get("primary_color"),
            **base,
        )
        el.series = series_list
        return el

    if t == "RadialBarChart":
        el = RadialBarChart(
            start_angle=d.get("start_angle", 0),
            end_angle=d.get("end_angle", 360),
            inner_radius=d.get("inner_radius", 30),
            outer_radius=d.get("outer_radius", 80),
            show_legend=d.get("show_legend", True),
            legend_position=d.get("legend_position", "top"),
            show_tooltip=d.get("show_tooltip", True),
            title=d.get("title"),
            primary_color=d.get("primary_color"),
            **base,
        )
        el.series = series_list
        return el

    if t == "Table":
        return Table(
            show_header=d.get("show_header", True),
            striped_rows=d.get("striped_rows", False),
            show_pagination=d.get("show_pagination", False),
            rows_per_page=d.get("rows_per_page", 5),
            title=d.get("title"),
            primary_color=d.get("primary_color"),
            columns=[_deserialize_column(c) for c in d.get("columns", [])],
            action_buttons=d.get("action_buttons", False),
            **base,
        )

    if t == "MetricCard":
        return MetricCard(
            metric_title=d.get("metric_title", "Metric Title"),
            format=d.get("format", "number"),
            value_color=d.get("value_color", "#2c3e50"),
            value_size=d.get("value_size", 32),
            show_trend=d.get("show_trend", True),
            positive_color=d.get("positive_color", "#27ae60"),
            negative_color=d.get("negative_color", "#e74c3c"),
            title=d.get("title"),
            primary_color=d.get("primary_color"),
            **base,
        )

    if t == "Button":
        return Button(
            label=d.get("label", ""),
            buttonType=d.get("buttonType", "Raised Button"),
            actionType=d.get("actionType", "navigate"),
            confirmation_required=d.get("confirmation_required", False),
            confirmation_message=d.get("confirmation_message"),
            **base,
        )

    if t == "Text":
        return Text(
            content=d.get("content", ""),
            **base,
        )

    if t == "Link":
        return Link(
            label=d.get("label", ""),
            url=d.get("url"),
            target=d.get("target"),
            rel=d.get("rel"),
            **base,
        )

    if t == "Image":
        return Image(
            source=d.get("source"),
            **base,
        )

    if t == "InputField":
        options_data = d.get("options") or []
        options = [SelectOption(label=o.get("label", ""), value=o.get("value", "")) for o in options_data]
        return InputField(
            field_type=d.get("field_type", "Text"),
            label=d.get("label", ""),
            placeholder=d.get("placeholder", ""),
            required=d.get("required", False),
            default_value=d.get("default_value"),
            options=options if options else None,
            min_value=d.get("min_value"),
            max_value=d.get("max_value"),
            step=d.get("step"),
            help_text=d.get("help_text"),
            disabled=d.get("disabled", False),
            readonly=d.get("readonly", False),
            multiple=d.get("multiple", False),
            validationRules=d.get("validationRules"),
            **base,
        )

    if t == "Form":
        return Form(
            inputFields=set(_deserialize_view_element(f) for f in d.get("inputFields", [])),
            title=d.get("title"),
            submit_label=d.get("submit_label", "Submit"),
            show_cancel=d.get("show_cancel", False),
            cancel_label=d.get("cancel_label", "Cancel"),
            columns=d.get("columns", 1),
            **base,
        )

    if t == "Menu":
        menu_items = set(
            MenuItem(
                label=mi.get("label", ""),
                url=mi.get("url"),
                target=mi.get("target"),
                rel=mi.get("rel"),
            )
            for mi in d.get("menuItems", [])
        )
        return Menu(menuItems=menu_items, **base)

    if t == "DataList":
        return DataList(list_sources=set(), **base)

    if t == "Alert":
        severity_str = d.get("severity", "info")
        _severity_map = {s.value: s for s in AlertSeverity}
        severity = _severity_map.get(severity_str, AlertSeverity.Info)
        return Alert(
            content=d.get("content", ""),
            severity=severity,
            title=d.get("title"),
            dismissible=d.get("dismissible", False),
            **base,
        )

    if t == "EmbeddedContent":
        return EmbeddedContent(
            source=d.get("source", ""),
            content_type=d.get("content_type", ""),
            extra_props=d.get("extra_props"),
            **base,
        )

    if t == "ViewContainer":
        return ViewContainer(
            view_elements=set(_deserialize_view_element(c) for c in d.get("view_elements", [])),
            layout=_deserialize_layout(d.get("layout")),
            **base,
        )

    # Fallback: generic ViewComponent
    return ViewComponent(**base)


def _deserialize_screen(d: dict) -> Screen:
    base = {
        "name": d["name"],
        "description": d.get("description", ""),
        "view_elements": set(_deserialize_view_element(el) for el in d.get("view_elements", [])),
        "x_dpi": d.get("x_dpi", ""),
        "y_dpi": d.get("y_dpi", ""),
        "screen_size": d.get("screen_size", "Medium"),
        "is_main_page": d.get("is_main_page", False),
        "layout": _deserialize_layout(d.get("layout")),
        "styling": _deserialize_styling(d.get("styling")),
        "route_path": d.get("route_path"),
    }
    for opt in ("component_id", "tag_name", "css_classes", "custom_attributes", "display_order"):
        if d.get(opt) is not None:
            base[opt] = d[opt]
    return Screen(**base)


def json_to_gui(json_str: str) -> GUIModel:
    """Deserialize a JSON string produced by :func:`gui_to_json` back into a :class:`GUIModel`.

    Args:
        json_str: JSON string representing the GUI model.

    Returns:
        A reconstructed :class:`GUIModel` instance.
    """
    data = json.loads(json_str)
    modules = set()
    for m in data.get("modules", []):
        screens = set(_deserialize_screen(s) for s in m.get("screens", []))
        modules.add(Module(name=m["name"], screens=screens))
    gui_kwargs = dict(
        name=data["name"],
        package=data.get("package", ""),
        versionCode=data.get("versionCode", 1),
        versionName=data.get("versionName", "1.0"),
        modules=modules,
        description=data.get("description", ""),
    )
    style_entries = data.get("style_entries")
    if style_entries is not None:
        try:
            return GUIModel(**gui_kwargs, style_entries=style_entries)
        except TypeError:
            pass
    return GUIModel(**gui_kwargs)
