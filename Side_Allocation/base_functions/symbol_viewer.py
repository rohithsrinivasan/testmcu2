"""
Symbol Viewer Utility Classes
Contains DataHandler, GeometryCalculator, and SymbolRenderer for ECAD symbol visualization
"""

import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List, Tuple


class DataHandler:
    """Handles data validation and processing."""
    
    REQUIRED_COLUMNS = [
        'Pin Designator', 'Pin Display Name', 'Electrical Type', 'Grouping', 'Side'
    ]
    
    @staticmethod
    def validate_dataframe(df: pd.DataFrame, part_name: str = None) -> Tuple[bool, List[str]]:
        """Validate DataFrame structure and content."""
        errors = []
        part_info = f" for part '{part_name}'" if part_name else ""
        
        if df.empty:
            errors.append(f"DataFrame{part_info} is empty")
            return False, errors
        
        missing_columns = [col for col in DataHandler.REQUIRED_COLUMNS if col not in df.columns]
        if missing_columns:
            errors.append(f"Missing required columns{part_info}: {missing_columns}")
        
        if 'Side' in df.columns:
            valid_sides = {'Left', 'Right'}
            invalid_sides = set(df['Side'].unique()) - valid_sides
            if invalid_sides:
                errors.append(f"Invalid Side values{part_info}: {invalid_sides}. Must be 'Left' or 'Right'")
        
        return len(errors) == 0, errors


class GeometryCalculator:
    """Calculates symbol dimensions and pin positions."""
    
    def __init__(self):
        self.config = {
            'min_symbol_width': 400.0,
            'min_symbol_height': 200.0,
            'pin_spacing': 40.0,
            'pin_length': 60.0,
            'text_height': 12.0,
            'margin': 20.0,
            'group_spacing': 60.0,
            'char_width_ratio': 0.6,
        }
    
    def calculate_symbol_geometry(self, df: pd.DataFrame) -> Dict:
        """Calculate overall symbol dimensions."""
        left_pins = df[df['Side'] == 'Left']
        right_pins = df[df['Side'] == 'Right']
        
        max_pin_name_length = df['Pin Display Name'].str.len().max()
        text_width = max_pin_name_length * self.config['text_height'] * self.config['char_width_ratio']
        
        min_width = (text_width * 6 + self.config['pin_length'] * 2 + self.config['margin'] * 4)
        symbol_width = max(self.config['min_symbol_width'], min_width)
        
        left_height = self.calculate_side_height(left_pins)
        right_height = self.calculate_side_height(right_pins)
        required_height = max(left_height, right_height)
        symbol_height = max(self.config['min_symbol_height'], required_height)
        
        return {
            'width': symbol_width,
            'height': symbol_height,
            'origin': (0.0, 0.0),
            'pin_spacing': self.config['pin_spacing'],
            'pin_length': self.config['pin_length'],
            'text_height': self.config['text_height'],
            'margin': self.config['margin']
        }
    
    def calculate_side_height(self, side_pins: pd.DataFrame) -> float:
        """Calculate required height for one side."""
        if side_pins.empty:
            return self.config['min_symbol_height']
        
        groups = side_pins['Grouping'].unique()
        total_height = self.config['margin'] * 2
        
        for group in groups:
            group_pins = side_pins[side_pins['Grouping'] == group]
            group_height = len(group_pins) * self.config['pin_spacing']
            total_height += group_height
        
        if len(groups) > 1:
            total_height += (len(groups) - 1) * self.config['group_spacing']
        
        return total_height
    
    def calculate_pin_positions(self, df: pd.DataFrame, geometry: Dict) -> List[Dict]:
        """Calculate positions for all pins - TOP to BOTTOM."""
        positions = []
        
        for side in ['Left', 'Right']:
            side_pins = df[df['Side'] == side].copy()
            if side_pins.empty:
                continue
            
            current_y = geometry['margin']
            groups = sorted(side_pins['Grouping'].unique())
            
            for group in groups:
                group_pins = side_pins[side_pins['Grouping'] == group].copy()
                #group_pins = group_pins.sort_values('Pin Designator')
                
                for _, pin_row in group_pins.iterrows():
                    if side == 'Left':
                        x = geometry['origin'][0] - geometry['pin_length']
                    else:
                        x = geometry['origin'][0] + geometry['width'] + geometry['pin_length']
                    
                    y = geometry['origin'][1] - current_y
                    
                    positions.append({
                        'x': x,
                        'y': y,
                        'side': side,
                        'pin_number': str(pin_row['Pin Designator']),
                        'pin_name': str(pin_row['Pin Display Name']),
                        'group': str(pin_row['Grouping'])
                    })
                    
                    current_y += geometry['pin_spacing']
                
                current_y += self.config['group_spacing']
        
        return positions


