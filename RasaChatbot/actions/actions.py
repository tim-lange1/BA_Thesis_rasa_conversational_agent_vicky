from typing import Any, Text, Dict, List, Optional
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import UserUtteranceReverted, FollowupAction, AllSlotsReset, Restarted
from fuzzywuzzy import process
from datetime import datetime
# TALK
learningStyles = {
    "visual": ["diagram", "diagrams", "picture", "pictures", "movie", "movies", "chart", "charts", "film", "films", "visual", "map", "graph", "graphs", "image", "images"],
    "verbal": ["textinstruction", "textinstructions", "movie clip", "sound", "sound clip", "words", "word, text", "texts", "textual explanations", "text explanation", "text explanatations", "text summarization", "textsummarization", "textual summarization", "text sum", "textual explanation", "written", "written instructions", "verbal", "description", "descriptions", "sketch", "draft", "instructor", "teacher", "supervisor"],
    "sensor": ["realistic", "realistics", "data", "facts", "fact", "real life", "real life situations", "real", "careful", "carefully", "certainty", "concrete", "solid", "physical", "existing" "concrete material", "careful", "details", "real","factual", "factual data"],
    "intuitor": ["innovative", "hypothesis", "inovative", "innovatives", "theorie", "theories", "principles", "theory questions", "theory quests", "idea", "ideas", "intention", "theory quest", "abstract","theoretical","theoretical model", "abstract material", "concepts", "concept", "creative"],
    "active": ["try", "try it out", "try out it", "tries", "experimentals", "experimental", "practical", "start", "start directly", "start immediately", "immediately", "begin immediately", "begin directly", "begin", "take up"],
    "reflective": ["plan", "understand", "appreciate", "realize", "recognize", "try to understand"],
    "sequential": ["confused", "speed", "tempo", "regular", "regular pace", "structured", "well ordered", "efficient", "organized", "fairly", "regular", "step", "step by step", "steps", "stay focused", "focus", "focused", "stay on", "stay", "keep", "keep on"],
    "global": ["all clicks", "suddenly", "confused", "connections", "make connections", "consequences", "result", "effect", "conclusion", "results", "effects", "conclusions", "consequence", "links", "association", "relations"]
}
dialogLearningStyles = {
    "visual": 0,
    "verbal": 0,
    "sensor": 0,
    "intuitor": 0,
    "active": 0,
    "reflective": 0,
    "sequential": 0,
    "global": 0
}
learningStyleRecommendation = {
    "visual": "Visual learners remember best what they see e.g., pictures and diagrams. I've got some tips for you: \n Try to find a visual representation of course material. Prepare a concept map by listing key points, enclosing them in boxes or circles, and drawing lines with arrows between concepts to show connections. Colour-code your notes with a highlighter so that everything relating to one topic is the same color.",
    "verbal": "Verbal learners get more out of words such as written and spoken explanations. I've got some tips for you: \n Write summaries or outlines of course material in your own words. Working in groups can be particularly effective: you gain an understanding of the material by hearing classmates explanations and you learn even more when you do the explaining",
    "sensor": "Sensing learners tend to be patient with details and good at memorizing facts. You often like solving problems by well-established methods and dislike complications and surprises. You remember and understand information best if you can see how it connects to the real world. If you are in a class where most of the material is abstract and theoretical, you may have difficulty. I've got some tips for you: \n  Ask your tutor for specific examples of concepts and procedures, and find out how the concepts apply in practice. If the teacher does not provide enough specifics, try to find some in your course text or other references or by brainstorming with friends or classmates.",
    "intuitor": "Intuitive learners often prefer discovering possibilities and relationships. You tend to work fast and innovatively. You don´t like courses that involve a lot of memorization and routine calculations. If you happen to be in a class that deals primarily with memorization and rote substitution in formulas, you may have trouble with boredom. I've got some tips for you: \n Ask your tutor for interpretations or theories that link the facts, or try to find the connections yourself. You may also be prone to careless mistakes on tests because you are impatient with details and don't like repetition (such as in checking your completed  solutions). Take time to read the entire question before you start answering and be sure to check your results.",
    "active": "Active learners tend to retain and understand information best by doing something active with it e.g., discussing or applying it or explaining it to others. I've got some tips for you: \n  Study in a group in which the members take turns explaining different topics to each other. Work with others to guess what you will be asked on the next test and figure out how you will answer. You will always retain information better if you find ways to do something with it.",
    "reflective": "Reflective learners prefer to think about things quietly first. I've got some tips for you: \n If you don't have time to think about new information in class, try to do so during your wrap-up of class. Don't just passively read or memorize the material; pause periodically to review what you have read and think about possible questions or applications. It may be helpful to write short summaries of what you have read or class notes in your own words. This may take extra time, but it will help you to retain the material better.",
    "sequential": "Sequential learners tend to gain understanding in linear steps, with each step following logically from the previous one. Therefore you follow logical stepwise paths in finding solutions. I've got some tips for you: \n  Take the time to outline the lecture material for yourself in logical order. In the long run, doing so will save you time. You might also try to strengthen your global thinking skills by relating each new topic you study to things you already know. The more you can do so, the deeper your understanding of the topic is likely to be.",
    "global": "Global learners tend to learn in large jumps, absorbing material almost randomly without seeing connections, and then suddenly 'getting it'. You may be able to solve complex problems quickly or put things together in novel ways once you have grasped the big picture, but you may have difficulty explaining how you did it. You have to realize that you need the big picture of a subject before you can master details. If your tutor plunges directly into new topics without bothering to explain how they relate to what you already know, it can cause problems for you. Fortunately, there are steps you can take that may help you get the big picture more rapidly. I've got some tips for you: \n  Before you begin to study the first section of a chapter in a text, skim through the entire chapter to get an overview. Doing so may be time-consuming initially but it may save you from going over and over individual parts later. Instead of spending a short time on every subject every night, you might find it more productive to immerse yourself in individual subjects for large blocks. Try to relate the subject to things you already know. Don't lose faith in yourself.",
}
skip_slot = False
caughtLearningStyles_talk = list()
caughtLearningStyles = list()
game_learningstyle_list = list()
list = list()

clicked_recommendation = False
HAPPY = ["good", "fine", "alright", "sunny", "easygoing", "cheery",
         "happy", "breezy", "cool", "easy", "well", "satisfied"]
UNHAPPY = ["sad", "unhappy", "sick", "depressed", "dissatisfied",
           "troubled", "bad", "worried", "heavy-hearted", "okay"]

##########################################################################################
# Interruption
##########################################################################################


