

from __future__ import print_function
from random import randint


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
            'title': title,
            'content': output
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

    speech_output = "There are 5 rounds in this local 2 player game. The winner is whoever wins 3 of the 5 rounds. Both players will start with 6 coins. Round 1 begins with Player 1 wagering some of your coins. You can wager any number from 0 to 6. Player 2 then respons with their wager amount. The winner of a round is whoever wagers the most coins in that round. The loser of the round gets their coins wagered in that round refunded. The winner wagers first in the following round. This game is mathematically complex and strategic, so wager carefully! If the round is a tie, the starting player of the following round is randomized. This can be an effective strategy to maintain a lead! Say Help to repeat these instructions, or Skip to start the game."
    reprompt_text = "Please say Help for the instructions again or Skip to start the game."

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
    def __init__(self, coins = 6, roundsWon = 0, previousWager = 0, hasPlayedThisRound = False):
        self.coins = coins
        self.roundsWon = roundsWon
        self.previousWager = previousWager  # useful for refunding coins to round loser(s)
        self.hasPlayedThisRound = hasPlayedThisRound

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
        playerDict[playerIndex] = vars(playerArray[playerIndex])
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
            playerDict = session_attributes[key]
            newPlayer = Player(**playerDict)
            playerArray.append(newPlayer)
    gameObject = GameState(**gameObjectAttributes)

    return gameObject, playerArray



def start_game(intent, session):
    gameInstance = GameState()  # contains game  info

    playerArray = []  # array of length numOfPlayers for player info
    for i in range(1, gameInstance.numOfPlayers + 1):
        playerArray.append(Player())

    session["attributes"] = create_session_attributes(gameInstance, playerArray)
    return round_start(intent, session)

def round_start(intent, session, speech_output = ""):
    gameInstance, playerArray = read_session_attributes(session["attributes"])

    card_title = "Round start"
    should_end_session = False
    speech_output += ("Welcome to Round %d. " % gameInstance.currentRound)

    for i in range(0, len(playerArray)):
        speech_output += ("Player %d, you have won %d rounds so far. You have %d coins left. " % (i+1, playerArray[i].roundsWon, playerArray[i].coins))

    speech_output += ("Player %d, you're up first this round. You have %d coins left. How many would you like to wager?" % (gameInstance.currentPlayer, playerArray[gameInstance.currentPlayer - 1].coins))

    reprompt_text = ("Sorry, didn't catch that. Player %d, you have %d coins left. How many would you like to wager?" % (gameInstance.currentPlayer, playerArray[gameInstance.currentPlayer - 1].coins))

    session_attributes = session["attributes"] # no need to create session attributes because none change within this function's scope
    return build_response(session_attributes, build_speechlet_response(card_title, speech_output, reprompt_text, should_end_session))

def get_wager(intent, session):
    """if this intent occurs, the first player has already said a number"""
    gameInstance, playerArray = read_session_attributes(session["attributes"])
    card_title = "Wager"
    should_end_session = False

    # if wager amount is more than current coins or is negative:
    if int(intent["slots"]["Number"]["value"]) > playerArray[gameInstance.currentPlayer - 1].coins or int(intent["slots"]["Number"]["value"]) < 0:
        speech_output = ("Sorry, that's not a valid wager of coins. You can wager 0 to %d coins. Player %d, how many would coins would you like to wager?" % (playerArray[gameInstance.currentPlayer - 1].coins, gameInstance.currentPlayer))
        reprompt_text = speech_output
        session_attributes = create_session_attributes(gameInstance, playerArray)
        return build_response(session_attributes, build_speechlet_response(card_title, speech_output, reprompt_text, should_end_session))

    playerArray[gameInstance.currentPlayer - 1].coins -= int(intent["slots"]["Number"]["value"]) # subtracts the wager amount from player's coin balance
    playerArray[gameInstance.currentPlayer - 1].previousWager = int(intent["slots"]["Number"]["value"])
    playerArray[gameInstance.currentPlayer - 1].hasPlayedThisRound = True

    #otherwise, this intent is valid. Now, we must check if the current player is last player. if they are, then round ends. if not, we prompt for next player to wager.

    turnNotOver = False
    for players in range(0, len(playerArray)):
        if playerArray[players].hasPlayedThisRound == False:
            gameInstance.currentPlayer = players + 1
            turnNotOver = True
            break
        else:
            continue
    if not turnNotOver:
        # round is over
        session["attributes"] = create_session_attributes(gameInstance, playerArray)
        return round_end(intent, session)
    else:
        # player has already been incremented to first player in playerArray that hasn't played yet
        speech_output = ("Player %d, you have %d coins left. How many do you want to wager?" % (gameInstance.currentPlayer, playerArray[gameInstance.currentPlayer - 1].coins))
        reprompt_text = "Sorry, didn't get that. How many coins do you want to wager?"

        session_attributes = create_session_attributes(gameInstance, playerArray)
        return build_response(session_attributes, build_speechlet_response(card_title, speech_output, reprompt_text, should_end_session))