class SymbolRenderer:
    """Renders ECAD symbols using Plotly."""
    
    def __init__(self):
        self.geometry_calc = GeometryCalculator()


    def get_pin_hover_text(self, df: pd.DataFrame, pin: Dict) -> str:
        """Generate hover text for a pin."""
        # Get pin details from dataframe
        pin_match = df[df['Pin Designator'].astype(str) == str(pin['pin_number'])]
        
        if not pin_match.empty:
            pin_details = pin_match.iloc[0]
        else:
            pin_details = pd.Series({'Electrical Type': 'N/A', 'Pin Alternate Name': ''})
        
        # Build hover text
        hover_text = f"<b>{pin['pin_name']}</b><br>"
        hover_text += f"Pin: {pin['pin_number']}<br>"
        hover_text += f"Group: {pin['group']}<br>"
        
        # Safely get Electrical Type
        elec_type = pin_details.get('Electrical Type', 'N/A')
        if pd.notna(elec_type):
            hover_text += f"Electrical Type: {elec_type}<br>"
        
        # Add alternate name if available
        alt_name = pin_details.get('Pin Alternate Name', '')
        if pd.notna(alt_name) and alt_name and str(alt_name).strip():
            hover_text += f"Alternate Name: {alt_name}<br>"
        
        hover_text += f"Side: {pin['side']}"
        
        return hover_text
    
    def render_symbol(self, part_name: str, df: pd.DataFrame) -> go.Figure:
        """Create a Plotly figure with the symbol."""
        geometry = self.geometry_calc.calculate_symbol_geometry(df)
        pin_positions = self.geometry_calc.calculate_pin_positions(df, geometry)
        
        fig = go.Figure()
        
        max_y = -min(p['y'] for p in pin_positions)
        
        # Calculate ranges FIRST
        all_x = [p['x'] for p in pin_positions]
        all_y = [p['y'] for p in pin_positions]
        
        # SET LAYOUT FIRST - Lock the axis ranges
        fig.update_layout(
            title=dict(text=f"Symbol: {part_name}", x=0.5, xanchor='center'),
            hoverlabel=dict(bgcolor="white", font_size=12, font_family="Arial"),
            xaxis=dict(
                range=[min(all_x) - 100, max(all_x) + 100],
                showgrid=True,
                gridcolor='white',
                zeroline=False,
                showticklabels=False
            ),
            yaxis=dict(
                range=[min(all_y) - 50, max(all_y) + 50],
                showgrid=True,
                gridcolor='white',
                zeroline=False,
                showticklabels=False,
                scaleanchor='x',
                scaleratio=1,
                autorange=False,
                fixedrange=False
            ),
            plot_bgcolor='#f5f5f5',
            height=700,
            hovermode='closest'
        )
        
        # Draw symbol rectangle
        fig.add_shape(
            type="rect",
            x0=geometry['origin'][0],
            y0=0,
            x1=geometry['origin'][0] + geometry['width'],
            y1=-(max_y + geometry['margin']),
            line=dict(color="black", width=2),
            fillcolor="#f7f09c"
        )
        
        # Draw pins and labels
        for pin in pin_positions:
            if pin['side'] == 'Left':
                x0, x1 = pin['x'], geometry['origin'][0]
            else:
                x0, x1 = geometry['origin'][0] + geometry['width'], pin['x']
            
            fig.add_shape(
                type="line",
                x0=x0, y0=pin['y'],
                x1=x1, y1=pin['y'],
                line=dict(color="black", width=2)
            )
            
            # Add hover - Invisible hover point
            hover_text = self.get_pin_hover_text(df, pin)
            fig.add_trace(go.Scatter(
                x=[(x0 + x1) / 2],
                y=[pin['y']],
                mode='markers',
                marker=dict(size=10, opacity=0),
                hovertext=hover_text,
                hoverinfo='text',
                showlegend=False
            ))
            
            # Pin name
            if pin['side'] == 'Left':
                text_x = geometry['origin'][0] + geometry['margin']
                text_anchor = 'left'
            else:
                text_x = geometry['origin'][0] + geometry['width'] - geometry['margin']
                text_anchor = 'right'
            
            fig.add_annotation(
                x=text_x, y=pin['y'],
                text=pin['pin_name'],
                showarrow=False,
                xanchor=text_anchor,
                yanchor='middle',
                font=dict(size=14, color='black')
            )
            
            # Pin number
            if pin['side'] == 'Left':
                num_x = pin['x'] - 10
                num_anchor = 'right'
            else:
                num_x = pin['x'] + 10
                num_anchor = 'left'
            
            fig.add_annotation(
                x=num_x, y=pin['y'],
                text=pin['pin_number'],
                showarrow=False,
                xanchor=num_anchor,
                yanchor='middle',
                font=dict(size=14, color='gray')
            )
        
        return fig
