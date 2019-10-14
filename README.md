# Server-side code for Circles mobile app.
Prod URI (reflects master): https://circles-6b621.appspot.com/
Dev URI (reflects latest commit to any branch): https://circles-dev-255922.appspot.com/

## To run a local instance of server:
1. Clone this repo
2. cd into repo and create virtualenv: `cd circles-server && python3 -m venv env`
3. Activate virtualenv: `source env/bin/activate`
4. Install required packages: `pip install -r requirements.txt`
	- If you run into an error, you may need to udpate pip before running the above command: `curl https://bootstrap.pypa.io/get-pip.py | python3`
5. Run server: `python main.py`

## Dev/Build Architecture
- Push changes to new branch
- Create a pull request to master for your changes
- Cloud Build (under circles-dev GCP project) is triggered; build must succeed to merge PR
- One reviewer must approve the PR
- PR may be merged to master
- Cloud Build (under circles GCP project) is triggered; app deployed to prod
