from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="symbolgen",
    version="1.0.0",
    description="IC symbol generation tool for electronic component datasheets",
    license="MIT",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.apac.eng.renesas.com/ecad/symbolgen_streamlit",
    author="Renesas Electronics",
    author_email="rohith.srinivasan.wr@renesas.com",
    packages=find_packages(exclude=["tests", "*.tests", "*.tests.*", "tests.*"]),
    python_requires=">=3.8",
    install_requires=[
        "pandas>=2.0.0",
        "pdfplumber==0.11.4",
        "tabula-py>=2.0.0",
        "numpy>=1.24.0",
        "streamlit==1.38.0",
        "streamlit-pdf-viewer>=0.0.1",
        "python-dotenv>=1.0.0",
        "google-generativeai>=0.3.0",
        "openpyxl>=3.0.0",
        "fuzzywuzzy>=0.18.0",
        "PyPDF2>=3.0.0",
        "python-docx>=1.0.0",
        "Pillow==10.4.0",
        "PyMuPDF>=1.23.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "isort>=5.0.0",
            "flake8>=6.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "symbolgen=cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
