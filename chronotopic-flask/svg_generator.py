import svgwrite
from lxml import etree
from shapely.geometry import LineString, Point
import math
from geomdl import BSpline
from geomdl import utilities
import numpy as np
import io
import os
import base64

# Color and print styles
from styles import colour_style, print_style

def calculate_edge_offset(line_start, line_end, node_size):
    """Calculate where to start an edge, factoring in the size of the node"""
    node_size = int(node_size)
    p = Point(line_end)
    c = p.buffer(node_size + 8).boundary
    l = LineString([(line_start), (line_end)])
    i = c.intersection(l)
    
    try:
        return i.coords[0]
    except:
        return p.coords[0]

def calculate_control_points(start, end, curve_strength=0.6):
    """Calculate control points for curved edges"""
    length = math.sqrt((start[0] - end[0])**2 + (start[1] - end[1])**2)
    p1 = Point(start[0], start[1])
    p2 = Point(end[0], end[1])
    
    multiplier = curve_strength
    
    c1 = p1.buffer(length * multiplier).boundary
    c2 = p2.buffer(length * multiplier).boundary
    i = c1.intersection(c2)
    
    if hasattr(i, 'geoms') and len(i.geoms) > 0:
        return (i.geoms[0].coords[0], i.geoms[1].coords[0])
    else:
        # Fallback for single geometry
        try:
            coords = list(i.coords)
            if len(coords) >= 2:
                return (coords[0], coords[1])
        except:
            pass
        return (start, end)

def draw_curved_path(dwg, start, end, edge_style, edge_width_multiplier=1.0, edge_opacity=1.0, curve_strength=0.6):
    """Draw a curved path between two points"""
    start_str = f"{start[0]},{start[1]}"
    end_str = f"{end[0]},{end[1]}"
    
    # Draw stroke case if needed
    case = None
    if edge_style['stroke-case'] > 0:
        case_attrs = {
            'd': f'M{start_str}',
            'stroke': edge_style['stroke-case-color'],
            'fill': 'none',
            'stroke_width': edge_style['stroke-case'] * edge_width_multiplier,
            'opacity': edge_opacity
        }
        if edge_style['stroke-dasharray'] is not None:
            case_attrs['stroke_dasharray'] = edge_style['stroke-dasharray']
        case = dwg.path(**case_attrs)
    
    # Draw main path
    path_attrs = {
        'd': f'M{start_str}',
        'stroke': edge_style['stroke'],
        'fill': 'none',
        'stroke_width': edge_style['stroke-width'] * edge_width_multiplier,
        'opacity': edge_opacity
    }
    if edge_style['stroke-dasharray'] is not None:
        path_attrs['stroke_dasharray'] = edge_style['stroke-dasharray']
    path = dwg.path(**path_attrs)
    
    # Calculate control points for curve
    control_points = calculate_control_points(start, end, curve_strength)
    
    # Create B-spline curve
    curve = BSpline.Curve()
    curve.degree = 3
    curve.ctrlpts = [start, control_points[0], control_points[1], end]
    curve.knotvector = utilities.generate_knot_vector(curve.degree, len(curve.ctrlpts))
    curve.sample_size = 100
    curve.evaluate()
    
    # Build path data
    for i, pt in enumerate(curve.evalpts):
        if i == 0:
            continue
        path.push(f'L {pt[0]},{pt[1]}')
        if case:
            case.push(f'L {pt[0]},{pt[1]}')
    
    return case, path

def draw_node_shape(dwg, x, y, size, shape='circle', fill='white', stroke='black', stroke_width=2, opacity=1.0):
    """Draw different node shapes"""
    if shape == 'circle':
        return dwg.circle(center=(x, y), r=size, fill=fill, stroke=stroke, stroke_width=stroke_width, opacity=opacity)
    elif shape == 'square':
        return dwg.rect(insert=(x - size, y - size), size=(size * 2, size * 2), fill=fill, stroke=stroke, stroke_width=stroke_width, opacity=opacity)
    elif shape == 'diamond':
        points = [(x, y - size), (x + size, y), (x, y + size), (x - size, y)]
        return dwg.polygon(points=points, fill=fill, stroke=stroke, stroke_width=stroke_width, opacity=opacity)
    elif shape == 'hexagon':
        angle = math.pi / 3
        points = []
        for i in range(6):
            px = x + size * math.cos(i * angle - math.pi / 6)
            py = y + size * math.sin(i * angle - math.pi / 6)
            points.append((px, py))
        return dwg.polygon(points=points, fill=fill, stroke=stroke, stroke_width=stroke_width, opacity=opacity)
    else:
        return dwg.circle(center=(x, y), r=size, fill=fill, stroke=stroke, stroke_width=stroke_width, opacity=opacity)

