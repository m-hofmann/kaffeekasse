import logging
import sys

from PyQt5.QtCore import Qt, QPropertyAnimation, QRect, QEasingCurve, \
    QParallelAnimationGroup, QObject, pyqtSignal
from PyQt5.QtWidgets import QApplication, QLabel, QFrame, QWidget, QGridLayout, QPushButton, QStackedLayout

from kaffeekasse.controller import StateChangedEvent, StateType, CoffeeFundController, InputEvent, InputAction
from kaffeekasse.utils.auto_enum import AutoNumber

logger = logging.getLogger(__name__)


ANIMATION_DURATION = 250


class GuiCards(AutoNumber):
    """
    List of all card views that are available in the application.
    """
    Start = ()
    ChooseAction = ()
    AccountInfo = ()
    RemoveCard = ()


class UiContext:
    def __init__(self):
        self.user_name = "Undefined User"  # type: str


class StartCard(QFrame):
    def __init__(self):
        super().__init__()
        card_label = QLabel("Bitte Karte auflegen")
        card_label.setObjectName("h1")
        card_label.setWordWrap(True)

        frame_card_layout = QGridLayout()
        frame_card_layout.addWidget(card_label, 0, 0, Qt.AlignCenter | Qt.AlignHCenter)
        self.setLayout(frame_card_layout)


class ChooseActionCard(QFrame):
    def __init__(self):
        super().__init__()
        self.choose_label = QLabel()
        self.choose_label.setObjectName("h2")
        self.choose_label.setWordWrap(True)

        self.button_account = QPushButton("Benutzerkonto")
        self.button_coffee = QPushButton("Kaffee")

        layout = QGridLayout()
        layout.addWidget(self.choose_label, 0, 0, 1, 2, Qt.AlignHCenter)
        layout.addWidget(self.button_account, 1, 0)
        layout.addWidget(self.button_coffee, 1, 1)

        self.setLayout(layout)
        self.set_user_name("User Name not set")

    def set_user_name(self, name: str):
        self.choose_label.setText("Hallo {0}, möchten Sie ihr Benutzerkonto überprüfen oder Kaffee kaufen?"
                                  .format(name))


class AccountCard(QFrame):
    def __init__(self):
        super().__init__()
        self.header_label = QLabel("Benutzerkonto für <User Name>")
        self.header_label.setObjectName("h2")
        self.header_label.setWordWrap(True)

        balance_text_label = QLabel("Kontostand")
        self.balance_value_label = QLabel("<kein Wert>")

        self.button_back = QPushButton("Zurück")

        layout = QGridLayout()
        layout.addWidget(self.header_label, 0, 0, 1, 3, Qt.AlignHCenter)
        layout.addWidget(balance_text_label, 1, 0)
        layout.addWidget(self.balance_value_label, 1, 1)
        layout.addWidget(self.button_back, 2, 2)

        self.setLayout(layout)

    def set_user_name(self, name: str):
        self.header_label.setText("Benutzerkonto für {0}"
                                  .format(name))

    def set_balance(self, value):
        self.balance_value_label.setText("{0} €".format(value/100))


class RemoveCard(QFrame):
    def __init__(self):
        super().__init__()
        header_label = QLabel("Danke! Bitte Karte entfernen.")
        header_label.setObjectName("h1")

        layout = QGridLayout()
        layout.addWidget(header_label, 0, 0, 1, 1, Qt.AlignHCenter)

        self.setLayout(layout)


