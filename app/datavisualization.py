from bokeh.models import (HoverTool,FactorRange, Plot, LinearAxis, Grid,  Range1d)
from bokeh.models.glyphs import VBar
from bokeh.plotting import figure
from bokeh.models.sources import ColumnDataSource

def create_hover_tool():
    hover_html = """
      <div>
        <span class="hover-tooltip">$x</span>
      </div>
      <div>
        <span class="hover-tooltip">@bugs bugs</span>
      </div>
      <div>
        <span class="hover-tooltip">$@costs{0.00}</span>
      </div>
    """
    return HoverTool(tooltips=hover_html)


def create_bar_chart(data, title, x_name, y_name, hover_tool=None,
                     width=1200, height=300):
    """Creates a bar chart plot with the exact styling for the centcom
       dashboard. Pass in data as a dictionary, desired plot title,
       name of x axis, y axis and the hover tool HTML.
    """
    source = ColumnDataSource(data)
    xdr = FactorRange(factors=data[x_name])
    ydr = Range1d(start=0, end=max(data[y_name])*1.5)

    tools = []
    if hover_tool:
        tools = [hover_tool,]

    plot = figure(title=title, x_range=xdr, y_range=ydr, plot_width=width,
                  plot_height=height, h_symmetry=False, v_symmetry=False,
                  min_border=0, toolbar_location="above", tools=tools,
                  responsive=True, outline_line_color="#666666")

    glyph = VBar(x=x_name, top=y_name, bottom=0, width=.8, fill_color="#e12127")
    plot.add_glyph(source, glyph)

    xaxis = LinearAxis()
    yaxis = LinearAxis()

    plot.add_layout(Grid(dimension=0, ticker=xaxis.ticker))
    plot.add_layout(Grid(dimension=1, ticker=yaxis.ticker))
    plot.toolbar.logo = None
    plot.min_border_top = 0
    plot.xgrid.grid_line_color = None
    plot.ygrid.grid_line_color = "#999999"
    plot.yaxis.axis_label = "Bugs found"
    plot.ygrid.grid_line_alpha = 0.1
    plot.xaxis.axis_label = "Days after app deployment"
    plot.xaxis.major_label_orientation = 1
    return plot
