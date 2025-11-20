import streamlit as st
import pandas as pd

# ✅ ADD THIS FUNCTION
def add_ground_symbol_to_fig(fig, pin_x, pin_y, pin_side):
    """Add a ground symbol at the pin location."""
    
    # Ground symbol size
    symbol_size = 150
    
    if pin_side == 'Left':
        # Ground extends to the left
        gnd_x = pin_x - symbol_size
    else:
        # Ground extends to the right
        gnd_x = pin_x + symbol_size
    
    gnd_y = pin_y
    
    # Draw ground symbol (three horizontal lines getting smaller)
    # Line 1 (top, longest)
    fig.add_shape(
        type="line",
        x0=gnd_x - 15, y0=gnd_y,
        x1=gnd_x + 15, y1=gnd_y,
        line=dict(color="black", width=3)
    )
    
    # Line 2 (middle)
    fig.add_shape(
        type="line",
        x0=gnd_x - 10, y0=gnd_y + 5,
        x1=gnd_x + 10, y1=gnd_y + 5,
        line=dict(color="black", width=3)
    )
    
    # Line 3 (bottom, shortest)
    fig.add_shape(
        type="line",
        x0=gnd_x - 5, y0=gnd_y + 10,
        x1=gnd_x + 5, y1=gnd_y + 10,
        line=dict(color="black", width=3)
    )
    
    # Connection line from pin to ground symbol
    fig.add_shape(
        type="line",
        x0=pin_x, y0=pin_y,
        x1=gnd_x, y1=gnd_y,
        line=dict(color="black", width=2)
    )
