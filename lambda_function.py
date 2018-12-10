"""
Alexa skills to Read news from various RSS new feeds ( The Hindu, Reuters, BBC, Times of India etc
"""

from __future__ import print_function

import feedparser
import pandas as pd
import re


def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])


def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "SectionIntent":
        return get_news_section(intent_request)
    elif intent_name == "AMAZON.HelpIntent":
        return get_help_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    elif intent_name == "AMAZON.FallbackIntent":
        return handle_session_fallback()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])



def get_welcome_response():
    session_attributes = {}
    card_title = "Welcome"
    speech_output = "<speak>What news do you want to read</speak>"
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with the same text.
    reprompt_text = speech_output
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def get_news_section(intent_request):
    session_attributes = {}
    card_title = "section"
    sound = "<audio src='soundbank://soundlibrary/musical/amzn_sfx_bell_short_chime_02'/>"
    speech_output = '<speak>'
    newspaper = intent_request["intent"]["slots"]["NewsPaper"]["value"]
    section = intent_request["intent"]["slots"]["section"]["value"]
    df = pd.read_csv("sourceurls.csv")

    df1 = df.pivot_table(index='Section', columns='Source', values='URL', aggfunc='first')
    usection = section.upper()
    unewspaper = newspaper.upper()
    if (usection in df['Section'].values) and (unewspaper in df['Source'].values):
        url = df1.loc[usection][unewspaper]
        d = feedparser.parse(url)
        if len(d['entries']) != 0 :
            i = 0
            clean = re.compile('<.*?>')
            if unewspaper == 'TOI':
                for post in d.entries:
                    speech_output = speech_output + post.title.replace("’","") + ". " + sound
                    i = i+1
                    if i >=5:
                        break
            else:
                for post in d.entries:
                    title = re.sub('[\',‘,&,’,\"]',"",post.title)
                    title = re.sub(clean,"",title)
                    desc = re.sub('[\',‘,&,’,\"]',"",post.description)
                    desc = re.sub(clean,"",desc)
                    speech_output = speech_output + title + ". " + desc + ". " + sound
                    i = i+1
                    if i >=5:
                        break

            speech_output = speech_output + "</speak>"
        else:
            speech_output = speech_output + "Sorry the news section is not available. What news do you want to read ?" + "</speak>"
    else:
        speech_output = speech_output + "Sorry the news section is not available. What news do you want to read ?" + "</speak>"

    reprompt_text = speech_output
    should_end_session = False
    return build_response(session_attributes,
                          build_speechlet_response(card_title, speech_output, reprompt_text, should_end_session))


def get_help_response():
    session_attributes = {}
    card_title = "Help"
    speech_output = "<speak>You can get new headlines from various new sources like BBC, Retuers, The Hindu, Time of India(TOI)." \
                    "You ask for example new from Reuters Sports section or BBC Asia etc.</speak>"
    reprompt_text = speech_output
    should_end_session = False
    return build_response(session_attributes,
                          build_speechlet_response(card_title, speech_output, reprompt_text, should_end_session))


def handle_session_fallback():
    session_attributes = {}
    card_title = "Fallback"
    speech_output = "<speak>Sorry did not get that. What news do you want to read</speak>"
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with the same text.
    reprompt_text = speech_output
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "<speak>Thank you for listening to the News.We hope you found it useful</speak>"
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))


# --------------- Helpers that build all of the responses ----------------------


def build_speechlet_response(title, output, reprompt_text, should_end_session):
    clean = re.compile('<.*?>')
    card_output = re.sub(clean,"",output)
    return {
        'outputSpeech': {
            'type': 'SSML',
            'ssml': output
        },
        'card': {
            'type': 'Simple',
            'title':  title,
            'content': card_output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'SSML',
                'ssml': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.1',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }
