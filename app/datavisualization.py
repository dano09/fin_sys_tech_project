from bokeh.models import (HoverTool,FactorRange, Plot, LinearAxis, Grid,  Range1d)
from bokeh.models.glyphs import VBar
from bokeh.plotting import figure
from bokeh.models.sources import ColumnDataSource
from bokeh.layouts import gridplot
from bokeh.plotting import figure, show, output_file
#from IPython import get_ipython
import pandas as pd
import numpy as np


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


# plot using bokeh
def create_line_chart(df, width=1200, height=300):
    df = df.dropna(axis=0, how='any')
    print('inside create_line_chart func')
    # transform the data type of 'Date' to datetime64 and set it as index
    df['Date'] = pd.to_datetime(df['Date'])

    #delete the 00:00:00
    df['Date'] = df['Date'].dt.normalize()

    def datetime(x):
        return np.array(x, dtype=np.datetime64)

    #get_ipython().magic('matplotlib inline')
    tools_to_show = 'hover,box_zoom,pan,save,reset,wheel_zoom'
    p1 = figure(x_axis_type="datetime", title="Bitcoin Closing Prices", tools=tools_to_show)
    p1.grid.grid_line_alpha=0.3
    p1.xaxis.axis_label = 'Date'
    p1.yaxis.axis_label = 'Price'
    p1.toolbar.logo = None
    p1.line(datetime(df['Date']), df['Close Price'], color='#A6CEE3', legend='BTC')
    p1.legend.location = "top_left"

    hover = p1.select(dict(type=HoverTool))
    hover.tooltips = [("Close Price", "@y{0.00}"), ]
    hover.mode = 'mouse'

    return p1


# plot using bokeh
def create_vol_chart(vol,strike, width=1200, height=300):
    tools_to_show = 'hover,box_zoom,pan,save,reset,wheel_zoom'
    p2 = figure(title="Implied Vol", tools=tools_to_show)
    p2.grid.grid_line_alpha=0.3
    p2.xaxis.axis_label = 'Strike Price'
    p2.yaxis.axis_label = 'Implied Vol'
    p2.toolbar.logo = None
    p2.scatter(strike,vol,color='blue')
    p2.legend.location = "top_left"

    hover = p2.select(dict(type=HoverTool))
    hover.tooltips = [("Implied_Vol", "@y{0.00}"), ("Strike Price", "@x{0.00}"), ]
    hover.mode = 'mouse'

    return p2


# plot using bokeh
def create_PnL_chart(FT,PnL, width=1200, height=300):
    tools_to_show = 'hover,box_zoom,pan,save,reset,wheel_zoom'
    p2 = figure(title="Profit & Loss at Maturity", tools=tools_to_show)
    p2.grid.grid_line_alpha=0.3
    p2.xaxis.axis_label = 'Price at Maturity'
    p2.yaxis.axis_label = 'Profit & Loss'
    p2.toolbar.logo = None
    p2.line(FT,PnL,color='blue')
    p2.legend.location = "top_left"

    hover = p2.select(dict(type=HoverTool))
    hover.tooltips = [("PnL", "@y{0.00}"), ("Price at Maturity", "@x{0.00}"), ]
    hover.mode = 'mouse'

    return p2