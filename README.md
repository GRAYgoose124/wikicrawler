# About ![example workflow](https://github.com/GRAYgoose124/wikicrawler/actions/workflows/tests.yml/badge.svg)

The goal of this project is to create a wikipedia crawler which makes finding new information faster. 

Currently it has a simple command line interface which you can access through the `arbiter` script installed by pip.

# Build
## 1. Retrieve
    git clone git@github.com:GRAYgoose124/wikicrawler.git
    cd wikicrawler
    pip install poetry

## 2. Build and Install
### 2a. Normal
    poetry install
### Graphviz
Please use conda to install graphviz on windows:

    conda install graphviz
    conda install python-graphviz
    
# Run
## Start
To start the app run after install: (use a venv!)

    arbiter

This will reveal a prompt, try the `help` and `st help`  command.

    > help
    > exit
## Typical workflows:
#### Search
    > s <phrase>
    > st found [idx]      # no idx: list, idx: get
    > st show [amount]      # float: percent, int: sentences
#### Collocation traverse
    > s <phrase>
    > o[racle] cmov <phrase>     # use most similar collocation in current page
#### State
    > st hist [idx]     # page traversal history

    > st found [idx]      # search travesal

    > st pop
    > st unpop
#### auto traverse
    > as <n> <start_phrase>

or, for auto building too:

    > bas <n> <start_phrase>
#### building markdown
After a valid search-type function:

    > seer build
## Issues
### Throttling / Rate limiting
Set the wiki_api_token in `~/.wikicrawler/config.json` to get autheticated rate throttling.