class CoffeeFundWindow(QWidget):
    signal_back = pyqtSignal()
    signal_coffee = pyqtSignal()
    signal_account = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__()

        self.cards = {}  # type: Dict[GuiCards, QWidget]
        """
            Python's GC will clean up QPropertyAnimations as soon as it leaves the button handler,
             therefore they will appear not to work. Use members to store the animations.
            see http://stackoverflow.com/a/6953965
        """
        self.slide_in_animation = None
        self.slide_out_animation = None
        self.animation_group = None
        self.setObjectName("coffeeFundWindow")

        """
            Store the position and size of visible/hidden cards for the animation sequences
        """
        self.hidden_geometry = None
        self.visible_geometry = None

        layout = QStackedLayout()
        layout.setStackingMode(QStackedLayout.StackAll)

        card_remove = RemoveCard()
        self.cards[GuiCards.RemoveCard] = card_remove
        layout.addWidget(card_remove)

        card_choose_action = ChooseActionCard()
        self.cards[GuiCards.ChooseAction] = card_choose_action
        layout.addWidget(card_choose_action)

        card_account = AccountCard()
        self.cards[GuiCards.AccountInfo] = card_account
        layout.addWidget(card_account)

        # keep this as last initialized card, the last card will be shown on startup!
        card_start = StartCard()
        self.cards[GuiCards.Start] = card_start
        layout.addWidget(card_start)

        self.setLayout(layout)
        self.setWindowTitle("Kaffeekasse")

        layout.setCurrentWidget(card_start)
        self.active_card = None

        card_choose_action.button_account.clicked.connect(self.signal_account)
        card_choose_action.button_coffee.clicked.connect(self.signal_coffee)
        card_account.button_back.clicked.connect(self.signal_back)

    def set_card_hidden(self, card: QWidget):
        card.setGeometry(self.hidden_geometry)

    def show_start(self):
        self.show_card(GuiCards.Start)

    def show_account(self, name, value):
        self.cards[GuiCards.AccountInfo].set_user_name(name)
        self.cards[GuiCards.AccountInfo].set_balance(value)
        self.show_card(GuiCards.AccountInfo)

    def show_choose_action(self, name: str):
        self.cards[GuiCards.ChooseAction].set_user_name(name)
        self.show_card(GuiCards.ChooseAction)

    def show_remove(self):
        self.show_card(GuiCards.RemoveCard)

    def show_card(self, card_id: GuiCards):
        if self.active_card is None:
            self.active_card = self.cards[GuiCards.Start]

        if self.active_card == self.cards[card_id]:
            return

        if self.visible_geometry is None or self.hidden_geometry is None:
            self.visible_geometry = self.active_card.geometry()  # type: QRect
            self.hidden_geometry = QRect(self.visible_geometry.x(), self.visible_geometry.height() * 1.5,
                                         self.visible_geometry.width(), self.visible_geometry.height())
        for key in self.cards.keys():
            if key != self.active_card:
                self.set_card_hidden(self.cards[key])

        card_to_show = self.cards[card_id]
        self.start_card_switch(card_to_show)
        self.active_card = self.cards[card_id]
        self.layout().setCurrentWidget(self.active_card)

    def start_card_switch(self, card_to_show):
        self.slide_out_animation = QPropertyAnimation(self.active_card, "geometry")
        self.slide_out_animation.setDuration(ANIMATION_DURATION)
        self.slide_out_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.slide_out_animation.setStartValue(self.visible_geometry)
        self.slide_out_animation.setEndValue(self.hidden_geometry)
        self.set_card_hidden(card_to_show)
        self.slide_in_animation = QPropertyAnimation(card_to_show, "geometry")
        self.slide_in_animation.setDuration(ANIMATION_DURATION)
        self.slide_in_animation.setEasingCurve(QEasingCurve.InCubic)
        self.slide_in_animation.setStartValue(self.hidden_geometry)
        self.slide_in_animation.setEndValue(self.visible_geometry)
        self.animation_group = QParallelAnimationGroup()
        self.animation_group.addAnimation(self.slide_out_animation)
        self.animation_group.addAnimation(self.slide_in_animation)
        self.animation_group.start()


class QtGuiController(QObject):
    """
    Starts the Qt GUI and glues the program's events to the interface.
    """
    show_start = pyqtSignal()
    show_choose = pyqtSignal(str)
    show_account = pyqtSignal(str, int)
    show_remove = pyqtSignal()

    def __init__(self, controller: CoffeeFundController):
        super().__init__()
        self.app = QApplication(sys.argv)
        self.app.setOverrideCursor(Qt.BlankCursor)
        self.set_styles()
        self.main_window = CoffeeFundWindow()
        self.controller = controller

        # signals and slots setup
        self.show_start.connect(self.main_window.show_start)
        self.show_choose.connect(self.main_window.show_choose_action)
        self.show_account.connect(self.main_window.show_account)
        self.show_remove.connect(self.main_window.show_remove)

        self.main_window.signal_back.connect(self.relay_gui_back)
        self.main_window.signal_coffee.connect(self.relay_gui_coffee)
        self.main_window.signal_account.connect(self.relay_gui_account)

    def run(self):
        # hide the cursor - this is a touch app
        self.main_window.showFullScreen()
        self.show_start.emit()
        sys.exit(self.app.exec_())

    def set_styles(self):
        with open("styles/gui_style.qss") as style_file:
            style = style_file.read()
            self.app.setStyleSheet(style)
            logger.debug("set stylesheet")

    def relay_gui_account(self):
        event = InputEvent(InputAction.account_info)
        self.gui_to_controller_event(event)

    def relay_gui_back(self):
        event = InputEvent(InputAction.back)
        self.gui_to_controller_event(event)

    def relay_gui_coffee(self):
        event = InputEvent(InputAction.coffee)
        self.gui_to_controller_event(event)

    def gui_to_controller_event(self, event):
        self.controller.enqueue_event(event)

    def apply_state_change(self, event: StateChangedEvent):
        if event.state == StateType.wait_for_card:
            print("Showing card Start for wait for card state")
            self.show_start.emit()
        elif event.state == StateType.choose_info_or_coffee:
            print("Showing card ChooseAction for choose_info_or_coffee for user {0}".format(event.context.current_user.name))
            self.show_choose.emit(event.context.current_user.name)
        elif event.state == StateType.remove_card:
            print("Showing card RemoveCard")
            self.show_remove.emit()
        elif event.state == StateType.show_account:
            print("Showing card ShowAccount")
            self.show_account.emit(event.context.current_user.name,
                                   event.context.current_user.balance_as_eur_cents)
        else:
            logger.debug("Unknown state internal {0}".format(event))
