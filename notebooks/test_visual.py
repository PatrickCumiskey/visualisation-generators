# Import the necessary components
from styles import colour_style
from visualisation_generators import SvgGrapher
from IPython.display import display_svg, SVG

# The path to the graphml file

name = "NAME"
graphml_file = 'file/location' + name +'.graphml'


# The name of the finished visualisation. By default, this just changes the name from *.graphml to *.svg.
svg_file = graphml_file.replace('graphml', 'svg')

# Instantiate the SvgGrapher class with the graphml file
visualisation = SvgGrapher(graphml_file)

# Save the visualisation
# option 2
# visualisation.draw_graph(svg_file, style=colour_style, size=.6, scale_correction=600, curved=False, label_correction=0.55, node_scale=6, offset=(-15,0))
visualisation.draw_graph(svg_file, style=colour_style, size=.6, scale_correction=880, curved=False, label_correction=0.4, node_scale=4, offset=(-25,0))

# Display the visualisation
display_svg(SVG('files/svg/' + svg_file))

