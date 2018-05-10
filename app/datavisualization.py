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
    p1.line(datetime(df['Date']), df['Close Price'], color='#A6CEE3',
            legend='BTC',line_width=4)
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
    p2.scatter(strike,vol,color='blue', size = 10)
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
    p2.line(FT,PnL,color='blue', line_width=3)
    p2.legend.location = "top_left"

    hover = p2.select(dict(type=HoverTool))
    hover.tooltips = [("PnL", "@y{0.00}"), ("Price at Maturity", "@x{0.00}"), ]
    hover.mode = 'mouse'

    return p2


# plot using bokeh
def create_PDF_chart(FT, PDF, width=1200, height=300):
    tools_to_show = 'hover,box_zoom,pan,save,reset,wheel_zoom'
    p2 = figure(title="Implied Probability Density", tools=tools_to_show)
    p2.grid.grid_line_alpha=0.3
    p2.xaxis.axis_label = 'Price at Maturity'
    p2.yaxis.axis_label = 'Probability Density'
    p2.toolbar.logo = None
    p2.line(FT,PDF,color='red', line_width=3)
    p2.legend.location = "top_left"

    hover = p2.select(dict(type=HoverTool))
    hover.tooltips = [("Density", "@y{0.00}"), ("Price at Maturity", "@x{0.00}"), ]
    hover.mode = 'mouse'

    return p2