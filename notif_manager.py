import auth
from pyfcm import FCMNotification
from py2neo import Graph
from Models import Person, Circle, Event, GraphError

push_service = FCMNotification(api_key=auth.fcm_creds())
EVENT_NOTIF_TITLE = 'New Event Invite'
FRIEND_NOTIF_TITLE = 'New Friend Request'
CIRCLE_NOTIF_TITLE = 'New Circle'


def send_event_notif(graph, c, e, creator_id):
    for p in list(Circle.members_of(graph, c.__primaryvalue__)):
        # if p.__primaryvalue__ is creator_id: #don't send notification to creator
        #     continue
        try:
            send_notification(p.messaging_token, EVENT_NOTIF_TITLE,
                              'You\'ve been invited to {} for your Circle called {}. '
                              'Open the app for more details!'
                              .format(e.display_name, c.display_name))

        # TODO: figure out what exceptions come up
        except Exception as x:
            print('Unable to send notification: ' + str(x))


def send_new_circle_notif(graph, c, creator_id):
    for p in list(Circle.members_of(graph, c.__primaryvalue__)):
        # if p.__primaryvalue__ is creator_id: #don't send notification to creator
        #     continue
        try:
            send_notification(p.messaging_token, CIRCLE_NOTIF_TITLE,
                              'You\'ve been added to a new Circle called {}. '
                              'Open the app for more details!'
                              .format(c.display_name))

        # TODO: figure out what exceptions come up
        except Exception as x:
            print('Unable to send notification: ' + str(x))


def send_notification(notif_id, notif_title, notif_body):
    return push_service.notify_single_device(registration_id=notif_id,
                                             message_title=notif_title, message_body=notif_body)

