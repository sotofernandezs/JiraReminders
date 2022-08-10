from itertools import chain
import features


def get_home_ticket_view(ticket):
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f" *<https://google.com|{ticket['title']}>*"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "plain_text",
                "text": "Car needs to have oil change to avoid big sad money pitalso need to change tires multiline sample for when the message goes multiline",
                "emoji": True
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Comment",
                        "emoji": True
                    },
                    "value": "click_me_123"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Set Reminder",
                        "emoji": True
                    },
                    "value": "click_me_123",
                    "url": "https://google.com"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Dismiss 1 hour",
                        "emoji": True
                    },
                    "value": "click_me_123"
                }
            ]
        },
        {
            "type": "divider"
        }
    ]


def render_blocks(tickets, notif_enable):
    tickets_blocks = list(chain.from_iterable(
        [get_home_ticket_view(ticket) for ticket in tickets]
    ))
    return [
               {
                   "type": "header",
                   "text": {
                       "type": "plain_text",
                       "text": "Assigned Issues :computer:",
                       "emoji": True
                   }
               },
               {
                   "type": "divider"
               }] \
           + \
           tickets_blocks \
           + \
           [
               {
                   "type": "header",
                   "text": {
                       "type": "plain_text",
                       "text": "Important!",
                       "emoji": True
                   }
               },
               {
                   "type": "divider"
               },
               {
                   "type": "section",
                   "text": {
                       "type": "plain_text",
                       "text": "To receive notification messages , enable then clicking the button ",
                       "emoji": True
                   }
               },
               {
                   "type": "actions",
                   "elements": [
                       {
                           "type": "button",
                           "text": {
                               "type": "plain_text",
                               "emoji": True,
                               "text": "Turn on Messages" if not notif_enable else "Turn off messages"
                           },
                           "style": "primary" if not notif_enable else "danger",
                           "action_id": "act_enable_messages" if not notif_enable else "act_disable_messages"
                       }
                   ]
               }
           ]


def render_set_up_home_view():
    return {
        "type": "home",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Set up",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "plain_text",
                    "text": "To start using the app , you must first set up "
                            "the details to acces Jira related information",
                    "emoji": True
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Set up Reminders",
                            "emoji": True
                        },
                        "style": "primary",
                        "value": "click_me_123",
                        "action_id": "set_up_app"
                    }
                ]
            }
        ]
    }


def render_home_view(tickets, user):
    notif_enable = user.get('features', {}).get(features.FEATURE_NOTIFICATIONS, False)
    return {
        "type": "home",
        "callback_id": "home_view",
        "blocks": render_blocks(tickets, notif_enable)
    }


def render_set_up_modal_form(user_name):
    return {
        "type": "modal",
        "callback_id": "modal_set_up",
        "title": {
            "type": "plain_text",
            "text": "My App",
            "emoji": True
        },
        "submit": {
            "type": "plain_text",
            "text": "Submit",
            "emoji": True
        },
        "close": {
            "type": "plain_text",
            "text": "Cancel",
            "emoji": True
        },
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "plain_text",
                    "text": f":wave: Hey {user_name}!\n\nLet set up the jira reminders so you can keep your "
                            f"tickets up to date",
                    "emoji": True
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "input",
                "label": {
                    "type": "plain_text",
                    "text": "Select the features to enable",
                    "emoji": True
                },
                "element": {
                    "type": "checkboxes",
                    "action_id": "features",
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Enable Message Reminders",
                                "emoji": True
                            },
                            "value": "reminders"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Enable Ticker Summary",
                                "emoji": True
                            },
                            "value": "summary"
                        }
                    ]
                }
            },
            {
                "type": "input",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "jira_token"
                },
                "label": {
                    "type": "plain_text",
                    "text": "Jira Api token Value",
                    "emoji": True
                }
            }
        ]
    }
