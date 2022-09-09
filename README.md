# About
The goal of this project is to create a wikipedia crawler which makes finding new information faster.

Currently it has a simple command line interface which you can access through the `arbiter` script installed by pip.

# Build & Run
## 1. Retrieve
    git clone git@github.com:GRAYgoose124/wikicrawler.git
    cd wikicrawler
## 2. Build and Install
### 2a. Normal
    pip install .
### 2b. Wheel
    pip install build
    python -m build . --wheel 
    pip install dist/<output_name>.whl
### 2c. Editable Install
    cd wikicrawler
    pip install -e .

## 3. Run
### Start
To start the app run after install: (use a venv!)

    arbiter

This will reveal a prompt, try the `help` and `st help`  command.

    > help
    > exit

### Typical workflows:

#### Search
    > s <phrase>
    > st found [idx]      # no idx: list, idx: get
    > st show [amount]      # float: percent, int: sentences
#### Collocation traverse
    > s <phrase>
    > ora cmov <phrase>     # use most similar collocation in current page
#### State
    > st hist [idx]     # page traversal history

    > st found [idx]      # search travesal

    > st pop
    > st unpop