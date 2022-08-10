import os
# Use the package we installed
from typing import List, Any, Callable

from slack_bolt import App
from dotenv import load_dotenv
from itertools import chain
from apscheduler.schedulers.background import BackgroundScheduler
from views.home_view import render_home_view, render_set_up_home_view, render_set_up_modal_form
# Initializes your app with your bot token and signing secret
from slack_sdk import WebClient
import features
from jira import JIRA

from dataclasses import dataclass
from abc import ABC


@dataclass
class Comments:
    user: str
    text: str

    @staticmethod
    def from_dict(obj: Any) -> 'Comments':
        _user = str(obj.get("user"))
        _text = str(obj.get("text"))
        return Comments(_user, _text)


@dataclass
class Ticket:
    user_id: str
    code: str
    title: str
    description: str
    comments: List[Comments]

    @staticmethod
    def from_dict(obj: Any):
        _user_id = str(obj.get("user_id"))
        _code = str(obj.get("code"))
        _title = str(obj.get("title"))
        _description = str(obj.get("description"))
        _comments = Comments.from_dict(obj.get("comments"))
        return Ticket(_user_id, _code, _title, _description, _comments)


def init_app():
    return App(
        token=os.environ.get("SLACK_BOT_TOKEN"),
        signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
    )


# Add functionality here
# @app.event("app_home_opened") etc
class UserStore:
    __store = {}

    def add_user(self, user_id):
        return self.__store.setdefault(user_id, {})

    def user_enable_feature(self, user_id, feature_id):
        user = self.add_user(user_id)
        user.setdefault('features', {}).setdefault(feature_id, True)
        print(self.__store)

    def user_disable_feature(self, user_id, feature_id):
        user = self.add_user(user_id)
        user.setdefault('features', {}).setdefault(feature_id, False)

    def get_user(self, user_id):
        return self.__store.get(user_id)


class UserMapper:
    store = {
        'U02S7MW3R9V': 'f23a1992-eb17-4299-b4e8-d24c1c70722c'
    }

    def get_jira_user_from_slack_user(self, user_id):
        return self.store.get(user_id)


class AppConnector(ABC):

    def get_user_assigned_tickets(self, user_id) -> List[Ticket]:
        ...


class DummyJiraConnector(AppConnector):

    def get_user_assigned_tickets(self, user_id) -> List[Ticket]:
        tickets = [
            {
                'user_id': 'f23a1992-eb17-4299-b4e8-d24c1c70722c',
                'code': 'OPT-165',
                'title': 'OPT-165 Refactor car oil change',
                'description': 'This is a ticket description',
                'comments': {
                    'user': 'dcff5c7c-a360-4b8d-bee5-4e4636135550',
                    'text': 'this is a comment text'
                }
            },
            {
                'user_id': 'f23a1992-eb17-4299-b4e8-d24c1c70722c',
                'code': 'OPT-166',
                'title': 'OPT-166 Refactor car oil change',
                'description': 'This is a ticket description',
                'comments': {
                    'user': 'dcff5c7c-a360-4b8d-bee5-4e4636135550',
                    'text': 'this is a comment text'
                }
            },
            {
                'user_id': 'f23a1992-eb17-4299-b4e8-d24c1c70722c',
                'code': 'OPT-167',
                'title': 'OPT-167 Refactor car oil change',
                'description': 'This is a ticket description',
                'comments': {
                    'user': 'dcff5c7c-a360-4b8d-bee5-4e4636135550',
                    'text': 'this is a comment text'
                }
            }
        ]
        return [Ticket.from_dict(t) for t in tickets]


class RealJiraConnector(AppConnector):

    def __init__(self, email, token):
        self.jira = JIRA(server='https://test-reminders.atlassian.net/', basic_auth=(email, token))
        pass

    def get_user_assigned_tickets(self, user_id):
        my_tickets = self.jira.search_issues('project = REM  and assignee =  currentUser()')
        issues_list = []

        for issue in my_tickets:
            issue = Ticket(user_id=issue.fields.assigne,
                           code=issue.fields.key,
                           title=issue.fields.summary,
                           description=issue.fields.description)
            issues_list.append(issue)
        return issues_list


