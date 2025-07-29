from setuptools import setup

with open("README.md", "r") as f:
    long_description = f.read()


setup(
    name="Symbol_Automation",
    version="1.0",
    description="An utility for extraction of component package information of a give datasheet",
    license="MIT",
    long_description=long_description,
    url="https://gitlab.apac.eng.renesas.com/ecad/ecad-automation-project",
    packages=[
        "Extraction",
        "Grouping",
        "Side_Allocation"
    ],
    install_requires=[
        "fitz",
        "jpype1",
        "pandas",
        "PyPDF2",
        "python-dotenv",
        "requests",
        "tabula-py",
        "tools",
        "openpyxl",
        "reportlab"
    ]
)
