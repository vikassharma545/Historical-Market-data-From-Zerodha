"""Local-development launcher — for users who cloned the repository.

Run with:
    streamlit run app.py

Installed users (pip install) should run:
    pyzdata-web
"""

# The actual app lives inside the package so it is available both when
# running locally (streamlit run app.py) and when installed (pyzdata-web).
from pyzdata._app import main

main()