def colorize_svg(svg_content, new_color):
    """Colorize an SVG by replacing fill colors with a new color"""
    from lxml import etree as svg_etree
    try:
        # Parse the SVG
        parser = svg_etree.XMLParser(remove_blank_text=True)
        root = svg_etree.fromstring(svg_content.encode(), parser)
        
        # Find all elements with fill attribute
        for elem in root.iter():
            # Skip if element has no attributes
            if elem.attrib is None:
                continue
                
            # Update fill color if it's not 'none' or transparent
            if 'fill' in elem.attrib:
                current_fill = elem.attrib['fill'].lower()
                if current_fill not in ['none', 'transparent', 'rgba(0,0,0,0)']:
                    elem.attrib['fill'] = new_color
                    
            # Update stroke color for certain elements
            if 'stroke' in elem.attrib:
                current_stroke = elem.attrib['stroke'].lower()
                if current_stroke not in ['none', 'transparent', 'rgba(0,0,0,0)']:
                    elem.attrib['stroke'] = new_color
                    
            # Handle style attribute
            if 'style' in elem.attrib:
                style = elem.attrib['style']
                # Replace fill colors in style
                import re
                style = re.sub(r'fill:\s*#[0-9a-fA-F]{6}', f'fill:{new_color}', style)
                style = re.sub(r'fill:\s*#[0-9a-fA-F]{3}', f'fill:{new_color}', style)
                style = re.sub(r'stroke:\s*#[0-9a-fA-F]{6}', f'stroke:{new_color}', style)
                style = re.sub(r'stroke:\s*#[0-9a-fA-F]{3}', f'stroke:{new_color}', style)
                elem.attrib['style'] = style
        
        # Return the modified SVG as string
        return svg_etree.tostring(root, encoding='unicode')
    except:
        # If colorization fails, return original
        return svg_content

