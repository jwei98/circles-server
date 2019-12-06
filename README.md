# Server-side code for Circles mobile app.

## General info/features
- Flask app that runs on Google App Engine // GCP.
- Exposes a REST API (GET, POST, PUT, DELETE endpoints) for the client-side application.
- Database is a Neo4j (graph db) instance running on Google Compute Engine.
- Authentication/User-management with Firebase.
- Push notifications with Firebase Cloud Messaging.
- Credentials for GCE instance & FCM stored and queried through Cloud Datastore.

## Development/Build architecture
We have both a Development and Production build pipeline. Prod reflects code on master while Dev reflects the latest PR to master:
1. Push changes to new branch
2. Create a pull request to master for your changes
3. Cloud Build (under circles-dev GCP project) is triggered; build must succeed to merge PR
4. One reviewer must approve the PR
5. PR may be merged to master
6. Cloud Build (under circles GCP project) is triggered; app deployed to prod

## (Graph) Data Model
There are three nodes or "Objects":
1. Person
2. Circles
3. Events

Relationships exist as follows (note that edges can be queried bidirectionally in Neo4j):
(Person) <- <:KNOWS> ->  (Person)
(Person) - <:IS_MEMBER> ->  (Circle)
(Person) - <:INVITED_TO> ->  (Event)
(Circle) - <:SCHEDULED> ->  (Event)