def round_end(intent, session):
    gameInstance, playerArray = read_session_attributes(session["attributes"])

    # NOTE: might be more efficient to have a dict, where key=player# and value = previousWager... then see max value in entire dict (if it exists) and that's val's key is the winning play
    currentHighestWager = playerArray[0].previousWager
    roundWinner = 1
    roundIsTie = True  # this is for scalability, so if there's 10 players and 5 of them tie but some of them win, the below loop still works
    for player in range(0, len(playerArray)):
        if playerArray[player].previousWager != currentHighestWager:
            roundIsTie = False  # players have wagered diff amounts, so not possible to tie
            if playerArray[player].previousWager > currentHighestWager:
                currentHighestWager = playerArray[player].previousWager
                roundWinner = player + 1

    if roundIsTie:
        speech_output = "This round was a tie! All players get their wagers from this round refunded. The starting player of the next round will be randomized. "
        gameInstance.currentPlayer = randint(1, gameInstance.numOfPlayers)
        roundWinner = -1  # used as a function paramter for refunds
    else:
        speech_output = ("Player %d won this round! All other players get their wagers from this round refunded. " % roundWinner)
        gameInstance.currentPlayer = roundWinner
        playerArray[roundWinner-1].roundsWon += 1

    playerArray = coin_refunder(playerArray, roundWinner)
    gameInstance.currentRound += 1

    if is_game_over(gameInstance, playerArray):
        should_end_session = True
        card_title = "Game Over"
        reprompt_text = None

        gameWinner = -1  # remains -1 if game is tie, else becomes Player#
        for player in range(0, len(playerArray)):
            if playerArray[player].roundsWon >= gameInstance.roundsToWin:
                gameWinner = player + 1
                speech_output += ("Player %d won %d rounds. Player %d is the winner of 5 Round Wager! Thanks for playing!" % (gameWinner, gameInstance.roundsToWin, gameWinner))
                break
        if gameWinner == -1:
            # the game was a tie, no one won
            speech_output += ("Unfortunately, no player won %d rounds. This game of 5 Round Wager is a tie! Thanks for playing!" % (gameInstance.roundsToWin))

        session_attributes = create_session_attributes(gameInstance, playerArray)
        return build_response(session_attributes, build_speechlet_response(card_title, speech_output, reprompt_text, should_end_session))

    else:
        # game is not over
        for player in range(0, len(playerArray)):
            playerArray[player].hasPlayedThisRound = False
        session["attributes"] = create_session_attributes(gameInstance, playerArray)
        return round_start(intent, session, speech_output)


def coin_refunder(playerArray, roundWinner):
    """roundWinner is -1 if the round was a tie, so everyone will get a refund back"""
    for player in range(0, len(playerArray)):
        if (player + 1) != roundWinner:
            playerArray[player].coins += playerArray[player].previousWager
    return playerArray

def is_game_over(gameInstance, playerArray):
    if gameInstance.currentRound > gameInstance.numOfRounds:
        return True

    for player in range(0, len(playerArray)):
        if playerArray[player].roundsWon >= gameInstance.roundsToWin:
            return True

    return False
