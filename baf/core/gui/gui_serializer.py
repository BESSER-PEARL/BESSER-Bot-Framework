"""Serialization helpers: GUIModel → JSON string."""
import json
from enum import Enum

from besser.BUML.metamodel.gui.graphical_ui import (
    GUIModel, Screen, ViewElement, ViewContainer, ViewComponent,
    Button, Text, Image, InputField, Form, Menu,
    DataList, DataSource, DataSourceElement, File, Collection,
    EmbeddedContent, Link,
)
from besser.BUML.metamodel.gui.style import Styling, Size, Position, Color, Layout
from besser.BUML.metamodel.gui.binding import DataBinding
from besser.BUML.metamodel.gui.dashboard import (
    LineChart, BarChart, PieChart, RadarChart, RadialBarChart,
    Table, MetricCard, AgentComponent, Series,
    Column, FieldColumn, LookupColumn, ExpressionColumn,
)


def _enum_val(v):
    return v.value if isinstance(v, Enum) else v


def _serialize_size(size: Size) -> dict:
    if size is None:
        return None
    return {k: _enum_val(v) for k, v in vars(size).items()
            if not k.startswith('_') and v is not None} or {
        k: _enum_val(v) for k, v in {
            "width": size.width, "height": size.height, "padding": size.padding,
            "margin": size.margin, "font_size": size.font_size, "line_height": size.line_height,
            "icon_size": size.icon_size, "unit_size": _enum_val(size.unit_size),
            "font_weight": size.font_weight, "font_family": size.font_family,
            "font_style": size.font_style, "text_decoration": size.text_decoration,
            "text_transform": size.text_transform, "letter_spacing": size.letter_spacing,
            "word_spacing": size.word_spacing, "white_space": size.white_space,
            "word_break": size.word_break, "min_width": size.min_width,
            "max_width": size.max_width, "min_height": size.min_height,
            "max_height": size.max_height, "padding_top": size.padding_top,
            "padding_right": size.padding_right, "padding_bottom": size.padding_bottom,
            "padding_left": size.padding_left, "margin_top": size.margin_top,
            "margin_right": size.margin_right, "margin_bottom": size.margin_bottom,
            "margin_left": size.margin_left,
        }.items() if v is not None
    }


def _serialize_position(pos: Position) -> dict:
    if pos is None:
        return None
    return {k: _enum_val(v) for k, v in {
        "p_type": pos.p_type, "top": pos.top, "left": pos.left, "right": pos.right,
        "bottom": pos.bottom, "alignment": pos.alignment, "z_index": pos.z_index,
        "display": pos.display, "overflow": pos.overflow, "overflow_x": pos.overflow_x,
        "overflow_y": pos.overflow_y, "visibility": pos.visibility, "cursor": pos.cursor,
        "box_sizing": pos.box_sizing, "transform": pos.transform, "transition": pos.transition,
        "animation": pos.animation, "filter": pos.filter,
    }.items() if v is not None}


def _serialize_color(color: Color) -> dict:
    if color is None:
        return None
    return {k: v for k, v in {
        "background_color": color.background_color, "text_color": color.text_color,
        "border_color": color.border_color, "line_color": color.line_color,
        "grid_color": color.grid_color, "axis_color": color.axis_color,
        "bar_color": color.bar_color, "label_color": color.label_color,
        "fill_color": color.fill_color, "opacity": color.opacity,
        "color_palette": color.color_palette, "primary_color": color.primary_color,
        "border_radius": color.border_radius, "border_width": color.border_width,
        "border_style": color.border_style, "border": color.border,
        "border_top": color.border_top, "border_right": color.border_right,
        "border_bottom": color.border_bottom, "border_left": color.border_left,
        "box_shadow": color.box_shadow, "text_shadow": color.text_shadow,
        "background_image": color.background_image, "background_size": color.background_size,
        "background_position": color.background_position, "background_repeat": color.background_repeat,
    }.items() if v is not None}


def _serialize_layout(layout: Layout) -> dict:
    if layout is None:
        return None
    return {k: _enum_val(v) for k, v in {
        "layout_type": layout.layout_type, "orientation": layout.orientation,
        "padding": layout.padding, "margin": layout.margin, "gap": layout.gap,
        "alignment": layout.alignment, "wrap": layout.wrap,
        "flex_direction": layout.flex_direction, "justify_content": layout.justify_content,
        "align_items": layout.align_items, "flex_wrap": layout.flex_wrap,
        "grid_template_columns": layout.grid_template_columns,
        "grid_template_rows": layout.grid_template_rows, "grid_gap": layout.grid_gap,
        "justify_items": layout.justify_items, "flex": layout.flex,
        "flex_grow": layout.flex_grow, "flex_shrink": layout.flex_shrink,
        "flex_basis": layout.flex_basis, "order": layout.order, "align_self": layout.align_self,
    }.items() if v is not None}


