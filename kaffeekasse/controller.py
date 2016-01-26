import logging
import queue

from kaffeekasse.nfcmonitor import NfcEvent
from kaffeekasse.database import Session
from kaffeekasse.model import User, IdentificationToken
from kaffeekasse.utils.auto_enum import AutoNumber
from kaffeekasse.utils.observer import Event, Observable

logger = logging.getLogger(__name__)


class Context:
    def __init__(self):
        self.current_user = None  # type: User


class StateChangedEvent(Event):
    def __init__(self, new_state, context):
        self.state = new_state
        self.context = context


class InputAction(AutoNumber):
    back = ()
    account_info = ()
    coffee = ()


class InputEvent(Event):
    def __init__(self, event_type: InputAction):
        self.event_type = event_type  # type: InputAction


class State:
    def __init__(self):
        pass

    def enter(self, context: Context):
        pass

    def exit(self, context: Context):
        pass

    def handle_event(self, context: Context, event: Event):
        pass


class StateType:
    wait_for_card = None
    show_account = None
    choose_info_or_coffee = None
    remove_card = None


class WaitForCardState(State):
    def handle_event(self, context: Context, event: NfcEvent):
        if isinstance(event, NfcEvent) and not event.invalid:
            uid = event.uid
            try:
                db_session = Session()
                user, token = db_session.query(User, IdentificationToken).join(IdentificationToken) \
                    .filter(IdentificationToken.id == uid).first()
                context.current_user = user
                return StateType.choose_info_or_coffee
            except:
                logger.warn("No user for NFC token ID {0}".format(uid))
        return StateType.wait_for_card

    def __repr__(self):
        return "WaitForCardState"


class ChooseInfoOrCoffee(State):
    def handle_event(self, context: Context, event: InputEvent):
        if isinstance(event, InputEvent):
            if event.event_type == InputAction.account_info:
                return StateType.show_account
            elif event.event_type == InputAction.coffee:
                context.current_user.balance_as_eur_cents -= 15
                return StateType.remove_card
        elif isinstance(event, NfcEvent) and event.invalid:
            return StateType.wait_for_card
        return StateType.choose_info_or_coffee

    def __repr__(self):
        return "ChooseInfoOrCoffeeState"


class ShowAccount(State):
    def handle_event(self, context: Context, event: Event):
        if isinstance(event, InputEvent):
            if event.event_type == InputAction.back:
                return StateType.choose_info_or_coffee
        elif isinstance(event, NfcEvent):
            if event.invalid:
                return StateType.wait_for_card
        return StateType.show_account

    def __repr__(self):
        return "ShowAccountState"


class RemoveCard(State):
    def handle_event(self, context: Context, event: NfcEvent):
        if isinstance(event, NfcEvent) and event.invalid:
            context.current_user = None
            return StateType.wait_for_card
        return StateType.remove_card

    def __repr__(self):
        return "RemoveCardState"


class StateMachine(Observable):
    def __init__(self):
        super().__init__()
        self.context = Context()
        self.bootstrap_state_instances()
        self.state = None
        self.set_new_state(StateType.wait_for_card)

    def bootstrap_state_instances(self):
        StateType.wait_for_card = WaitForCardState()
        StateType.choose_info_or_coffee = ChooseInfoOrCoffee()
        StateType.remove_card = RemoveCard()
        StateType.show_account = ShowAccount()

    def handle(self, event: Event):
        new_state = self.state.handle_event(self.context, event)

        if new_state is None:
            raise Exception("State {0} returned None as new state!".format(self.state))

        self.set_new_state(new_state)

    def set_new_state(self, new_state):
        if new_state != self.state:
            self.notify_all(StateChangedEvent(new_state, self.context))
            if self.state is not None:
                self.state.exit(self.context)
            self.state = new_state
            self.state.enter(self.context)


class CoffeeFundController(Observable):
    def __init__(self):
        super().__init__()
        self.state_machine = StateMachine()
        self.state_machine.register(self.dispatch_state_change)
        self.event_queue = queue.Queue()  # type: queue.Queue

    def enqueue_event(self, event: Event):
        self.event_queue.put(event)

    def run_event_loop(self):
        while True:
            event = self.event_queue.get()
            self.state_machine.handle(event)

    def gui_set_state(self, state: StateType):
        self.state_machine.set_new_state(state)

    def dispatch_state_change(self, event: StateChangedEvent):
        """
        Forward an internal state change from the state machine to the outside (i.e. GUI)
        :param event: a state changed event with the new state
        :return:
        """
        self.notify_all(event)
