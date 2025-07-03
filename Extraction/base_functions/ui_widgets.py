import streamlit as st

def renesas_logo():

    image_path = 'dados/logo3.png'
    #st.logo(image_path) 
    print(f"Renesas Logo to be displayed...error")

def header_intro():
    col1, col3 = st.columns([1, 1])

    with col1:
        st.markdown("""
            <h1 style='color: #1c508c; font-size: 39px; vertical-align: top;'>SymbolGen</h1>
            <p style='font-size: 16px;'>Testing version 1.3 - Last update 27/05/2025</p>
        """, unsafe_allow_html=True)

    with col3:
        st.image('dados/logo3.png', width=250)
    
def header_intro_2():
    #st.write("This application's main functionality is to create Schematic Symbols from Standardised Datasheets and generate the .csv downloadable ")   
    st.write("Create schematic symbols from Renesas' new datasheets with ECAD Design information and generate a smart Symbol table. The smart table can be imported into Altium to generate an intelligent symbol.")