def _serialize_styling(styling: Styling) -> dict:
    if styling is None:
        return None
    result = {}
    if styling.size is not None:
        result["size"] = _serialize_size(styling.size)
    if styling.position is not None:
        result["position"] = _serialize_position(styling.position)
    if styling.color is not None:
        result["color"] = _serialize_color(styling.color)
    if styling.layout is not None:
        result["layout"] = _serialize_layout(styling.layout)
    return result or None


def _serialize_data_binding(db: DataBinding) -> dict:
    if db is None:
        return None
    return {k: v for k, v in {
        "name": db.name,
        "domain_concept": db.domain_concept.name if db.domain_concept else None,
        "visualization_attrs": [p.name for p in db.visualization_attrs] if db.visualization_attrs else [],
        "label_field": db.label_field.name if db.label_field else None,
        "data_field": db.data_field.name if db.data_field else None,
        "label_field_path": db.label_field_path,
        "data_field_path": db.data_field_path,
        "filter_expression": db.filter_expression,
    }.items() if v is not None}


def _serialize_data_source(ds: DataSource) -> dict:
    if ds is None:
        return None
    if isinstance(ds, DataSourceElement):
        return {k: v for k, v in {
            "type": "DataSourceElement", "name": ds.name,
            "dataSourceClass": ds.dataSourceClass.name if ds.dataSourceClass else None,
            "field_names": ds.field_names or [],
            "label_field_name": ds.label_field_name,
            "value_field_name": ds.value_field_name,
        }.items() if v is not None}
    if isinstance(ds, File):
        return {"type": "File", "name": ds.name, "file_type": _enum_val(ds.file_type)}
    if isinstance(ds, Collection):
        return {"type": "Collection", "name": ds.name, "col_type": _enum_val(ds.col_type)}
    return {"type": "DataSource", "name": ds.name}


def _serialize_series(s: Series) -> dict:
    if s is None:
        return None
    return {k: v for k, v in {
        "name": s.name, "label": s.label,
        "data_binding": _serialize_data_binding(s.data_binding),
        "styling": _serialize_styling(s.styling),
    }.items() if v is not None}


def _serialize_column(col: Column) -> dict:
    if isinstance(col, FieldColumn):
        return {"type": "FieldColumn", "label": col.label, "field": col.field.name}
    if isinstance(col, LookupColumn):
        return {"type": "LookupColumn", "label": col.label,
                "path": col.path.name, "field": col.field.name}
    if isinstance(col, ExpressionColumn):
        return {"type": "ExpressionColumn", "label": col.label, "expression": col.expression}
    return {"type": "Column", "label": col.label}


def _base_fields(el: ViewElement) -> dict:
    d = {"name": el.name}
    if getattr(el, "description", None):
        d["description"] = el.description
    if el.component_id:
        d["component_id"] = el.component_id
    if el.tag_name:
        d["tag_name"] = el.tag_name
    if el.css_classes:
        d["css_classes"] = el.css_classes
    if el.custom_attributes:
        d["custom_attributes"] = el.custom_attributes
    if el.display_order is not None:
        d["display_order"] = el.display_order
    styling = _serialize_styling(el.styling)
    if styling:
        d["styling"] = styling
    return d


def _sorted_elements(elements):
    return sorted(elements, key=lambda x: (x.display_order if x.display_order is not None else float('inf'), x.name))