class JiraIntegration:

    def __init__(self, _jira_connector: Callable[[str, str], AppConnector]):
        self.__jira_connector_factory = _jira_connector
        self.__jira_connector = None

    def connect_with(self, email, token):
        self.__jira_connector = self.__jira_connector_factory(email, token)

    def get_user_assigned_tickets(self, user_id):
        tickets = self.__jira_connector.get_user_assigned_tickets(user_id)
        return tickets


class SlackRequests:

    def __init__(self, _app: App, _integration: JiraIntegration, _user_mapper: UserMapper,
                 _user_store: UserStore):
        self.app = _app
        self.integration = _integration
        self.user_mapper = _user_mapper
        self.user_store = _user_store
        self.setup()

    def setup(self):
        self.app.event("app_home_opened")(self.home_opened)
        self.app.action("act_enable_messages")(self.enable_messages)
        self.app.action("act_disable_messages")(self.disable_messages)
        self.app.action("set_up_app")(self.set_up_app)
        self.app.view("modal_set_up")(self.handle_set_up_modal_submit)

    def home_opened(self, client: WebClient, event):
        user_id = event['user']
        user_dict = self.user_store.add_user(user_id)
        is_set_up = user_dict.get('set_up', False)
        if is_set_up:
            self.__publish_home_view(client, user_id)
        else:
            client.views_publish(
                user_id=user_id,
                view=render_set_up_home_view()
            )

    def enable_messages(self, body, ack, say):
        user_id = body['user']['id']
        self.user_store.user_enable_feature(user_id=user_id, feature_id=features.FEATURE_NOTIFICATIONS)
        ack()
        say(text=f"<@{body['user']['username']}> Notification messages *enabled*", channel=user_id)
        self.__publish_home_view(app.client, user_id)

    def disable_messages(self, body, ack, say):
        user_id = body['user']['id']
        self.user_store.user_disable_feature(user_id=user_id, feature_id=features.FEATURE_NOTIFICATIONS)
        ack()
        self.__publish_home_view(app.client, user_id)

    def __publish_home_view(self, client, user_id):
        user = self.user_store.add_user(user_id)
        jira_user = self.user_mapper.get_jira_user_from_slack_user(user_id)
        jira_tickets = self.integration.get_user_assigned_tickets(jira_user)
        home_view = render_home_view(tickets=jira_tickets, user=user)
        print(home_view)
        client.views_publish(
            user_id=user_id,
            view=home_view
        )

    def set_up_app(self, body, ack, client):
        ack()
        jira_tickets = self.integration.get_user_assigned_tickets("jira_user")
        client.views_open(
            user_id=body['user']['id'],
            trigger_id=body['trigger_id'],
            view=render_set_up_modal_form(body['user']['username'])
        )

    def handle_set_up_modal_submit(self, body, client, ack):
        ack()
        input_vals_arr = [v for k, v in body['view']['state']['values'].items()]
        input_val_dict = {k: v for d in input_vals_arr for k, v in d.items()}
        features_arr = [v for v in input_val_dict['features']['selected_options']]
        features_arr_value = [d['value'] for d in features_arr]

        jira_token = input_val_dict['jira_token']['value']
        print(features_arr_value, jira_token)
        pass


#


if __name__ == "__main__":
    load_dotenv()
    scheduler = BackgroundScheduler()
    app = init_app()
    connector = lambda email, token: RealJiraConnector(email, token)
    SlackRequests(app, JiraIntegration(connector), UserMapper(), UserStore())
    # scheduler.scheduled_job()
    app.start(port=int(os.environ.get("PORT", 3000)))
