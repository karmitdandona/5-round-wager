

from __future__ import print_function


# --------------- Main handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    if (event['session']['application']['applicationId'] !=
            "amzn1.ask.skill.f6ea6084-9f7c-44e0-9433-6bedcd60b55d"):
        raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])

# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "StartGame":
        return start_game(intent, session)
    elif intent_name == "GetWager":
        return get_wager(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return help_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here

# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': "SessionSpeechlet - " + title,
            'content': "SessionSpeechlet - " + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """

    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Welcome to 5 Round Wager. Say Help for instructions or Skip to start playing."
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "Please say Help for instructions or Skip to start the game."
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def help_response():
    """Contains the instructions of the game"""
    session_attributes = {}
    card_title = "Welcome"

    speech_output = "There are 5 rounds in this local 2 player game. The winner is whoever wins 3 of the 5 rounds. Both players will start with 6 coins. Round 1 begins with Player 1 wagering some of your coins. You can wager any number from 0 to 6. Player 2 then respons with their wager amount. The winner of a round is whoever wagers the most coins in that round. The loser of the round gets half of their coins spent in that round refunded, rounded up. The winner wagers first in the following round. This game is mathematically complex and strategic, so wager carefully! Say Help to repeat these instructions, or Skip to start the game."
    reprompt_text = "Please say Help for instructions or Skip to start the game."

    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Thanks for playing 5 round wager!"
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))


# --------------- Custom Game Logic ------------------

class Player(object):
    """Class for each player"""
    def __init__(self, coins = 6, roundsWon = 0):
        self.coins = coins
        self.roundsWon = roundsWon

class GameState(object):
    """Class for the state of the game"""
    def __init__(self, numOfRounds = 5, roundsToWin = 3, currentRound = 1, numOfPlayers = 2, currentPlayer = 1):
        self.numOfRounds = numOfRounds
        self.roundsToWin = roundsToWin
        self.currentRound = currentRound
        self.numOfPlayers = numOfPlayers
        self.currentPlayer = currentPlayer


def create_session_attributes(gameObject, playerArray):
    session_attributes = {}
    session_attributes.update(vars(gameObject))

    playerDict = {}
    for playerIndex in range(0, len(playerArray)):
        playerDict[playerIndex] = playerArray[playerIndex]
    session_attributes.update(playerDict)

    #sample format: {'numOfRounds': 5, 'roundsToWin': 3, 'currentRound': 0, 'numOfPlayers': 2, 'currentPlayer': 1, 0: {'coins': 6, 'roundsWon': 0}, 1: {'coins': 6, 'roundsWon': 0}}

    return session_attributes

def read_session_attributes(session_attributes):
    playerArray = []
    gameObjectAttributes = {}

    for key in session_attributes:
        if not str(key).isdigit():
            gameObjectAttributes[key] = session_attributes[key]
        else:
            playerArray.append(Player(**session_attributes[key]))
    gameObject = GameState(**gameObjectAttributes)

    return gameObject, playerArray

def start_game(intent, session):
    gameInstance = GameState()  # contains game  info

    playerArray = []  # array of length numOfPlayers for player info
    for i in range(1, gameInstance.numOfPlayers + 1):
        playerArray.append(Player())

def round_start(gameInstance, playerArray):
    card_title = "Round start"
    should_end_session = False
    speech_output = ("Welcome to Round %d. " % gameInstance.currentRound)

    for i in range(0, len(playerArray)):
        speech_output += ("Player %d, you have won %d rounds so far. You have %d coins left." % i+1, playerArray[i].roundsWon, playerArray[i].coins)




#
# def create_favorite_color_attributes(favorite_color):
#     return {"favoriteColor": favorite_color}
#
#
# def set_color_in_session(intent, session):
#     """ Sets the color in the session and prepares the speech to reply to the
#     user.
#     """
#
#     card_title = intent['name']
#     session_attributes = {}
#     should_end_session = False
#
#     if 'Color' in intent['slots']:
#         favorite_color = intent['slots']['Color']['value']
#         session_attributes = create_favorite_color_attributes(favorite_color)
#         speech_output = "I now know your favorite color is " + \
#                         favorite_color + \
#                         ". You can ask me your favorite color by saying, " \
#                         "what's my favorite color?"
#         reprompt_text = "You can ask me your favorite color by saying, " \
#                         "what's my favorite color?"
#     else:
#         speech_output = "I'm not sure what your favorite color is. " \
#                         "Please try again."
#         reprompt_text = "I'm not sure what your favorite color is. " \
#                         "You can tell me your favorite color by saying, " \
#                         "my favorite color is red."
#     return build_response(session_attributes, build_speechlet_response(
#         card_title, speech_output, reprompt_text, should_end_session))
#
#
# def get_color_from_session(intent, session):
#     session_attributes = {}
#     reprompt_text = None
#
#     if session.get('attributes', {}) and "favoriteColor" in session.get('attributes', {}):
#         favorite_color = session['attributes']['favoriteColor']
#         speech_output = "Your favorite color is " + favorite_color + \
#                         ". Goodbye."
#         should_end_session = True
#     else:
#         speech_output = "I'm not sure what your favorite color is. " \
#                         "You can say, my favorite color is red."
#         should_end_session = False
#
#     # Setting reprompt_text to None signifies that we do not want to reprompt
#     # the user. If the user does not respond or says something that is not
#     # understood, the session will end.
#     return build_response(session_attributes, build_speechlet_response(
#         intent['name'], speech_output, reprompt_text, should_end_session))