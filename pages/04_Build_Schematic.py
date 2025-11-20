import streamlit as st
from Extraction.base_functions import ui_widgets

from Side_Allocation.base_functions.symbol_viewer import GeometryCalculator
from Build_Schematic import Adding_common_pins



st.set_page_config(page_icon= 'dados/logo_small.png', page_title= "Parameters" )

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
#st.markdown(hide_st_style, unsafe_allow_html=True)
ui_widgets.header_intro()
ui_widgets.header_intro_2()

st.subheader("Build Schematic Page")


# Check if symbol data exists in session state
if 'symbol_figure' not in st.session_state or st.session_state['symbol_figure'] is None:
    st.warning("⚠️ No symbol found. Please complete Side Allocation first.")
    st.info("👈 Navigate to **02_Side_Allocation** page to generate a symbol.")
    st.stop()

# Get saved data from session state
fig = st.session_state['symbol_figure']
df = st.session_state['symbol_data']
part_name = st.session_state.get('part_name', 'Component')


# Main area - Display the symbol
st.subheader(f"Symbol Viewer: {part_name}")

# ✅ Display the saved Plotly figure
st.plotly_chart(fig, use_container_width=True)

# Optional: Show dataframe
with st.expander("📋 View Complete Pin Data"):
    st.dataframe(df, use_container_width=True, height=400)


# Initialize session state for attached symbols
if 'attached_grounds' not in st.session_state:
    st.session_state['attached_grounds'] = {}

# Sidebar: Pin list with action buttons
with st.sidebar:
    st.header("🔧 Add Schematic Symbols")
    st.write("Click on a pin to attach a ground symbol")
    
    st.divider()
    
    # Find ground-eligible pins
    ground_pins = df[df['Grouping'].str.contains('GND|Ground|Negative|ground|negative', case=False, na=False)]
    
    if len(ground_pins) > 0:
        st.subheader("⏚ Ground-Eligible Pins")
        
        # Display each pin with a button
        for idx, row in ground_pins.iterrows():
            pin_name = row['Pin Display Name']
            pin_num = row['Pin Designator']
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**{pin_name}** (Pin {pin_num})")
            
            with col2:
                # Check if already attached
                is_attached = pin_name in st.session_state['attached_grounds']
                
                if is_attached:
                    st.success("✓")
                else:
                    if st.button("➕", key=f"add_gnd_{pin_num}"):
                        # Store pin info for ground attachment
                        st.session_state['attached_grounds'][pin_name] = {
                            'pin_number': pin_num,
                            'pin_name': pin_name,
                            'side': row['Side']
                        }
                        st.rerun()
        
        # Clear all button
        if len(st.session_state['attached_grounds']) > 0:
            if st.button("🗑️ Clear All Grounds", use_container_width=True):
                st.session_state['attached_grounds'] = {}
                st.rerun()
    else:
        st.info("No ground pins detected")

# Main area
st.subheader(f"Symbol Viewer: {part_name}")
st.write(f"Ground symbols attached: {len(st.session_state['attached_grounds'])}")

# Display the figure (we'll add ground symbols in next step)
st.plotly_chart(fig, use_container_width=True)

# Show dataframe
with st.expander("📋 View Complete Pin Data"):
    st.dataframe(df, use_container_width=True, height=400)
