# About
The goal of this project is to create a wikipedia crawler which makes finding new information faster.


# Build
    git clone git@github.com:GRAYgoose124/wikicrawler.git
    cd wikicrawler

    pip -m build . --wheel
`pip install -e .` also works for an editable install.

# Run 
Run from the root folder of the project. 
(Currently using os.getcwd() instead of a unified root folder configuration.)