class GraphMLToSVG:
    """Convert GraphML files to SVG visualizations"""
    
    def __init__(self, graphml_file):
        self.tree = etree.parse(graphml_file)
        self.root = self.tree.getroot()
        self.nodes = {}
        self.edges = {}
        self.key = {}
        self._parse_graphml()
    
    def _parse_graphml(self):
        """Parse GraphML file structure"""
        # Parse keys
        for key_item in self.root.iter('{http://graphml.graphdrawing.org/xmlns}key'):
            values = key_item.values()
            self.key[values[3] if len(values) > 3 else values[0]] = {
                'name': values[0],
                'type': values[1] if len(values) > 1 else 'string',
                'for': values[2] if len(values) > 2 else 'node'
            }
        
        # Parse nodes
        for node in self.root.iter('{http://graphml.graphdrawing.org/xmlns}node'):
            node_data = {'id': node.attrib['id']}
            for data in node:
                if 'key' in data.attrib:
                    node_data[data.attrib['key']] = data.text
            self.nodes[node.attrib['id']] = node_data
        
        # Parse edges
        edge_count = 0
        for edge in self.root.iter('{http://graphml.graphdrawing.org/xmlns}edge'):
            edge_id = edge.attrib.get('id', f'e{edge_count}')
            edge_data = {
                'source': edge.attrib['source'],
                'target': edge.attrib['target']
            }
            for data in edge:
                if 'key' in data.attrib:
                    edge_data[data.attrib['key']] = data.text
            
            # Add coordinates
            source = edge_data['source']
            target = edge_data['target']
            if source in self.nodes and target in self.nodes:
                edge_data['start'] = (
                    float(self.nodes[source].get('x', 0)),
                    float(self.nodes[source].get('y', 0))
                )
                edge_data['end'] = (
                    float(self.nodes[target].get('x', 0)),
                    float(self.nodes[target].get('y', 0))
                )
            
            self.edges[edge_id] = edge_data
            edge_count += 1
    
    def generate_svg(self, settings):
        """Generate SVG with given settings"""
        # Extract settings
        size = settings.get('size', 1000)
        scale = settings.get('scale', 1.0)
        curved = settings.get('curved', True)
        label_position = settings.get('label_position', 'below')
        node_scale = settings.get('node_scale', 1.0)
        color_scheme = settings.get('color_scheme', 'color')
        edge_width_multiplier = settings.get('edge_width', 1.0)
        show_arrows = settings.get('show_arrows', False)
        node_opacity = settings.get('node_opacity', 1.0)
        edge_opacity = settings.get('edge_opacity', 1.0)
        label_size = settings.get('label_size', 0.6)
        background_color = settings.get('background_color', '#525252')
        node_stroke_width = settings.get('node_stroke_width', 2)
        node_stroke_color = settings.get('node_stroke_color', '#ffffff')
        label_color = settings.get('label_color', '#dbdbdb')
        show_shadows = settings.get('show_shadows', False)
        show_grid = settings.get('show_grid', False)
        grid_size = settings.get('grid_size', 50)
        export_scale = settings.get('export_scale', 1.0)
        curve_strength = settings.get('curve_strength', 0.6)
        node_shape = settings.get('node_shape', 'circle')
        symbol_color = settings.get('symbol_color', '#000000')
        
        # Use appropriate style
        style = colour_style if color_scheme == 'color' else print_style
        
        # Create SVG
        dwg_size = int(size * export_scale)
        dwg = svgwrite.Drawing(size=(dwg_size, dwg_size))
        
        # Background
        dwg.add(dwg.rect(insert=(0, 0), size=(dwg_size, dwg_size), fill=background_color))
        
        # Add grid if enabled
        if show_grid:
            grid_group = dwg.add(dwg.g(opacity=0.2))
            grid_step = grid_size * export_scale
            for i in range(0, dwg_size + int(grid_step), int(grid_step)):
                grid_group.add(dwg.line(start=(i, 0), end=(i, dwg_size), stroke='white', stroke_width=1))
                grid_group.add(dwg.line(start=(0, i), end=(dwg_size, i), stroke='white', stroke_width=1))
        
        # Add shadow filter if enabled
        if show_shadows:
            defs = dwg.add(dwg.defs())
            shadow_filter = defs.add(dwg.filter(id='shadow'))
            shadow_filter.add(dwg.feGaussianBlur(in_='SourceAlpha', stdDeviation=3))
            shadow_filter.add(dwg.feOffset(dx=2, dy=2, result='offsetblur'))
            shadow_filter.add(dwg.feFlood(flood_color='#000000', flood_opacity=0.3))
            shadow_filter.add(dwg.feComposite(in2='offsetblur', operator='in'))
            feMerge = shadow_filter.add(dwg.feMerge())
            feMerge.add(dwg.feMergeNode())
            feMerge.add(dwg.feMergeNode(in_='SourceGraphic'))
        
        # Calculate bounds and scale
        if self.nodes:
            x_vals = [float(n.get('x', 0)) for n in self.nodes.values()]
            y_vals = [float(n.get('y', 0)) for n in self.nodes.values()]
            
            if x_vals and y_vals:
                min_x, max_x = min(x_vals), max(x_vals)
                min_y, max_y = min(y_vals), max(y_vals)
                
                # Calculate scale to fit
                graph_width = max_x - min_x
                graph_height = max_y - min_y
                
                if graph_width > 0 and graph_height > 0:
                    scale_factor = min(dwg_size * 0.8 / graph_width, dwg_size * 0.8 / graph_height) * scale
                    
                    # Transform nodes
                    for node_data in self.nodes.values():
                        x = float(node_data.get('x', 0))
                        y = float(node_data.get('y', 0))
                        
                        # Center and scale
                        x = (x - (max_x + min_x) / 2) * scale_factor + dwg_size / 2
                        y = (y - (max_y + min_y) / 2) * scale_factor + dwg_size / 2
                        
                        node_data['x'] = x
                        node_data['y'] = y
        
        # Draw edges
        edges_group = dwg.add(dwg.g())
        for edge_data in self.edges.values():
            if 'start' in edge_data and 'end' in edge_data:
                source_id = edge_data['source']
                target_id = edge_data['target']
                
                if source_id in self.nodes and target_id in self.nodes:
                    start = (self.nodes[source_id]['x'], self.nodes[source_id]['y'])
                    end = (self.nodes[target_id]['x'], self.nodes[target_id]['y'])
                    
                    # Find edge style
                    edge_style = None
                    relation = edge_data.get('relation', edge_data.get('d2', 'none'))
                    
                    for es in style['edges']:
                        if es['label'] == relation:
                            edge_style = es
                            break
                    
                    if not edge_style:
                        for es in style['edges']:
                            if es['label'] is None or es['label'] == 'none':
                                edge_style = es
                                break
                    
                    if edge_style:
                        if curved:
                            case, path = draw_curved_path(dwg, start, end, edge_style, edge_width_multiplier, edge_opacity, curve_strength)
                            if case:
                                edges_group.add(case)
                            edges_group.add(path)
                        else:
                            # Straight line
                            line_attrs = {
                                'start': start,
                                'end': end,
                                'stroke': edge_style['stroke'],
                                'stroke_width': edge_style['stroke-width'] * edge_width_multiplier,
                                'opacity': edge_opacity
                            }
                            if edge_style['stroke-dasharray']:
                                line_attrs['stroke_dasharray'] = edge_style['stroke-dasharray']
                            edges_group.add(dwg.line(**line_attrs))
        
        # Draw nodes
        nodes_group = dwg.add(dwg.g())
        if show_shadows:
            nodes_group['filter'] = 'url(#shadow)'
        for node_id, node_data in self.nodes.items():
            x = node_data.get('x', 0)
            y = node_data.get('y', 0)
            
            # Get node properties
            size_val = float(node_data.get('size', node_data.get('d3', 10))) * node_scale * export_scale
            
            # Find node style by searching through all node data values
            node_style = None
            for ns in style['nodes']:
                for value in node_data.values():
                    if ns['label'] == value:
                        node_style = ns
                        break
                if node_style:
                    break
            
            if not node_style:
                # Default style
                node_style = {'color': '#cccccc', 'symbol': None}
            
            # Draw node background shape
            nodes_group.add(draw_node_shape(
                dwg, x, y, size_val, 
                shape=node_shape,
                fill=style['background']['color'],
                stroke='none',
                opacity=1.0
            ))
            
            # Draw symbol if available, otherwise draw colored circle
            if node_style.get('symbol'):
                try:
                    symbol_path = os.path.join(os.path.dirname(__file__), node_style['symbol'])
                    with open(symbol_path, 'r') as file:
                        svg_content = file.read()
                    
                    # Colorize the SVG if a custom color is specified
                    if symbol_color != '#000000':
                        svg_content = colorize_svg(svg_content, symbol_color)
                    
                    # Encode as base64
                    encoded = base64.b64encode(svg_content.encode()).decode()
                    svgdata = f'data:image/svg+xml;base64,{encoded}'
                    nodes_group.add(dwg.image(
                        href=svgdata,
                        insert=(x - size_val, y - size_val),
                        size=(size_val * 2, size_val * 2),
                        opacity=node_opacity
                    ))
                except:
                    # Fallback to colored shape if symbol not found
                    nodes_group.add(draw_node_shape(
                        dwg, x, y, size_val,
                        shape=node_shape,
                        fill=node_style['color'],
                        stroke=node_stroke_color,
                        stroke_width=node_stroke_width,
                        opacity=node_opacity
                    ))
            else:
                # Draw colored shape
                nodes_group.add(draw_node_shape(
                    dwg, x, y, size_val,
                    shape=node_shape,
                    fill=node_style['color'],
                    stroke=node_stroke_color,
                    stroke_width=node_stroke_width,
                    opacity=node_opacity
                ))
            
            # Add label
            label = node_id
            if label_position == 'below':
                label_y = y + size_val + 15
            else:
                label_y = y + 5
            
            nodes_group.add(dwg.text(
                label,
                insert=(x, label_y),
                text_anchor='middle',
                font_family=style['label']['font-family'],
                font_size=f"{label_size}em",
                fill=label_color
            ))
        
        # Return SVG as string
        return dwg.tostring()

def graphml_to_svg(graphml_path, settings):
    """Main function to convert GraphML to SVG"""
    converter = GraphMLToSVG(graphml_path)
    return converter.generate_svg(settings)