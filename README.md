# Server-side code for Circles mobile app.
API uri: https://circles-6b621.appspot.com/

## To run a local instance of server:
1. Clone this repo
2. `cd` into repo
3. Activate virtualenv: `python3 -m venv .`
4. Install required packages: `pip install -r requirements.txt`
5. Run server: `python main.py`

## Dev/Build Architecture
- Push changes to new branch
- Create a pull request for changes
- Cloud Build is triggered; required check is that build must succeed
- One reviewer must approve the PR
- PR may be merged to master
- Cloud Build deploys app to App Engine
