# Server-side code for Circles mobile app.
Prod URI (reflects master): https://circles-6b621.appspot.com/
Dev URI (reflects latest commit to any branch): https://circles-dev-255922.appspot.com/

## To run a local instance of server:
1. Clone this repo
2. `cd` into repo
3. Activate virtualenv: `python3 -m venv .`
4. Install required packages: `pip install -r requirements.txt`
5. Run server: `python main.py`

## Dev/Build Architecture
- Push changes to new branch
- Create a pull request for changes
- Cloud Build (under circles-dev) is triggered; required check is that build must succeed
- One reviewer must approve the PR
- PR may be merged to master
- Cloud Build (under circles) is triggered; app deployed to prod