class askedBot(Action):
    def name(self) -> Text:
        return "action_asked_bot"

    def run(self, dispatcher: "CollectingDispatcher", tracker: "Tracker", domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(response='utter_iamabot')
        return [UserUtteranceReverted(), FollowupAction(tracker.active_form.get('latest_action_name'))]


class YourResidence(Action):
    def name(self) -> Text:
        return "action_your_residence"

    def run(self, dispatcher: "CollectingDispatcher",
            tracker: "Tracker",
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response='utter_residence')
        return [UserUtteranceReverted(), FollowupAction(tracker.active_form.get('latest_action_name'))]


class Learningstyle(Action):
    def name(self) -> Text:
        return "action_learningstyle"

    def run(self, dispatcher: "CollectingDispatcher",
            tracker: "Tracker",
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(response='utter_learningstyle')
        return [UserUtteranceReverted(), FollowupAction(tracker.active_form.get('latest_action_name'))]


class Killerphrases(Action):
    def name(self) -> Text:
        return "action_killerphrases"

    def run(self, dispatcher: "CollectingDispatcher",
            tracker: "Tracker",
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(response='utter_killerphrases')
        return [UserUtteranceReverted(), FollowupAction(tracker.active_form.get('latest_action_name'))]


class ActionOutOfScoop(Action):
    def name(self) -> Text:
        return "action_out_of_scope"

    def run(self, dispatcher: "CollectingDispatcher", tracker: "Tracker", domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(response='utter_out_of_scope')
        return [UserUtteranceReverted(), FollowupAction(tracker.active_form.get('latest_action_name'))]

class ActionNegation(Action):
    def name(self) -> Text:
        return "action_negation"

    def run(self, dispatcher: "CollectingDispatcher", tracker: "Tracker", domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(response='utter_negation')
        return [UserUtteranceReverted(), FollowupAction(tracker.active_form.get('latest_action_name'))]

class ActionTime(Action):
    def name(self) -> Text:
        return "action_time"

    def run(self, dispatcher: "CollectingDispatcher", tracker: "Tracker", domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        dispatcher.utter_message(text='The current time is ' + current_time)
        return [UserUtteranceReverted(), FollowupAction(tracker.active_form.get('latest_action_name'))]


class ActionAnswerBot(Action):
    def name(self) -> Text:
        return "action_answer_bot"

    def run(self, dispatcher: "CollectingDispatcher", tracker: "Tracker", domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(response='utter_answer_bot')
        return [UserUtteranceReverted(), FollowupAction(tracker.active_form.get('latest_action_name'))]


class ActionChitChat(Action):
    def name(self) -> Text:
        return "action_chitchat"

    def run(self, dispatcher: "CollectingDispatcher", tracker: "Tracker", domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        lastintent = tracker.latest_message['intent'].get('name')
        #if(lastintent == '')
        dispatcher.utter_message(response='utter_' + lastintent)
        return [UserUtteranceReverted(), FollowupAction(tracker.active_form.get('latest_action_name'))]


class ActionRepeatLastQuest(Action):
    def name(self) -> Text:
        return "action_repeat_last_quest"

    def run(self, dispatcher: "CollectingDispatcher", tracker: "Tracker", domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        getSlotValue = ""
        utter_action = ""
        last_question = ""
        for event in tracker.events:
            if event['event'] == 'slot':
                if event['name'] == 'requested_slot':
                    getSlotValue = event['value']
            if event['event'] == 'bot':
                utter_action = event['metadata'].get('utter_action')
                if utter_action == 'utter_greet/N':
                    last_question = 'utter_greet/N'
                elif utter_action == 'utter_greet/NN':
                    last_question = 'utter_greet/NN'
                elif utter_action == 'utter_how_you_are_doing/g':
                    last_question = 'utter_how_you_are_doing/request'
                elif utter_action == 'utter_how_you_are_doing/b':
                    last_question = 'utter_how_you_are_doing/request'
                elif utter_action == 'utter_how_you_are_doing/n':
                    last_question = 'utter_how_you_are_doing/request'
                if utter_action == 'utter_activity':
                    last_question = 'utter_activity'
                elif utter_action == 'utter_learning_style_recommendation_talk':
                    last_question = 'utter_learning_style_recommendation_talk'
                elif utter_action == 'utter_confirm_start_game':
                    last_question = 'utter_confirm_start_game'
                elif utter_action == 'utter_learning_style_recommendation_game':
                    last_question = 'utter_learning_style_recommendation_game'
                else:
                    last_question == 'utter_no_repeat'
        if getSlotValue is not None:
            if getSlotValue[0] == '2':
                dispatcher.utter_message(response='utter_ask_' + getSlotValue)
            else:
                dispatcher.utter_message(
                    response='utter_ask_' + getSlotValue + '/request')
        else:
            dispatcher.utter_message(response=last_question)
        return [UserUtteranceReverted(), FollowupAction(tracker.active_form.get('latest_action_name'))]

class ActionRephraseLearningStyle(Action):
    def name(self) -> Text:
        return "action_rephrase_learningstyle"

    def run(self, dispatcher: "CollectingDispatcher", tracker: "Tracker", domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        utter_action = ""
        rephrase = ""
        for event in tracker.events:
            if event['event'] == 'bot':
                utter_action = event['metadata'].get('utter_action')
                if utter_action == 'utter_learningstyle':
                    rephrase= "You take in and process information in different ways. A learning style is a method you use to learn. You can use recognition of their individual learning styles to find what study methods, environment, and activities help you to learn best."
                else:
                    rephase = "I'm sorry! That´s not possible at the moment. Therefore I need more trainingsdata."

        dispatcher.utter_message(text=rephrase)
        return [UserUtteranceReverted(), FollowupAction(tracker.active_form.get('latest_action_name'))]

class ActionUserUnkown(Action):
    def name(self) -> Text:
        return "action_user_unknown"

    def run(self, dispatcher: "CollectingDispatcher",
            tracker: "Tracker",
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(response := 'utter_user_unknown') 
        return [UserUtteranceReverted(), FollowupAction(tracker.active_form.get('latest_action_name'))] 
        
##########################################################################################
        # Namehandling
##########################################################################################


class ValidateNameForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_name_form"

    def validate_1_first_name(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate `first_name` value."""
        #print("begin",caughtLearningStyles, caughtLearningStyles_talk, dialogLearningStyles, game_learningstyle_list)

        name = slot_value
        if name is not None and len(name) > 0:
            dispatcher.utter_message(response='utter_greet/N')
            return {"1_first_name": slot_value}
        else:
            dispatcher.utter_message(response='utter_greet/N')
            return {"1_first_name": "name"}


class ActionGoodbyePersonByName(Action):
    def name(self) -> Text:
        return "action_goodbye_person_by_name"

    def run(self, dispatcher, tracker, domain):
        name = tracker.get_slot('1_first_name')
        if name is not None and len(name) > 0:
            dispatcher.utter_message(text=f"Bye {name}!")
        else:
            dispatcher.utter_message(text=f"Bye Buddy!")
        return []
##########################################################################################
        # Feeling
##########################################################################################
class ActionRestart(Action):
    def name(self) -> Text:
        return "action_restart"

    def run(self, dispatcher, tracker, domain):
        caughtLearningStyles.clear()
        caughtLearningStyles_talk.clear()
        gameLearningStylePoints.update({}.fromkeys(gameLearningStylePoints,0))
        dialogLearningStyles.update({}.fromkeys(dialogLearningStyles,0))
       # print("restart",caughtLearningStyles, caughtLearningStyles_talk, dialogLearningStyles, game_learningstyle_list)
        dispatcher.utter_message(text="I have been restarted. 🤖")
        return [AllSlotsReset(), Restarted()]


##########################################################################################
        # Feeling
##########################################################################################

    class ActionFeeling(Action):
        def name(self) -> Text:
            return "action_feeling"

        def run(self, dispatcher, tracker, domain):
            feeling = tracker.get_slot('1_how_you_are_doing')
            if feeling is not None:
                feeling = feeling.lower()

            if feeling in HAPPY:
                dispatcher.utter_message(response='utter_how_you_are_doing/g')
            elif feeling in UNHAPPY:
                dispatcher.utter_message(response='utter_how_you_are_doing/b')
            else:
                dispatcher.utter_message(response='utter_how_you_are_doing/n')
            return []


##########################################################################################
        # Explain Learning Style and start Talk Form or just start Talk Form
##########################################################################################

    class ActionExplain_Learning_Style(Action):
        def name(self) -> Text:
            return "action_explain_learning_style"

        def run(self, dispatcher, tracker, domain):
            if tracker.get_intent_of_latest_message() == "explain":
                dispatcher.utter_message(text="A learning style is a way in which you begin to concentrate on the process of absorbing and retaining new and difficult information. The interaction of these elements occurs differently in everyone. Therefore, it is necessary to determine what is most likely to trigger your concentration, how to maintain it, and how to respond to your natural processing style to produce long term memory and retention.")

            if tracker.get_intent_of_latest_message() == "not_explain":
                dispatcher.utter_message(
                    text="Okay, you can ask me this at a later time anyway. ")
            return []
##########################################################################################
        # Delay for utter_actitvity
##########################################################################################
    class ActionTimerUtterActivity(Action):
            def name(self) -> Text:
                return "action_timer_utter_activity"

            def run(self, dispatcher, tracker, domain):
                dispatcher.utter_message(response='utter_activity')

                
                return []
##########################################################################################
            # VALIDATIONFORM
##########################################################################################


class ValidateElicitationForm(FormValidationAction):
    """Validating our form input using quest from ILS """

    def name(self) -> Text:
        """Unique identifier of the form"""
        return "validate_elicitation_form"

    # validate user answers
    @staticmethod
    def answers_db(answer, learningStyles):
        """Database of LearningStyle answers"""
        for key, value in learningStyles.items():
            if answer.lower() in value:
                return key

    def create_validation_function(name_of_slot):
        """Function generate our validation functions, since  they're pretty much the same for each slot"""

        def validate_slot(
            self,
            value: Text,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
        ) -> Dict[Text, Any]:
            """Validate user input."""

           # print(tracker.required_slots())

            if type(value) == list:
                valueSec = ''.join(value)
                value = valueSec
            #print("Userinput", value)

            if self.answers_db(value, learningStyles) is not None:
                # validation succeeded, set the value of the slot to
                # user-provided value
                learningStyleItem = self.answers_db(value, learningStyles)
                # increase LearningStyleItem
                dialogLearningStyles[learningStyleItem] = dialogLearningStyles[learningStyleItem] + 1
                # print(name_of_slot,value)

                return {name_of_slot: value}
            else:
                # find the closest answer by some measure (edit distance?)
                for key, listValues in learningStyles.items():
                    answer = process.extractOne(value, listValues)
                    if answer[1] > 80:
                        break

                # check to see if distnace is greater than some threshold
                if answer[1] <= 80:
                    # if so, set slot to "None"
                    #   print("not found")
                    # maybe I don´t need that because of Fallback
                    # dispatcher.utter_message(text=f"Sorry, I didn't understand you, please try input something else")
                    return {name_of_slot: None}

                else:
                    learningStyleItem = self.answers_db(
                        answer[0], learningStyles)
                    # increase LearningStyleItem
                    dialogLearningStyles[learningStyleItem] = dialogLearningStyles[learningStyleItem] + 1
                    return {name_of_slot: answer[0]}
        return validate_slot

    validate_100_q_three = create_validation_function(
        name_of_slot="100_q_three")
    validate_101_q_twentyThree = create_validation_function(
        name_of_slot="101_q_twentyThree")
    validate_102_q_thirtyOne = create_validation_function(
        name_of_slot="102_q_thirtyOne")
    validate_103_q_twentyFive = create_validation_function(
        name_of_slot="103_q_twentyFive")
    validate_104_q_two = create_validation_function(name_of_slot="104_q_two")
    validate_105_q_eightTeen = create_validation_function(
        name_of_slot="105_q_eightTeen")
    validate_106_q_sevenTeen = create_validation_function(
        name_of_slot="106_q_sevenTeen")
    validate_107_q_thirtyEight = create_validation_function(
        name_of_slot="107_q_thirtyEight")
    validate_108_q_ten = create_validation_function(name_of_slot="108_q_ten")
    validate_109_q_twentyFour = create_validation_function(
        name_of_slot="109_q_twentyFour")
    validate_110_q_thirtySix = create_validation_function(
        name_of_slot="110_q_thirtySix")
    validate_111_q_seven = create_validation_function(
        name_of_slot="111_q_seven")
    validate_112_q_eleven = create_validation_function(
        name_of_slot="112_q_eleven")
    validate_113_q_twentySeven = create_validation_function(
        name_of_slot="113_q_twentySeven")
    validate_114_q_fourtyFour = create_validation_function(
        name_of_slot="114_q_fourtyFour")
    validate_115_q_twentyTwo = create_validation_function(
        name_of_slot="115_q_twentyTwo")
    validate_116_q_six = create_validation_function(name_of_slot="116_q_six")


##########################################################################################
    # Utter_Connections
##########################################################################################

    class Ask_108_q_ten(Action):
        def name(self) -> Text:
            return "action_ask_108_q_ten"

        def run(self, dispatcher, tracker, domain):
            learningStyleItem = ValidateElicitationForm.answers_db(
                tracker.get_slot("107_q_thirtyEight"), learningStyles)
            if learningStyleItem == "sensor":
                dispatcher.utter_message(response='utter_ask__108_q_ten/c')

            elif learningStyleItem == "intuitor":
                # say anderen fall
                dispatcher.utter_message(response='utter_ask__108_q_ten/a')

            else:
                dispatcher.utter_message(
                    text=f"Therefore do you find it easier to learn facts or to learn concepts?")
            return []

    class Ask_112_q_eleven(Action):
        def name(self) -> Text:
            return "action_ask_112_q_eleven"

        def run(self, dispatcher, tracker, domain):
            learningStyleItem = ValidateElicitationForm.answers_db(
                tracker.get_slot("111_q_seven"), learningStyles)
            if learningStyleItem == "visual":
                dispatcher.utter_message(response='utter_ask_112_q_eleven/vs')
            elif learningStyleItem == "verbal":
                dispatcher.utter_message(response='utter_ask_112_q_eleven/vb')
            else:
                dispatcher.utter_message(
                    text=f"If you look in a book with lots of diagrams. Do you likely look over the diagrams carefully or do you focus on the description")
            return []

    class Ask_113_q_twentySeven(Action):
        def name(self) -> Text:
            return "action_ask_113_q_twentySeven"

        def run(self, dispatcher, tracker, domain):
            learningStyleItem = ValidateElicitationForm.answers_db(
                tracker.get_slot("100_q_three"), learningStyles)
            if learningStyleItem == "visual":
                dispatcher.utter_message(
                    response='utter_ask_113_q_twentySeven/p')

            elif learningStyleItem == "verbal":
                dispatcher.utter_message(
                    response='utter_ask_113_q_twentySeven/w')
            else:
                dispatcher.utter_message(
                    text=f"Does it mean when you see a sketch in class do you likely to remember the sketch or that what the instructor said about it?")
            return []
##########################################################################################
            # DETECTION
##########################################################################################


class DetectLearningStyle(Action):
    def name(self) -> Text:
        return "action_detect_learning_style"

    def run(self, dispatcher, tracker, domain):
        #print(caughtLearningStyles_talk)
        #print(dialogLearningStyles)
        # visual_verbal
        if dialogLearningStyles['visual'] > dialogLearningStyles['verbal']:
            caughtLearningStyles_talk.append("visual")

            # firstLearningStyle = "Visual: " + learningStyleRecommendation['visual'] + "\n"
            firstLearningStyle = "Visual" + "\n"
        elif dialogLearningStyles['visual'] < dialogLearningStyles['verbal']:
            caughtLearningStyles_talk.append("verbal")

            # firstLearningStyle = "Verbal: " + learningStyleRecommendation['verbal']  + "\n"
            firstLearningStyle = "Verbal" + "\n"
        elif dialogLearningStyles['visual'] == dialogLearningStyles['verbal']:
            caughtLearningStyles_talk.append("visual")
            caughtLearningStyles_talk.append("verbal")
            # firstLearningStyle = "Neither visual nor verbal. Thus, your learning style is essentially well balanced in this category. \n Visual: " + learningStyleRecommendation['visual'] + "\n " + "Verbal: " + learningStyleRecommendation['verbal'] + "\n"
            firstLearningStyle = "Neither visual nor verbal. Thus, your learning style is essentially well balanced in this category. \n"

          # sensor_intuitor
        if dialogLearningStyles['sensor'] > dialogLearningStyles['intuitor']:
            caughtLearningStyles_talk.append("sensor")

            # secondLearningStyle = "Sensor: "+ learningStyleRecommendation['sensor']  + "\n"
            secondLearningStyle = "Sensor" + "\n"
        elif dialogLearningStyles['sensor'] < dialogLearningStyles['intuitor']:
            caughtLearningStyles_talk.append("intuitor")
            # secondLearningStyle = "Intuitor: "+ learningStyleRecommendation['intuitor']  + "\n"
            secondLearningStyle = "Intuitive" + "\n"
        elif dialogLearningStyles['sensor'] == dialogLearningStyles['intuitor']:
            caughtLearningStyles_talk.append("sensor")
            caughtLearningStyles_talk.append("intuitor")
            # secondLearningStyle = "Neither sensor nor intuitor. Thus, your learning style is essentially well balanced in this category. \n Sensor: " + learningStyleRecommendation['sensor'] + "\n " + "Intuitor: " + learningStyleRecommendation['intuitor']+ "\n"
            secondLearningStyle = "Neither sensor nor intuitive. Thus, your learning style is essentially well balanced in this category. \n"

          # active_reflective
        if dialogLearningStyles['active'] > dialogLearningStyles['reflective']:
            caughtLearningStyles_talk.append("active")
            # thirdLearningStyle = "Active: "+ learningStyleRecommendation['active']  + "\n"
            thirdLearningStyle = "Active" + "\n"
        elif dialogLearningStyles['active'] < dialogLearningStyles['reflective']:
            caughtLearningStyles_talk.append("reflective")

            # thirdLearningStyle = "Reflective: "+ learningStyleRecommendation['reflective']  + "\n"
            thirdLearningStyle = "Reflective" + "\n"
        elif dialogLearningStyles['active'] == dialogLearningStyles['reflective']:
            caughtLearningStyles_talk.append("active")
            caughtLearningStyles_talk.append("reflective")
            # thirdLearningStyle = "Neither active nor reflective. Thus, your learning style is essentially well balanced in this category. \n Active: " + learningStyleRecommendation['active'] + "\n " + "Reflective: " + learningStyleRecommendation['reflective']+ "\n"
            thirdLearningStyle = "Neither active nor reflective. Thus, your learning style is essentially well balanced in this category. \n "

            # sequential_global
        if dialogLearningStyles['sequential'] > dialogLearningStyles['global']:
            # fourthLearningStyle = "Sequential: "+ learningStyleRecommendation['sequential']  + "\n"
            fourthLearningStyle = "Sequential" + "\n"
            caughtLearningStyles_talk.append("sequential")

        elif dialogLearningStyles['sequential'] < dialogLearningStyles['global']:
            caughtLearningStyles_talk.append("global")

            fourthLearningStyle = "Global" + "\n"
        elif dialogLearningStyles['sequential'] == dialogLearningStyles['global']:
            caughtLearningStyles_talk.append("sequential")
            caughtLearningStyles_talk.append("global")
            # fourthLearningStyle = "Neither sequential nor global. Thus, your learning style is essentially well balanced in this category. \n Sequential: " + learningStyleRecommendation['sequential'] + "\n " + "Global: " + learningStyleRecommendation['global']+ "\n"
            fourthLearningStyle = "Neither sequential nor global. Thus, your learning style is essentially well balanced in this category. \n"
        dispatcher.utter_message(
            text=f"\n  After our conversation, I identified the following learning styles: \n - {firstLearningStyle} - {secondLearningStyle} - {thirdLearningStyle} - {fourthLearningStyle} \n")

        return []


##########################################################################################
        # QuestGame
##########################################################################################
gameLearningStylePoints = {
    "visual": 0,
    "verbal": 0,
    "sensor": 0,
    "intuitor": 0,
    "active": 0,
    "reflective": 0,
    "sequential": 0,
    "global": 0
}
LogicRules = {
    "1": ["intuitor"],
    "2": ["visual", "verbal"],
    "3": ["visual"],
    "4": ["sensor"],
    "5": ["intuitor"],
    "6": ["intuitor", "global"],
    "7": ["global", "intuitor"],
    "8": ["sequential", "reflective",],
    "9": ["sequential", "verbal"],
    "10a": ["sensor", "verbal"],
    "10b": ["intuitor", "visual"],
    "11a": ["active", "sensor"],
    "11b": ["reflective", "intuitor"]
}


class ValidateQuestGameForm(FormValidationAction):
    """Validating answers from the User """
    generalAttemp = 0
    lasthelp = ""
    counter = 0
    seq = ""
    code = ""
    seqProcess = False
    splitpoint = False
    shortcut = False

    def name(self) -> Text:
        return "validate_quest_game_form_part_one"

    # validate user answers
    # @staticmethod
    def questGameAnswers_db() -> Dict[str, List]:
        """Database of questanswers"""
        return {
            "200_qG0": ["thursday", "Thursday"],
            "201_qG1": ["left", "Left"],
            "307_qG7": ["qG07B"],
            "304_qG4": ["blue", "Blue"],
            "305_qG5": ["twenty-seven"],
            "305_qG5seq": ["double", " doubled", "twice", "two", "2"],
            "306_qG6": ["9/8.5/7", "9/8,5/7"],
            "209_qG9": ["qG09D"],
            "208_qG8": ["XV", "xv"],
            "208_qG8seq": ["three","increment of 3","increase of 3", "increase of three", "increment of three", "higher of three", "higher of 3", "3 more", "three more", "triple", "3", "threefold"],
        }

    def questGameLearningstyle_db() -> Dict[str, List]:
        """Database of LearningStyle"""
        return {
            "200_qG01": ["6", "7", "10a",  "11b"],  # firstTry
            "200_qG02": ["1", "6","10b","11b"],  # text
            "200_qG03": ["3", "6","10b", "11b"],  # image
            "200_qG06": ["1","10b", "11b"],  # text >firstTry
            "200_qG07": ["3","10b", "11b"],  # image > firstTry
            "200_qG010": ["9", "10b","11b"],  # >firstTry without Help

            "201_qG11": ["6", "7", "11a"],
            "201_qG12": ["1", "6", "11a"],  # text
            "201_qG14": ["2", "6", "11a"],  # movie
            "201_qG15": ["4", "6", "11a"],  # example
            "201_qG16": ["1", "11a"],  # >ft text
            "201_qG18": ["2", "11a"],  # >ft movie
            "201_qG19": ["4", "11a"],  # >ft example
            "201_qG110": ["9", "11a"],  # >ft oH

            "304_qG41": ["6", "7", "10a","11b"],
            "304_qG42": ["1", "6", "10b","11b"],  # text
            "304_qG46": ["1","10b","11b"],  # >ft text
            "304_qG410": ["9", "10b","11b"],  # >ft oH

            "305_qG51": ["6", "7", "11a"],
            "305_qG52": ["6", "8", "11a"],  # text
            "305_qG56": ["9", "11a"],  # >ft text
            "305_qG510": ["9", "11a"],  # >ft oH

            "306_qG61": ["6", "7", "11a"],
            "306_qG62": ["1", "6", "11a"],  # text
            "306_qG64": ["2", "6", "11a"],  # movie
            "306_qG65": ["4", "6", "11a"],  # example
            "306_qG66": ["1", "11a"],  # >ft text
            "306_qG68": ["2", "11a"],  # >ft movie
            "306_qG69": ["4", "11a"],  # >ft example
            "306_qG610": ["9", "11a"],  # >ft oH

            "307_qG71": ["6", "7", "11a"],
            "307_qG72": ["1", "6", "11a"],  # text
            "307_qG74": ["2", "6", "11a"],  # movie
            "307_qG76": ["1", "11a"],  # >ft text
            "307_qG78": ["2",  "11a"],  # >ft movie
            "307_qG710": ["9", "11a"],  # >ft oH

            "208_qG81": ["6", "7", "11a"],
            "208_qG82": ["6", "8", "11a"],  # text
            "208_qG86": ["8","9", "11a"],  # >ft text
            "208_qG810": ["9", "11a"],  # >ft oH

            "209_qG91": ["6", "7", "11b"],  # firstTry
            "209_qG92": ["1", "6", "11b"],  # text
            "209_qG93": ["3", "6", "11b"],  # image
            "209_qG96": ["1", "11b"],  # text >firstTry
            "209_qG97": ["3", "11b"],  # image > firstTry
            "209_qG910": ["9", "11b"],  # >firstTry without Help


        }

    def qGHelpAndAnswers_db() -> Dict[str, List]:
        """Database of LearningStyle"""
        return {
            "200_qG0": [{"qG00solution": "I say you the solution. You can see that now must be Friday since two days from Friday is Sunday. The 'day before yesterday' is Wednesday, and the 'day that follows the day before yesterday' is Thursday. Let ́s move on to the next question."},
                        {"qG00textHelp": "The key is to realize that 'now' must be Friday. Look for the phrase in the problem that tells you something you can work with and use that with another part of the problem to gradually and stepwise lead to a solution."},
                        {"qG00imageHelp": "Look, here is an image which explains the topic very well. 😉 \n https://i.ibb.co/jb2VYc7/quest1-2.jpg. \n When you finished trying to answer or use another button."},
                        {"Answer": "That ́s right, well done ✅ 🤙. You can see that now must be Friday since two days from Friday is Sunday. The 'day before yesterday' is Wednesday, and the 'day that follows the day before yesterday' is Thursday. Let ́s move on to the next question!"},
                        ],
            "201_qG1": [{"qG01solution": "5/19 because with cross multiplication, calculating 5 x 29 yields 145, and calculating 29 x 5 yields 57. Finally, 145 is greater than 57, so 5/19 is greater than 3/29."},
                        {"qG01textHelp": "Look, here is a website which explains the topic very well. 😉 \n https://www.mathsisfun.com/comparing-fractions.html.\n When you are finished, feel free to type in the answer or press another button if you need help."},
                        {"qG01movieHelp": "Look, here is a video that explains the topic very well. 😉 \n https://www.youtube.com/watch?v=KNdUJQ_qd4U.\n When you are finished, feel free to type in the answer or press another button if you need help."},
                        {"qG01exampleHelp": "You have fractions 1/2 and 3/4. 1/2 equals 0.5, and 3/4 equals 0.75. Otherwise, you can get the higher fraction by cross-multiplying. If you multiply the denominator of the first term by the numerator of the second term, you calculate 2 x 4 = 8. So, the second term has the number 8. For the other term, you calculate 4 x 1 = 4. Therefore, the first term has the number 4. 8 is greater than 4. Finally, the second term is greater than the first term."},
                        {"Answer": "Yeeah you got it, cool! ✅ 🤙. Because with cross multiplication, calculating 5 x 29 yields 145, and calculating 29 x 5 yields 57. Finally, 145 is greater than 57, so 5/19 is greater than 3/29."}
                        ],

            "209_qG9":  [
                {"qG09solution": "Greenhouse gases trap heat that is radiated from the surface."},
                {"qG09textHelp": "Look, here is a website which explains the topic very well. 😉 \n https://climatekids.nasa.gov/greenhouse-effect/"},
                {"qG09translatorHelp": "Look up here: https://dict.leo.org/englisch-deutsch/"},
                {"qG09imageHelp": "Look, here is an image which explains the topic very well. 😉 \n https://i.ibb.co/tB3nT9p/greenhouse-effect.png.\n When you are finished, feel free to type in the answer or press another button if you need help."},
                {"Answer": "Yeeah you got it, cool! ✅ 🤙. Greenhouse gases trap heat that is radiated from the surface."},

            ],
            "304_qG4":  [{"qG04textHelp": "There are three possible colors: green, blue, and red. Have a look at this sentence: “The coat, belonging to Tessa…”"},
                         {"qG04solution": "It is blue. None of these clothes have the same color. Tessa's coat is not green. Tessa's skirt is red. So, Tessa’s coat must be blue because the clothes are only available in blue, green, or red."},
                         {"Answer": "Yeeah you got it, cool! ✅ 🤙. It is blue. None of these clothes have the same color. Tessa's coat is not green. Tessa's skirt is red. So, Tessa’s coat must be blue because the clothes are only available in blue, green, or red."},
                         ],
            "305_qG5":  [{"qG05textHelp": "Buddy, we will work out the solution together step by step. First, try to answer the next sub-question: By comparing each number between the bottom row and the top row, which connection do you recognize? If you know the solution for the quiz question, feel free to tell me. If not, you can also answer with 'Need Help'."},
                         {"qG05solution": "The numbers in the bottom row are always twice the numbers in the top row, so it must be twenty-seven. Let's move on."},
                         {"Answer": "That ́s right, well done ✅ 🦾. The numbers in the bottom row are always twice the numbers in the top row, so it must be twenty-seven. Let's move on."},
                         {"Answerseq": "That ́s right ✅ 👍. Each number is double. Which number would replace the question mark?"},
                         {"AnswerseqF": "I will give you some dummy numbers as an example. Add to the top row a three and to the bottom row eighteen. Try to answer the next subquestion first: Can you tell me now a Relationship? If not answer with 'Need Help'"},
                         {"AnswerseqFF": "The numbers in the bottom row are always twice the numbers in the top row. Which number would replace the question mark?"}
                         ],
            "306_qG6": [{"qG06solution": "The mean is 9. Let me explain how to calculate the solution. 7 + 7 + 14 + 10 + 3 + 7 + 14 = 72. 72 divided by 8, which is the number of integers, gives 9. To find the median, you get the series 3,7,7,10,10,14,14. Now you have to calculate the average of the two numbers in the middle, so (7 + 10) / 2 = 8.5. The mode represents the most frequent number. The series contains the number 7 three times. Thus, the mode is 7."},
                        {"qG06textHelp": "To calculate the mean value, you have to add up all the numbers. Then divide them by the total amount of numbers you got. For the median, you need to sort the numbers in order from smallest to largest. If you have an uneven data set, take the number in the middle for the median. For an even data set, the median is the average of the two middle values. The mode shows the most frequent number in the data set. "},
                        {"qG06movieHelp": "Look, here is a video that explains the topic very well. 😉 \n https://www.youtube.com/watch?v=B1HEzNTGeZ4. \n When you are finished, feel free to type in the answer or press another button if you need help."},
                        {"qG06exampleHelp": "Dataset: 2,2,3,4. Mean: First you add all numbers: 2+4+3+2 = 11. After that, you divide the result by how many numbers you got: 11 / 4 = 2.75 Median: order the items: 2,2,3,4. Get the two numbers in the middle: 2+3 and divide them by 2. You get 2.5 as a result. Mode: indicates the most often number. The number 2 occurs two times. Therefore the number 2 is the Mode."},
                        {"Answer": "Yeeah you got it, cool! ✅ 🤙. The mean is 9. Let me explain how to calculate the solution. 7 + 7 + 14 + 10 + 3 + 7 + 14 = 72. 72 divided by 8, which is the number of integers, gives 9. To find the median, you get the series 3,7,7,10,10,14,14. Now you have to calculate the average of the two numbers in the middle, so (7 + 10) / 2 = 8.5. The mode represents the most frequent number. The series contains the number 7 three times. Thus, the mode is 7."},
                        ],
            "307_qG7":  [
                {"qG07solution": "Greenhouse gases absorb heat, and sunlight is the energy source for heat."},
                {"qG07textHelp": "Look, here is a website which explains the topic very well. 😉 \n https://news.climate.columbia.edu/2021/02/25/carbon-dioxide-cause-global-warming/"},
                {"qG07movieHelp": "Look, here is a video that explains the topic very well. 😉  \n https://www.youtube.com/watch?v=SN5-DnOHQmE&t=2s"},
                {"qG07translatorHelp": "Look up here: https://dict.leo.org/englisch-deutsch/"},
                {"Answer": "Yeeah you got it, cool! ✅ 🤙. Greenhouse gases absorb heat, and sunlight is the energy source for heat."},
            ],
            "208_qG8":  [
                {"qG08solution": "There are two alternating sequences: 0, I, III, V, VII, IX and 0, III, VI, IX, XII. Thus, the next number is XV."},
                {"qG08textHelp": "Hey buddy, we'll work out the solution together step by step. Look at the second, fourth, sixth, eighth and tenth numbers. Try answering the next sub-question first: Which relation do you see between the numbers, perhaps a particular increment? If you should get stuck, answer with ‘Help’."},
                {"Answer": "That ́s right, well done ✅ 🦾. There are two alternating sequences: 0, I, III, V, VII, IX and 0, III, VI, IX, XII. Thus, the next number is XV."},
                {"Answerseq": "That ́s right, well done ✅ 👍. There are two alternating sequences: 0, I, III, V, VII, IX and 0, III, VI, IX, XII. So which would be the next Roman numbers?"},
                {"AnswerseqF": "Look, there are two alternating sequences: 0, I, III, V, VII, IX and 0, III, VI, IX, XII. Which relation do you see between the numbers, perhaps a particular increment?"},
                {"AnswerseqFF": "There are two alternating sequences: 0, 1, 3, 5, 7, 9 and 0, 3, 6, 9, 12. Between the numbers are is increment of three. So which would be the next number in Roman numbers?"}

            ],
        }

    @staticmethod
    def getHistory(tracker):
        messages = []
        for event in (list(tracker.events)):
            if event.get("event") == "user":
                messages.append(event.get("text"))
                return messages

    def splitpoints(name_of_slot, choices, value, dispatcher):
        msg = ""
        x = ""
        # validate Format
        regex = False
        tokenCounter = 0
        for element in range(0, len(value)):
            if (value[element] == '/') | (value[element] == '-'):
                tokenCounter += 1
                if tokenCounter == 2:
                    regex = True
        if(regex):
            if(name_of_slot == "306_qG6"):
                x = '/'
            elif(name_of_slot == "202_qG2"):
                x = '-'
            if(choices[0].split(x)[0] == value.split(x)[0]):
                msg += "first number is right! "
                ValidateQuestGameForm.splitpoint = True
            if(choices[0].split(x)[1] == value.split(x)[1]) | (choices[1].split(x)[1] == value.split(x)[1]):
                msg += "second number is right! "
                ValidateQuestGameForm.splitpoint = True
            if(choices[0].split(x)[2] == value.split(x)[2]):
                ValidateQuestGameForm.splitpoint = True
                msg += "third number is right! "
        else:
            msg = ""
        regex = False
        tokenCounter = 0
        dispatcher.utter_message(
            text="Sorry that´s wrong 😕 but " + msg + "keep Going!")

    @staticmethod
    def get_previous_slot_value_from_tracker(tracker: Tracker, slot: Text) -> Optional[Any]:
        is_first = True
        for event in reversed(tracker.events):
            if event["event"] == "slot" and event["name"] == 'requested_slot':
                if is_first:
                    is_first = False
                else:
                    return event["value"]
            if event["event"] == "session_started":
                return None

    @staticmethod
    def getKeyValuePairHelpers(helperAnswerChoices, userinput):
        for item in helperAnswerChoices:
            for key in item:
                if key == userinput:
                    return item[key]

    @staticmethod
    def clean_up_user_input(value):
        if type(value) == list:
            return value[0]
        else:
            return value

    def create_validation_function(name_of_slot):
        """Function generate our validation functions, since
        they're pretty much the same for each slot"""

        if(name_of_slot == "305_qG5") | (name_of_slot == "208_qG8"):
            # processquests
            def validate_process_quests(self, value: Text, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any],) -> Dict[Text, Any]:
                value = ValidateQuestGameForm.clean_up_user_input(value)
                helperAnswerChoices = []
                helperAnswerChoices = ValidateQuestGameForm.qGHelpAndAnswers_db()[
                    name_of_slot]
                helperText = ValidateQuestGameForm.getKeyValuePairHelpers(
                    helperAnswerChoices, value)
                # user selected solution
                if(value[4:] == "solution"):
                    ValidateQuestGameForm.seqProcess = False
                    ValidateQuestGameForm.lasthelp = ""
                    ValidateQuestGameForm.generalAttemp = 0
                    dispatcher.utter_message(text=helperText)
                    return {name_of_slot: "solution"}

                # user selected HelpText
                if value[4:] == "textHelp":
                    dispatcher.utter_message(text=helperText)
                    ValidateQuestGameForm.lasthelp = "text"
                    ValidateQuestGameForm.seq = "seq"
                    ValidateQuestGameForm.seqProcess = True
                    return {name_of_slot: None}

                #user answer right answer in help
                if(ValidateQuestGameForm.seqProcess):
                    if(value.lower() =="xv"):
                        ValidateQuestGameForm.counter = 2
                        ValidateQuestGameForm.seqProcess = False                
                # Check Reset
                bound = 2
                if(ValidateQuestGameForm.counter == bound):
                    # reset
                    ValidateQuestGameForm.seqProcess = False
                    ValidateQuestGameForm.code = ""
                    ValidateQuestGameForm.counter = 0

                # check if Sequentieller Process
                if(ValidateQuestGameForm.seqProcess):
                    choices = ValidateQuestGameForm.questGameAnswers_db(
                    )[name_of_slot + ValidateQuestGameForm.seq]
                else:
                    choices = ValidateQuestGameForm.questGameAnswers_db()[
                        name_of_slot]
                # check answer
                answer = process.extractOne(value.lower(), choices)
                ValidateQuestGameForm.generalAttemp = ValidateQuestGameForm.generalAttemp + 1
                if answer[1] > 95:
                    if(ValidateQuestGameForm.seqProcess):
                        msg = ValidateQuestGameForm.getKeyValuePairHelpers(
                            helperAnswerChoices, "Answer" + ValidateQuestGameForm.seq)
                        dispatcher.utter_message(text=msg)
                        ValidateQuestGameForm.seqProcess = False
                        return {name_of_slot: None}
                    else:
                        rules = []
                        # First Try without any Help
                        if(ValidateQuestGameForm.generalAttemp == 1) & (ValidateQuestGameForm.lasthelp == ""):
                            rules = ValidateQuestGameForm.questGameLearningstyle_db()[
                                name_of_slot + "1"]
                        # FirstTry & text
                        elif(ValidateQuestGameForm.generalAttemp <= 3) & (ValidateQuestGameForm.lasthelp == "text"):
                            rules = ValidateQuestGameForm.questGameLearningstyle_db()[
                                name_of_slot + "2"]

                        elif(ValidateQuestGameForm.generalAttemp > 3) & (ValidateQuestGameForm.lasthelp == "text"):
                            rules = ValidateQuestGameForm.questGameLearningstyle_db()[
                                name_of_slot + "6"]
                            # Increment LearningStyle
                        for rule in rules:
                            learningstyle = LogicRules[rule]
                            for ls in learningstyle:
                                gameLearningStylePoints[ls] = gameLearningStylePoints[ls] + 1
                        ValidateQuestGameForm.generalAttemp = 0
                        ValidateQuestGameForm.seq = ""
                        ValidateQuestGameForm.code = ""
                        ValidateQuestGameForm.counter = 0
                        msg = ValidateQuestGameForm.getKeyValuePairHelpers(
                            helperAnswerChoices, "Answer")
                        dispatcher.utter_message(text=msg)
                       # print(gameLearningStylePoints)
                        return {name_of_slot: value}
                else:
                    if ValidateQuestGameForm.seqProcess:
                        for item in helperAnswerChoices:
                            for key in item:
                                if key == "Answer" + ValidateQuestGameForm.seq+"F":
                                    msg = item[key]
                                elif key == "Answer" + ValidateQuestGameForm.seq + ValidateQuestGameForm.code:
                                    msg = item[key]
                        ValidateQuestGameForm.code = "FF"
                        ValidateQuestGameForm.counter = ValidateQuestGameForm.counter + 1
                        dispatcher.utter_message(text=msg)
                        return {name_of_slot: None}
                    else:
                        dispatcher.utter_message(text="Sorry that´s wrong 😕. Keep going! 🦾 ")
                        return {name_of_slot: None}
            return validate_process_quests


        else:
            def validate_slot(self, value: Text, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any],) -> Dict[Text, Any]:
                """Validate user input."""
                input = ValidateQuestGameForm.get_previous_slot_value_from_tracker(
                    tracker, name_of_slot)
                # print("function",input)
                value = ValidateQuestGameForm.clean_up_user_input(value)
                # get Object vom Database
                helper = ["textHelp", "imageHelp", "movieHelp",
                          "exampleHelp", "translatorHelp"]
                helperAnswerChoices = []
                helperAnswerChoices = ValidateQuestGameForm.qGHelpAndAnswers_db()[
                    name_of_slot]
                helperText = ValidateQuestGameForm.getKeyValuePairHelpers(
                    helperAnswerChoices, value)
                # user selected solution
                if(value[4:] == "solution"):
                    ValidateQuestGameForm.seqProcess = False
                    ValidateQuestGameForm.lasthelp = ""
                    ValidateQuestGameForm.generalAttemp = 0
                    dispatcher.utter_message(text=helperText)
                    return {name_of_slot: "solution"}
                # user selected any help
                for help in helper:
                    if value[4:] == help:
                        if(help == "translatorHelp"):
                            ValidateQuestGameForm.lasthelp = "textHelp"
                        else:
                            ValidateQuestGameForm.lasthelp = help
                        dispatcher.utter_message(text=helperText)
                        return {name_of_slot: None}
                # Answerchoices
                
                choices = ValidateQuestGameForm.questGameAnswers_db()[
                    name_of_slot]
                answer = process.extractOne(value.lower(), choices)
                ValidateQuestGameForm.generalAttemp = ValidateQuestGameForm.generalAttemp + 1
               # print("Value", value, "answer", answer, "choices", choices)
                if answer[1] > 95:
                    #print(answer[0], answer[1])
                    rules = []
                    # First Try without any Help
                    if(ValidateQuestGameForm.generalAttemp == 1) & (ValidateQuestGameForm.lasthelp == ""):
                        rules = ValidateQuestGameForm.questGameLearningstyle_db()[
                            name_of_slot + "1"]
                    # FirstTry & text
                    elif(ValidateQuestGameForm.generalAttemp <= 2) & (ValidateQuestGameForm.lasthelp == "textHelp"):
                        rules = ValidateQuestGameForm.questGameLearningstyle_db()[
                            name_of_slot + "2"]
                        # FirstTry img
                    elif(ValidateQuestGameForm.generalAttemp <= 2) & (ValidateQuestGameForm.lasthelp == "imageHelp"):
                        rules = ValidateQuestGameForm.questGameLearningstyle_db()[
                            name_of_slot + "3"]
                    # FirstTry & movie
                    elif(ValidateQuestGameForm.generalAttemp <= 2) & (ValidateQuestGameForm.lasthelp == "movieHelp"):
                        rules = ValidateQuestGameForm.questGameLearningstyle_db()[
                            name_of_slot + "4"]
                        # FirstTry example
                    elif(ValidateQuestGameForm.generalAttemp <= 2) & (ValidateQuestGameForm.lasthelp == "exampleHelp"):
                        rules = ValidateQuestGameForm.questGameLearningstyle_db()[
                            name_of_slot + "5"]
                        # text > first try
                    elif(ValidateQuestGameForm.generalAttemp > 2) & (ValidateQuestGameForm.lasthelp == "textHelp"):
                        rules = ValidateQuestGameForm.questGameLearningstyle_db()[
                            name_of_slot + "6"]
                        # image > first try
                    elif(ValidateQuestGameForm.generalAttemp > 2) & (ValidateQuestGameForm.lasthelp == "imageHelp"):
                        rules = ValidateQuestGameForm.questGameLearningstyle_db()[
                            name_of_slot + "7"]
                        # movie > first try
                    elif(ValidateQuestGameForm.generalAttemp > 2) & (ValidateQuestGameForm.lasthelp == "movieHelp"):
                        rules = ValidateQuestGameForm.questGameLearningstyle_db()[
                            name_of_slot + "8"]
                        # example > first try
                    elif(ValidateQuestGameForm.generalAttemp > 2) & (ValidateQuestGameForm.lasthelp == "exampleHelp"):
                        rules = ValidateQuestGameForm.questGameLearningstyle_db()[
                            name_of_slot + "9"]
                        # mehrer Versuche ohne Hilfe
                    elif(ValidateQuestGameForm.generalAttemp > 1) & (ValidateQuestGameForm.lasthelp == ""):
                        rules = ValidateQuestGameForm.questGameLearningstyle_db()[
                            name_of_slot + "10"]

                    # Increment LearningStyle
                    for rule in rules:
                        learningstyle = LogicRules[rule]

                        for ls in learningstyle:
                            gameLearningStylePoints[ls] = gameLearningStylePoints[ls] + 1
                    # smallmistkae
                    if(ValidateQuestGameForm.splitpoint):
                        gameLearningStylePoints["intuitor"] = gameLearningStylePoints["intuitor"] + 1
                    # Reset
                    ValidateQuestGameForm.splitpoint = False
                    ValidateQuestGameForm.lasthelp = ""
                    ValidateQuestGameForm.generalAttemp = 0
                    msg = ValidateQuestGameForm.getKeyValuePairHelpers(
                        helperAnswerChoices, "Answer")
                    dispatcher.utter_message(text=msg)
                    #print(gameLearningStylePoints)
                    return {name_of_slot: value}
                else:
                    # Teilpunkte
                    if(name_of_slot == "306_qG6") | (name_of_slot == "202_qG2"):
                        ValidateQuestGameForm.splitpoints(
                            name_of_slot, choices, value, dispatcher)
                    else:
                        dispatcher.utter_message(text="Sorry that´s wrong 😕. Keep going! 🦾 ")
                    return {name_of_slot: None}
            return validate_slot

    # Quests
    validate_200_qG0 = create_validation_function(name_of_slot="200_qG0")
    validate_201_qG1 = create_validation_function(name_of_slot="201_qG1")
    validate_208_qG8 = create_validation_function(name_of_slot="208_qG8")
    validate_209_qG9 = create_validation_function(name_of_slot="209_qG9")
##########################################################################################
    # PART TWO
##########################################################################################

    class ValidateQuestGameFormPartTwo(FormValidationAction):
        def name(self) -> Text:
            return "validate_quest_game_form_part_two"
        def create_validation_function_part_two(name_of_slot):
            if(name_of_slot == "305_qG5") | (name_of_slot == "208_qG8"):
            # processquests
                def validate_process_quests(self, value: Text, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any],) -> Dict[Text, Any]:
                    value = ValidateQuestGameForm.clean_up_user_input(value)
                    helperAnswerChoices = []
                    helperAnswerChoices = ValidateQuestGameForm.qGHelpAndAnswers_db()[
                        name_of_slot]
                    helperText = ValidateQuestGameForm.getKeyValuePairHelpers(
                        helperAnswerChoices, value)
                    # user selected solution
                    if(value[4:] == "solution"):
                        ValidateQuestGameForm.seqProcess = False
                        ValidateQuestGameForm.lasthelp = ""
                        ValidateQuestGameForm.generalAttemp = 0
                        dispatcher.utter_message(text=helperText)
                        return {name_of_slot: "solution"}

                    # user selected HelpText
                    if value[4:] == "textHelp":
                        dispatcher.utter_message(text=helperText)
                        ValidateQuestGameForm.lasthelp = "text"
                        ValidateQuestGameForm.seq = "seq"
                        ValidateQuestGameForm.seqProcess = True
                        return {name_of_slot: None}
                    #user answer right answer in help
                    if(ValidateQuestGameForm.seqProcess):
                        if(value.lower() == "twenty-seven"):
                            ValidateQuestGameForm.counter = 2
                            ValidateQuestGameForm.seqProcess = False
                    # Check Reset
                    bound = 0
                    if(name_of_slot == "305_qG5"):
                        bound = 2
                    elif(name_of_slot == "208_qG8"):
                        bound = 1
                    if(ValidateQuestGameForm.counter == bound):
                        # reset
                        ValidateQuestGameForm.seqProcess = False
                        ValidateQuestGameForm.code = ""
                        ValidateQuestGameForm.counter = 0

                    # check if Sequentieller Process
                    if(ValidateQuestGameForm.seqProcess):
                        choices = ValidateQuestGameForm.questGameAnswers_db(
                        )[name_of_slot + ValidateQuestGameForm.seq]
                    else:
                        choices = ValidateQuestGameForm.questGameAnswers_db()[
                            name_of_slot]
                    # check answer
                    answer = process.extractOne(value.lower(), choices)
                    ValidateQuestGameForm.generalAttemp = ValidateQuestGameForm.generalAttemp + 1
                    if answer[1] > 95:
                        #print(answer[0], answer[1])
                        if(ValidateQuestGameForm.seqProcess):
                            msg = ValidateQuestGameForm.getKeyValuePairHelpers(
                                helperAnswerChoices, "Answer" + ValidateQuestGameForm.seq)
                            dispatcher.utter_message(text=msg)
                            ValidateQuestGameForm.seqProcess = False
                            return {name_of_slot: None}
                        else:
                            rules = []
                            # First Try without any Help
                            if(ValidateQuestGameForm.generalAttemp == 1) & (ValidateQuestGameForm.lasthelp == ""):
                                rules = ValidateQuestGameForm.questGameLearningstyle_db()[
                                    name_of_slot + "1"]
                            # FirstTry & text
                            elif(ValidateQuestGameForm.generalAttemp <= 3) & (ValidateQuestGameForm.lasthelp == "text"):
                                rules = ValidateQuestGameForm.questGameLearningstyle_db()[
                                    name_of_slot + "2"]

                            elif(ValidateQuestGameForm.generalAttemp > 3) & (ValidateQuestGameForm.lasthelp == "text"):
                                rules = ValidateQuestGameForm.questGameLearningstyle_db()[
                                    name_of_slot + "6"]
                                # Increment LearningStyle
                            for rule in rules:
                                learningstyle = LogicRules[rule]
                                for ls in learningstyle:
                                    gameLearningStylePoints[ls] = gameLearningStylePoints[ls] + 1
                            ValidateQuestGameForm.generalAttemp = 0
                            ValidateQuestGameForm.seq = ""
                            ValidateQuestGameForm.code = ""
                            ValidateQuestGameForm.counter = 0
                            msg = ValidateQuestGameForm.getKeyValuePairHelpers(
                                helperAnswerChoices, "Answer")
                            dispatcher.utter_message(text=msg)
                            return {name_of_slot: value}
                    else:
                        if ValidateQuestGameForm.seqProcess:
                            for item in helperAnswerChoices:
                                for key in item:
                                    if key == "Answer" + ValidateQuestGameForm.seq+"F":
                                        msg = item[key]
                                    elif key == "Answer" + ValidateQuestGameForm.seq + ValidateQuestGameForm.code:
                                        msg = item[key]
                            ValidateQuestGameForm.code = "FF"
                            ValidateQuestGameForm.counter = ValidateQuestGameForm.counter + 1
                            dispatcher.utter_message(text=msg)
                            #print(gameLearningStylePoints)
                            return {name_of_slot: None}
                        else:
                            dispatcher.utter_message(text="Sorry that´s wrong 😕. Keep going! 🦾 ")
                            return {name_of_slot: None}
                return validate_process_quests
            else:
                def validate_slot(self, value: Text, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any],) -> Dict[Text, Any]:
                    """Validate user input."""
                    input = ValidateQuestGameForm.get_previous_slot_value_from_tracker(
                        tracker, name_of_slot)
                    # print("function",input)
                    value = ValidateQuestGameForm.clean_up_user_input(value)
                    # get Object vom Database
                    helper = ["textHelp", "imageHelp", "movieHelp",
                            "exampleHelp", "translatorHelp"]
                    helperAnswerChoices = []
                    helperAnswerChoices = ValidateQuestGameForm.qGHelpAndAnswers_db()[
                        name_of_slot]
                    helperText = ValidateQuestGameForm.getKeyValuePairHelpers(
                        helperAnswerChoices, value)
                    # user selected solution
                    if(value[4:] == "solution"):
                        ValidateQuestGameForm.seqProcess = False
                        ValidateQuestGameForm.lasthelp = ""
                        ValidateQuestGameForm.generalAttemp = 0
                        dispatcher.utter_message(text=helperText)
                        return {name_of_slot: "solution"}
                    # user selected any help
                    for help in helper:
                        if value[4:] == help:
                            if(help == "translatorHelp"):
                                ValidateQuestGameForm.lasthelp = "textHelp"
                            else:
                                ValidateQuestGameForm.lasthelp = help
                            dispatcher.utter_message(text=helperText)
                            return {name_of_slot: None}
                    # Answerchoices
                    choices = ValidateQuestGameForm.questGameAnswers_db()[
                        name_of_slot]
                    answer = process.extractOne(value.lower(), choices)
                    ValidateQuestGameForm.generalAttemp = ValidateQuestGameForm.generalAttemp + 1
                # print("Value", value, "answer", answer, "choices", choices)
                    if answer[1] > 95:
                        #print(answer[0], answer[1])
                        rules = []
                        # First Try without any Help
                        if(ValidateQuestGameForm.generalAttemp == 1) & (ValidateQuestGameForm.lasthelp == ""):
                            rules = ValidateQuestGameForm.questGameLearningstyle_db()[
                                name_of_slot + "1"]
                        # FirstTry & text
                        elif(ValidateQuestGameForm.generalAttemp <= 2) & (ValidateQuestGameForm.lasthelp == "textHelp"):
                            rules = ValidateQuestGameForm.questGameLearningstyle_db()[
                                name_of_slot + "2"]
                            # FirstTry img
                        elif(ValidateQuestGameForm.generalAttemp <= 2) & (ValidateQuestGameForm.lasthelp == "imageHelp"):
                            rules = ValidateQuestGameForm.questGameLearningstyle_db()[
                                name_of_slot + "3"]
                        # FirstTry & movie
                        elif(ValidateQuestGameForm.generalAttemp <= 2) & (ValidateQuestGameForm.lasthelp == "movieHelp"):
                            rules = ValidateQuestGameForm.questGameLearningstyle_db()[
                                name_of_slot + "4"]
                            # FirstTry example
                        elif(ValidateQuestGameForm.generalAttemp <= 2) & (ValidateQuestGameForm.lasthelp == "exampleHelp"):
                            rules = ValidateQuestGameForm.questGameLearningstyle_db()[
                                name_of_slot + "5"]
                            # text > first try
                        elif(ValidateQuestGameForm.generalAttemp > 2) & (ValidateQuestGameForm.lasthelp == "textHelp"):
                            rules = ValidateQuestGameForm.questGameLearningstyle_db()[
                                name_of_slot + "6"]
                            # image > first try
                        elif(ValidateQuestGameForm.generalAttemp > 2) & (ValidateQuestGameForm.lasthelp == "imageHelp"):
                            rules = ValidateQuestGameForm.questGameLearningstyle_db()[
                                name_of_slot + "7"]
                            # movie > first try
                        elif(ValidateQuestGameForm.generalAttemp > 2) & (ValidateQuestGameForm.lasthelp == "movieHelp"):
                            rules = ValidateQuestGameForm.questGameLearningstyle_db()[
                                name_of_slot + "8"]
                            # example > first try
                        elif(ValidateQuestGameForm.generalAttemp > 2) & (ValidateQuestGameForm.lasthelp == "exampleHelp"):
                            rules = ValidateQuestGameForm.questGameLearningstyle_db()[
                                name_of_slot + "9"]
                            # mehrer Versuche ohne Hilfe
                        elif(ValidateQuestGameForm.generalAttemp > 1) & (ValidateQuestGameForm.lasthelp == ""):
                            rules = ValidateQuestGameForm.questGameLearningstyle_db()[
                                name_of_slot + "10"]

                        # Increment LearningStyle
                        for rule in rules:
                            learningstyle = LogicRules[rule]

                            for ls in learningstyle:
                                gameLearningStylePoints[ls] = gameLearningStylePoints[ls] + 1
                        # smallmistkae
                        if(ValidateQuestGameForm.splitpoint):
                            gameLearningStylePoints["intuitor"] = gameLearningStylePoints["intuitor"] + 1
                        # Reset
                        ValidateQuestGameForm.splitpoint = False
                        ValidateQuestGameForm.lasthelp = ""
                        ValidateQuestGameForm.generalAttemp = 0
                        msg = ValidateQuestGameForm.getKeyValuePairHelpers(
                            helperAnswerChoices, "Answer")
                        dispatcher.utter_message(text=msg)
                        #print(gameLearningStylePoints)
                        return {name_of_slot: value}
                    else:
                        # Teilpunkte
                        if(name_of_slot == "306_qG6") | (name_of_slot == "202_qG2"):
                            ValidateQuestGameForm.splitpoints(
                                name_of_slot, choices, value, dispatcher)
                        else:
                            dispatcher.utter_message(text="Sorry that´s wrong 😕. Keep going! 🦾 ")
                        return {name_of_slot: None}
                return validate_slot
        validate_304_qG4 = create_validation_function_part_two(name_of_slot="304_qG4")
        validate_307_qG7 = create_validation_function_part_two(name_of_slot="307_qG7")
        validate_305_qG5 = create_validation_function_part_two(name_of_slot="305_qG5")
        validate_306_qG6 = create_validation_function_part_two(name_of_slot="306_qG6")

##########################################################################################
    # DETECTION_GAME
##########################################################################################


class DetectLearningStyleGame(Action):
    def name(self) -> Text:
        return "action_detect_learning_style_game"

    def run(self, dispatcher, tracker, domain):
        # visual_verbal
        #print(gameLearningStylePoints)
        #print(caughtLearningStyles)
        if gameLearningStylePoints['visual'] > gameLearningStylePoints['verbal']:
            caughtLearningStyles.append("visual")
            # firstLearningStyle = "Visual " + learningStyleRecommendation['visual'] + "\n"
            firstLearningStyle = "Visual" + "\n"

        elif gameLearningStylePoints['visual'] < gameLearningStylePoints['verbal']:
            caughtLearningStyles.append("verbal")
            # firstLearningStyle = "Verbal " + learningStyleRecommendation['verbal']  + "\n"
            firstLearningStyle = "Verbal" + "\n"

        elif gameLearningStylePoints['visual'] == gameLearningStylePoints['verbal']:
            caughtLearningStyles.append("visual")
            caughtLearningStyles.append("verbal")
            # firstLearningStyle = "Neither visual nor verbal. Thus, your learning style is essentially well balanced in this category. \n Visual: " + learningStyleRecommendation['visual'] + "\n " + "Verbal: " + learningStyleRecommendation['verbal'] + "\n"
            firstLearningStyle = "Neither visual nor verbal. Thus, your learning style is essentially well balanced in this category.\n"

          # sensor_intuitor
        if gameLearningStylePoints['sensor'] > gameLearningStylePoints['intuitor']:
            caughtLearningStyles.append("sensor")
            # secondLearningStyle = "Sensor "+ learningStyleRecommendation['sensor']  + "\n"
            secondLearningStyle = "Sensor" + "\n"

        elif gameLearningStylePoints['sensor'] < gameLearningStylePoints['intuitor']:
            caughtLearningStyles.append("intuitor")
            # secondLearningStyle = "Intuitor "+ learningStyleRecommendation['intuitor']  + "\n"
            secondLearningStyle = "Intuitive" + "\n"

        elif gameLearningStylePoints['sensor'] == gameLearningStylePoints['intuitor']:
            caughtLearningStyles.append("sensor")
            caughtLearningStyles.append("intuitor")
            # secondLearningStyle = "Neither sensor nor intuitor. Thus, your learning style is essentially well balanced in this category. \n Sensor: " + learningStyleRecommendation['sensor'] + "\n " + "Intuitor: " + learningStyleRecommendation['intuitor']+ "\n"
            secondLearningStyle = "Neither sensor nor intuitive. Thus, your learning style is essentially well balanced in this category.\n"
          # active_reflective
        if gameLearningStylePoints['active'] > gameLearningStylePoints['reflective']:
            caughtLearningStyles.append("active")
            # thirdLearningStyle = "Active "+ learningStyleRecommendation['active']  + "\n"
            thirdLearningStyle = "Active" + "\n"

        elif gameLearningStylePoints['active'] < gameLearningStylePoints['reflective']:
            caughtLearningStyles.append("reflective")
            # thirdLearningStyle = "Reflective "+ learningStyleRecommendation['reflective']  + "\n"
            thirdLearningStyle = "Reflective" + "\n"

        elif gameLearningStylePoints['active'] == gameLearningStylePoints['reflective']:
            caughtLearningStyles.append("active")
            caughtLearningStyles.append("reflective")
            # thirdLearningStyle = "Neither active nor reflective. Thus, your learning style is essentially well balanced in this category. \n Active: " + learningStyleRecommendation['active'] + "\n " + "Reflective: " + learningStyleRecommendation['reflective']+ "\n"
            thirdLearningStyle = "Neither active nor reflective. Thus, your learning style is essentially well balanced in this category.\n"

            # sequential_global
        if gameLearningStylePoints['sequential'] > gameLearningStylePoints['global']:
            caughtLearningStyles.append("sequential")
            # fourthLearningStyle = "Sequential "+ learningStyleRecommendation['sequential']  + "\n"
            fourthLearningStyle = "Sequential" + "\n"

        elif gameLearningStylePoints['sequential'] < gameLearningStylePoints['global']:
            caughtLearningStyles.append("global")
            # fourthLearningStyle = "Global "+ learningStyleRecommendation['global']  + "\n"
            fourthLearningStyle = "Global" + "\n"

        elif gameLearningStylePoints['sequential'] == gameLearningStylePoints['global']:
            caughtLearningStyles.append("sequential")
            caughtLearningStyles.append("global")
            # fourthLearningStyle = "Neither sequential nor global. Thus, your learning style is essentially well balanced in this category. \n Sequential: " + learningStyleRecommendation['sequential'] + "\n " + "Global: " + learningStyleRecommendation['global']+ "\n"
            fourthLearningStyle = "Neither sequential nor global. Thus, your learning style is essentially well balanced in this category.\n"

        dispatcher.utter_message(
            text=f"After our Quiz-Game I detected following learning styles:\n - {firstLearningStyle} - {secondLearningStyle} - {thirdLearningStyle} - {fourthLearningStyle} \n")

        return []


##########################################################################################
        # COMPARE After Talk
##########################################################################################

class GiveLearningStyleRecommendationTalk(Action): #ILS-DIM1
    def name(self) -> Text:
        return "give_learning_style_recommendation_talk"

    async def run(self, dispatcher, tracker, domain):
        msg = ""
        

        intent = tracker.get_intent_of_latest_message()
        if intent == "affirm":
            global clicked_recommendation
            clicked_recommendation = True
            buttons = []
            buttons.append({"title": 'next' , "payload": '/affirm'})

            if "verbal" in caughtLearningStyles_talk:
                if "visual" in caughtLearningStyles_talk:
                    dispatcher.utter_message(text=learningStyleRecommendation["visual"] + "\n") #der erste wird ausgegeben
            elif "visual" in caughtLearningStyles_talk:
                    dispatcher.utter_message(text=learningStyleRecommendation["visual"] + "\n", buttons = buttons) #der erste wird ausgegeben
            if "verbal" in caughtLearningStyles_talk:
                dispatcher.utter_message(text=learningStyleRecommendation["verbal"] + "\n", buttons = buttons) #der erste wird ausgegeben
        elif intent == "deny":
            dispatcher.utter_message(
                text="Don't worry. Here's a link to read through the descriptions of each learning style later on. 😉 " + "\n" + "https://www.engr.ncsu.edu/wp-content/uploads/drive/1WPAfj3j5o5OuJMiHorJ-lv6fON1C8kCN/styles.pdf")
        return []

##########################################################################################
        #  utter_start_game
##########################################################################################
    class ActionTimerUtterConfirmStartGame(Action):
            def name(self) -> Text:
                return "action_timer_utter_confirm_start_game"

            def run(self, dispatcher, tracker, domain):
                dispatcher.utter_message(response='utter_confirm_start_game')
                return []


class GiveLearningStyleILSDim2(Action):
    def name(self) -> Text:
        return "give_learning_style_ILS_Dim_2"

    def run(self, dispatcher, tracker, domain):
        intent = tracker.get_intent_of_latest_message()
        if intent == "affirm":
            buttons = []
            buttons.append({"title": 'next' , "payload": '/affirm'})
            if "intuitor" in caughtLearningStyles_talk:
                if "sensor" in caughtLearningStyles_talk:
                    dispatcher.utter_message(text=learningStyleRecommendation["sensor"] + "\n") #der erste wird ausgegeben
            elif "sensor" in caughtLearningStyles_talk:
                    dispatcher.utter_message(text=learningStyleRecommendation["sensor"] + "\n", buttons = buttons) #der erste wird ausgegeben
            if "intuitor" in caughtLearningStyles_talk:
                dispatcher.utter_message(text=learningStyleRecommendation["intuitor"] + "\n", buttons = buttons) #der erste wird ausgegeben
        #print(caughtLearningStyles_talk)
        return []


class GiveLearningStyleILSDim3(Action):
    def name(self) -> Text:
        return "give_learning_style_ILS_Dim_3"

    def run(self, dispatcher, tracker, domain):

        buttons = []
        buttons.append({"title": 'next' , "payload": '/affirm'})
        if "reflective" in caughtLearningStyles_talk:
            if "active" in caughtLearningStyles_talk:
                dispatcher.utter_message(text=learningStyleRecommendation["active"] + "\n") #der erste wird ausgegeben
        elif "active" in caughtLearningStyles_talk:
                dispatcher.utter_message(text=learningStyleRecommendation["active"] + "\n", buttons = buttons) #der erste wird ausgegeben
        if "reflective" in caughtLearningStyles_talk:
            dispatcher.utter_message(text=learningStyleRecommendation["reflective"] + "\n", buttons = buttons) #der erste wird ausgegeben
        #print(caughtLearningStyles_talk)

        return []

class GiveLearningStyleILSDim4(Action):
    def name(self) -> Text:
        return "give_learning_style_ILS_Dim_4"

    def run(self, dispatcher, tracker, domain):
        intent = tracker.get_intent_of_latest_message()
        buttons = []
        buttons.append({"title": 'finished reading 📖 ✅' , "payload": '/affirm'})
        if "global" in caughtLearningStyles_talk:
            if "sequential" in caughtLearningStyles_talk:
                dispatcher.utter_message(text=learningStyleRecommendation["sequential"] + "\n") #der erste wird ausgegeben
        elif "sequential" in caughtLearningStyles_talk:
                dispatcher.utter_message(text=learningStyleRecommendation["sequential"] + "\n", buttons = buttons) #der erste wird ausgegeben
        if "global" in caughtLearningStyles_talk:
            dispatcher.utter_message(text=learningStyleRecommendation["global"] + "\n", buttons = buttons) #der erste wird ausgegeben
       # print(caughtLearningStyles_talk)

        return []



##########################################################################################
        # COMPARE After Game
##########################################################################################


class GiveLearningStyleRecommendationGame(Action):
    def name(self) -> Text:
        return "give_learning_style_recommendation_game"

    @staticmethod
    def getDifference(caughtLearningStyles_talk, caughtLearningStyles,):
        return list(set(caughtLearningStyles_talk) - set(caughtLearningStyles))

    def run(self, dispatcher, tracker, domain):
        msg = ""
        intent = tracker.get_intent_of_latest_message()
        if intent == "affirm":

                buttons = []
                buttons.append({"title": 'next' , "payload": '/affirm'})
                if "verbal" in caughtLearningStyles:
                    if "visual" in caughtLearningStyles:
                        dispatcher.utter_message(text=learningStyleRecommendation["visual"] + "\n") #der erste wird ausgegeben
                elif "visual" in caughtLearningStyles:
                        dispatcher.utter_message(text=learningStyleRecommendation["visual"] + "\n", buttons = buttons) #der erste wird ausgegeben
                if "verbal" in caughtLearningStyles:
                    dispatcher.utter_message(text=learningStyleRecommendation["verbal"] + "\n", buttons = buttons) #der erste wird ausgegeben
            
        elif intent == "deny":
            msg = "Thanks for your company. I will give you a link: https://www.engr.ncsu.edu/wp-content/uploads/drive/1WPAfj3j5o5OuJMiHorJ-lv6fON1C8kCN/styles.pdf where you can read the explanation of different learning styles at a later time." + "\n"
            dispatcher.utter_message(text=msg + "See you next time! Bye!")
        return []

class GiveLearningStyleGameILSDim2(Action):
    def name(self) -> Text:
        return "give_learning_style_game_ILS_Dim_2"

    def run(self, dispatcher, tracker, domain):

        buttons = []
        buttons.append({"title": 'next' , "payload": '/affirm'})

        if "intuitor" in caughtLearningStyles:
            if "sensor" in caughtLearningStyles:
                dispatcher.utter_message(text=learningStyleRecommendation["sensor"] + "\n") #der erste wird ausgegeben
        elif "sensor" in caughtLearningStyles:
                dispatcher.utter_message(text=learningStyleRecommendation["sensor"] + "\n", buttons = buttons) #der erste wird ausgegeben
        if "intuitor" in caughtLearningStyles:
            dispatcher.utter_message(text=learningStyleRecommendation["intuitor"] + "\n", buttons = buttons) #der erste wird ausgegeben
        #print(caughtLearningStyles)

        return []

class GiveLearningStyleGameILSDim3(Action):
    def name(self) -> Text:
        return "give_learning_style_game_ILS_Dim_3"

    def run(self, dispatcher, tracker, domain):

        buttons = []
        buttons.append({"title": 'next' , "payload": '/affirm'})
        if "reflective" in caughtLearningStyles:
            if "active" in caughtLearningStyles:
                dispatcher.utter_message(text=learningStyleRecommendation["active"] + "\n") #der erste wird ausgegeben
        elif "active" in caughtLearningStyles:
                dispatcher.utter_message(text=learningStyleRecommendation["active"] + "\n", buttons = buttons) #der erste wird ausgegeben
        if "reflective" in caughtLearningStyles:
            dispatcher.utter_message(text=learningStyleRecommendation["reflective"] + "\n", buttons = buttons) #der erste wird ausgegeben
       # print(caughtLearningStyles)

        return []

class GiveLearningStyleGameILSDim3(Action):
    def name(self) -> Text:
        return "give_learning_style_game_ILS_Dim_4"

    def run(self, dispatcher, tracker, domain):
        buttons = []
        buttons.append({"title": 'finished reading 📖 ✅' , "payload": '/affirm'})
        if "global" in caughtLearningStyles:
            if "sequential" in caughtLearningStyles:
                dispatcher.utter_message(text=learningStyleRecommendation["sequential"] + "\n") #der erste wird ausgegeben
        elif "sequential" in caughtLearningStyles:
                dispatcher.utter_message(text=learningStyleRecommendation["sequential"] + "\n", buttons = buttons) #der erste wird ausgegeben
        if "global" in caughtLearningStyles:
            dispatcher.utter_message(text=learningStyleRecommendation["global"] + "\n", buttons = buttons) #der erste wird ausgegeben
       # print(caughtLearningStyles)

        return []

##########################################################################################
        # utter_bye_game
##########################################################################################
    class ActionTimerUtterByeGame(Action):
            def name(self) -> Text:
                return "action_timer_utter_bye_game"

            def run(self, dispatcher, tracker, domain):
                dispatcher.utter_message(response='utter_bye_game')
                caughtLearningStyles.clear()
                caughtLearningStyles_talk.clear()
                gameLearningStylePoints.update({}.fromkeys(gameLearningStylePoints,0))
                dialogLearningStyles.update({}.fromkeys(dialogLearningStyles,0))
                return []