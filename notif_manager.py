<<<<<<< HEAD
=======
"""
Deifne methods for sending notifications via FCM.
"""
>>>>>>> 559ddf2a3d6953425bd4a5a55925a70d609da7f0
import auth
from pyfcm import FCMNotification
from py2neo import Graph
from Models import Person, Circle, Event, GraphError

push_service = FCMNotification(api_key=auth.fcm_creds())
EVENT_NOTIF_TITLE = 'New Event Invite'
<<<<<<< HEAD
FRIEND_NOTIF_TITLE = 'New Friend Request'
CIRCLE_NOTIF_TITLE = 'New Circle'


def send_event_notif(graph, c, e, creator_id):
    for p in list(Circle.members_of(graph, c.__primaryvalue__)):
        # if p.__primaryvalue__ is creator_id: #don't send notification to creator
        #     continue
=======
FRIEND_NOTIF_TITLE = 'New Friend'
CIRCLE_NOTIF_TITLE = 'New Circle'


def send_add_person_notif(graph, adder, people_to_notify):
    for p in people_to_notify:
        try:
            send_notification(p.messaging_token, FRIEND_NOTIF_TITLE,
                              '{} has added you as a friend!'
                              .format(adder.display_name))
        except Exception as x:
            print('Unable to send notification: ' + str(x))


def send_event_notif(graph, c, e, creator_id):
    for p in list(Circle.members_of(graph, c.__primaryvalue__)):
        if p.__primaryvalue__ is creator_id:  # don't send notification to creator
            continue
>>>>>>> 559ddf2a3d6953425bd4a5a55925a70d609da7f0
        try:
            send_notification(p.messaging_token, EVENT_NOTIF_TITLE,
                              'You\'ve been invited to {} for your Circle called {}. '
                              'Open the app for more details!'
                              .format(e.display_name, c.display_name))
<<<<<<< HEAD

        # TODO: figure out what exceptions come up
=======
>>>>>>> 559ddf2a3d6953425bd4a5a55925a70d609da7f0
        except Exception as x:
            print('Unable to send notification: ' + str(x))


<<<<<<< HEAD
def send_new_circle_notif(graph, c, creator_id):
    for p in list(Circle.members_of(graph, c.__primaryvalue__)):
        # if p.__primaryvalue__ is creator_id: #don't send notification to creator
        #     continue
=======
def send_new_circle_notif(graph, c, creator_id, people_to_notify):
    for p in people_to_notify:
        if p.__primaryvalue__ is creator_id:  # don't send notification to creator
            continue
>>>>>>> 559ddf2a3d6953425bd4a5a55925a70d609da7f0
        try:
            send_notification(p.messaging_token, CIRCLE_NOTIF_TITLE,
                              'You\'ve been added to a new Circle called {}. '
                              'Open the app for more details!'
                              .format(c.display_name))
<<<<<<< HEAD

        # TODO: figure out what exceptions come up
=======
>>>>>>> 559ddf2a3d6953425bd4a5a55925a70d609da7f0
        except Exception as x:
            print('Unable to send notification: ' + str(x))


def send_notification(notif_id, notif_title, notif_body):
    return push_service.notify_single_device(registration_id=notif_id,
                                             message_title=notif_title, message_body=notif_body)
<<<<<<< HEAD

=======
>>>>>>> 559ddf2a3d6953425bd4a5a55925a70d609da7f0