def _serialize_view_element(el: ViewElement) -> dict:
    # Dashboard: AgentComponent
    if isinstance(el, AgentComponent):
        d = _base_fields(el)
        d["type"] = "AgentComponent"
        if el.agent_name:
            d["agent_name"] = el.agent_name
        if el.agent_title:
            d["agent_title"] = el.agent_title
        return d

    # Dashboard: Charts
    if isinstance(el, LineChart):
        d = _base_fields(el)
        d.update({k: v for k, v in {
            "type": "LineChart", "title": el.title,
            "series": [_serialize_series(s) for s in el.series],
            "line_width": el.line_width, "show_grid": el.show_grid,
            "show_legend": el.show_legend, "show_tooltip": el.show_tooltip,
            "curve_type": el.curve_type, "animate": el.animate,
            "legend_position": el.legend_position, "grid_color": el.grid_color,
            "dot_size": el.dot_size,
        }.items() if v is not None})
        return d

    if isinstance(el, BarChart):
        d = _base_fields(el)
        d.update({k: v for k, v in {
            "type": "BarChart", "title": el.title,
            "series": [_serialize_series(s) for s in el.series],
            "bar_width": el.bar_width, "orientation": el.orientation,
            "show_grid": el.show_grid, "show_legend": el.show_legend,
            "show_tooltip": el.show_tooltip, "stacked": el.stacked,
            "animate": el.animate, "legend_position": el.legend_position,
            "grid_color": el.grid_color, "bar_gap": el.bar_gap,
        }.items() if v is not None})
        return d

    if isinstance(el, PieChart):
        d = _base_fields(el)
        d.update({k: v for k, v in {
            "type": "PieChart", "title": el.title,
            "series": [_serialize_series(s) for s in el.series],
            "show_legend": el.show_legend,
            "legend_position": _enum_val(el.legend_position),
            "show_labels": el.show_labels,
            "label_position": _enum_val(el.label_position),
            "padding_angle": el.padding_angle, "inner_radius": el.inner_radius,
            "outer_radius": el.outer_radius, "start_angle": el.start_angle,
            "end_angle": el.end_angle,
        }.items() if v is not None})
        return d

    if isinstance(el, RadarChart):
        d = _base_fields(el)
        d.update({k: v for k, v in {
            "type": "RadarChart", "title": el.title,
            "series": [_serialize_series(s) for s in el.series],
            "show_grid": el.show_grid, "show_tooltip": el.show_tooltip,
            "show_radius_axis": el.show_radius_axis, "show_legend": el.show_legend,
            "legend_position": el.legend_position, "dot_size": el.dot_size,
            "grid_type": el.grid_type, "stroke_width": el.stroke_width,
        }.items() if v is not None})
        return d

    if isinstance(el, RadialBarChart):
        d = _base_fields(el)
        d.update({k: v for k, v in {
            "type": "RadialBarChart", "title": el.title,
            "series": [_serialize_series(s) for s in el.series],
            "start_angle": el.start_angle, "end_angle": el.end_angle,
            "inner_radius": el.inner_radius, "outer_radius": el.outer_radius,
            "show_legend": el.show_legend, "legend_position": el.legend_position,
            "show_tooltip": el.show_tooltip,
        }.items() if v is not None})
        return d

    # Dashboard: Table
    if isinstance(el, Table):
        d = _base_fields(el)
        d.update({k: v for k, v in {
            "type": "Table", "title": el.title, "primary_color": el.primary_color,
            "show_header": el.show_header, "striped_rows": el.striped_rows,
            "show_pagination": el.show_pagination, "rows_per_page": el.rows_per_page,
            "columns": [_serialize_column(c) for c in el.columns],
            "action_buttons": el.action_buttons,
            "data_binding": _serialize_data_binding(el.data_binding),
        }.items() if v is not None})
        return d

    # Dashboard: MetricCard
    if isinstance(el, MetricCard):
        d = _base_fields(el)
        d.update({k: v for k, v in {
            "type": "MetricCard", "metric_title": el.metric_title,
            "format": el.format, "value_color": el.value_color,
            "value_size": el.value_size, "show_trend": el.show_trend,
            "positive_color": el.positive_color, "negative_color": el.negative_color,
            "title": el.title, "primary_color": el.primary_color,
            "data_binding": _serialize_data_binding(el.data_binding),
        }.items() if v is not None})
        return d

    # Standard: Button
    if isinstance(el, Button):
        d = _base_fields(el)
        d["type"] = "Button"
        d["label"] = el.label
        d["buttonType"] = _enum_val(el.buttonType)
        d["actionType"] = _enum_val(el.actionType)
        if el.targetScreen:
            d["targetScreen"] = el.targetScreen.name
        if el.entity_class:
            d["entity_class"] = el.entity_class.name
        if el.instance_source is not None:
            src = el.instance_source
            d["instance_source"] = src.name if hasattr(src, "name") else str(src)
        d["is_instance_method"] = el.is_instance_method
        d["confirmation_required"] = el.confirmation_required
        if el.confirmation_message:
            d["confirmation_message"] = el.confirmation_message
        return d

    # Standard: Text
    if isinstance(el, Text):
        d = _base_fields(el)
        d["type"] = "Text"
        d["content"] = el.content
        db = _serialize_data_binding(el.data_binding)
        if db:
            d["data_binding"] = db
        return d

    # Standard: Link
    if isinstance(el, Link):
        d = _base_fields(el)
        d.update({k: v for k, v in {
            "type": "Link", "label": el.label, "url": el.url,
            "target": el.target, "rel": el.rel,
        }.items() if v is not None})
        return d

    # Standard: Image
    if isinstance(el, Image):
        d = _base_fields(el)
        d["type"] = "Image"
        if el.source:
            d["source"] = el.source
        return d

    # Standard: InputField
    if isinstance(el, InputField):
        d = _base_fields(el)
        d.update({k: v for k, v in {
            "type": "InputField",
            "field_type": _enum_val(el.field_type),
            "validationRules": el.validationRules,
            "data_binding": _serialize_data_binding(el.data_binding),
        }.items() if v is not None})
        return d

    # Standard: Form
    if isinstance(el, Form):
        d = _base_fields(el)
        d["type"] = "Form"
        d["inputFields"] = [_serialize_view_element(f) for f in _sorted_elements(el.inputFields)]
        db = _serialize_data_binding(el.data_binding)
        if db:
            d["data_binding"] = db
        return d

    # Standard: Menu
    if isinstance(el, Menu):
        d = _base_fields(el)
        d["type"] = "Menu"
        d["menuItems"] = [
            {k: v for k, v in {"label": mi.label, "url": mi.url,
                                "target": mi.target, "rel": mi.rel}.items() if v is not None}
            for mi in el.menuItems
        ]
        return d

    # Standard: DataList
    if isinstance(el, DataList):
        d = _base_fields(el)
        d["type"] = "DataList"
        d["list_sources"] = [_serialize_data_source(ds) for ds in el.list_sources]
        db = _serialize_data_binding(el.data_binding)
        if db:
            d["data_binding"] = db
        return d

    # Standard: EmbeddedContent
    if isinstance(el, EmbeddedContent):
        d = _base_fields(el)
        d.update({k: v for k, v in {
            "type": "EmbeddedContent", "source": el.source,
            "content_type": el.content_type, "extra_props": el.extra_props or None,
        }.items() if v is not None})
        return d

    # ViewContainer (generic containers)
    if isinstance(el, ViewContainer):
        d = _base_fields(el)
        d["type"] = "ViewContainer"
        layout = _serialize_layout(el.layout)
        if layout:
            d["layout"] = layout
        d["view_elements"] = [_serialize_view_element(c) for c in _sorted_elements(el.view_elements)]
        return d

    # Fallback: generic ViewComponent
    d = _base_fields(el)
    d["type"] = "ViewComponent"
    if isinstance(el, ViewComponent):
        db = _serialize_data_binding(el.data_binding)
        if db:
            d["data_binding"] = db
    return d


