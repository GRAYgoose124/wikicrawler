### Module Structure
- arbiter TODO: Clean up class names and strture.
    - script: Handles scripting backend for the arbiter.
    - prompt: Handles interactive cli and state traversal.
    - seer: interface the seer module to the scripting system.

- seer
    - handles state conversion to visualizations
        - markdown trees

- core
    - grabber
        - core handles the fetching and caching of links
    - seeker
        - extension to grabber, this can traverse by searching and special wiki pages.
    - crawler TODO: seeker extend crawler instead.
        - extension to seeker, which crawls links using raw wiki hrefs.