def _serialize_screen(screen: Screen) -> dict:
    d = {"type": "Screen", "name": screen.name}
    if screen.description:
        d["description"] = screen.description
    if screen.x_dpi:
        d["x_dpi"] = screen.x_dpi
    if screen.y_dpi:
        d["y_dpi"] = screen.y_dpi
    d["screen_size"] = screen.screen_size
    d["is_main_page"] = screen.is_main_page
    d["route_path"] = screen.route_path
    if screen.component_id:
        d["component_id"] = screen.component_id
    if screen.tag_name:
        d["tag_name"] = screen.tag_name
    if screen.css_classes:
        d["css_classes"] = screen.css_classes
    if screen.custom_attributes:
        d["custom_attributes"] = screen.custom_attributes
    styling = _serialize_styling(screen.styling)
    if styling:
        d["styling"] = styling
    layout = _serialize_layout(screen.layout)
    if layout:
        d["layout"] = layout
    d["view_elements"] = [_serialize_view_element(el) for el in _sorted_elements(screen.view_elements)]
    return d


def gui_to_json(gui_model: GUIModel) -> str:
    """Serialize a :class:`GUIModel` instance to a JSON string.

    Args:
        gui_model: The GUI model to serialize.

    Returns:
        A JSON string representation of the model.
    """
    result = {
        "name": gui_model.name,
        "package": gui_model.package,
        "versionCode": gui_model.versionCode,
        "versionName": gui_model.versionName,
        "description": gui_model.description,
        "style_entries": getattr(gui_model, 'style_entries', None),
        "modules": [
            {
                "name": module.name,
                "screens": [_serialize_screen(s) for s in sorted(module.screens, key=lambda s: s.name)],
            }
            for module in sorted(gui_model.modules, key=lambda m: m.name)
        ],
    }
    return json.dumps(result, indent=2)
