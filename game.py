from abc import ABC, abstractmethod
from typing import List, Optional

import pandas as pd
from IPython.display import HTML, DisplayHandle, display

from playingcards import DefaultCardComparer, BlackjackCardComparer
from participants import BlackjackPlayer, Dealer
from cards import Shoe
class Game(ABC):
  def __init__(self, players:List[BlackjackPlayer], dealer:Optional[Dealer] = None, comparer = DefaultCardComparer):
    self.pool = 0
    self.round = 0

    self._game = 0

    self._players = players
    self._dealer = dealer

    self._all_players = [dealer] + players

    self._all_hands = pd.DataFrame(self.get_names(), index = None, columns = ["Names"])

    self._scoreboard = pd.DataFrame(self.get_names(), index = None, columns = ["Names"])

    self.deck = None
    self.round:int
    self.pool:int
    self._handle = display(DisplayHandle(), display_id=True)

###### Getters #######
  def get_scores(self) -> pd.Series:
    return pd.Series([player.score for player in self._all_players], name = "Scores")

  def get_chips(self) -> pd.Series:
    return pd.Series([player.chips for player in self._all_players], name = "Chips")

  def get_names(self) -> pd.Series:
    return pd.Series([player.name for player in self._all_players], name = "Names")

  def get_hands(self) -> pd.Series:
    return pd.Series([p.get_hand() for p in self._all_players], name = "Hands")

  def get_actives(self) -> pd.Series:
    return pd.Series([not p.is_done() for p in self._all_players], name = "Active")

  def get_active_players(self) -> List[BlackjackPlayer]:
    return [p for p in self._players if not p.is_done()]

###### Output ########

  def _update_scoreboard(self):
    self._scoreboard["Scores"] = self.get_scores()
    self._scoreboard["Hands"] = self.get_hands()
    self._scoreboard["Chips"] = self.get_chips()
    self._scoreboard["Active"] = self.get_actives()
    self._handle.update(HTML(self._scoreboard.to_html(escape=False)))

  def display_scoreboard(self, player = None):
    if not player:
      self._update_scoreboard()
      print()
    else:
      try:
        print()
        print()
        player.display()
        print()
        print()
      except:
        print("Player not found")

######## Game Functions ###########

  def _prompt_bet(self, player):
      """
      Loop until we get a valid integer within the player’s stack.
      """
      while True:
          raw = input(f"{player.name}: (chips: {player.chips}), enter bet ≥ 1:\n")
          try:
              bet = int(raw)
          except ValueError:
              print("Error:  Please enter a whole number.")
              continue

          if bet < 1:
              print(f"Error: Minimum bet is $1.")
          elif bet > player.chips:
              print(f"Error:  You only have {player.chips} chips.")
          else:
              return player.bet(bet)

  def take_bets(self):
    for player in self._players:
      bet = self._prompt_bet(player)
      self.pool += bet

    self.pool += self.dealer.bet(self.pool)

  def play_round(self):
    self._game += 1
    self.before_round()
    print("Placing Bets...")
    print("-----------------")
    self.take_bets()
    print("-----------------\n")

    self.deal_opening()
    self.loop_turns()
    print("Payout....")
    self.settle()

    self.after_round()
    print("-----------------\n")
  @abstractmethod
  def _hit(self, player): ...
  @abstractmethod
  def _stand(self, player): ...
  @abstractmethod
  def before_round(self): ...
  @abstractmethod
  def deal_opening(self): ...
  @abstractmethod
  def loop_turns(self): ...
  @abstractmethod
  def settle(self): ...
  @abstractmethod
  def after_round(self): ...
########## Player Functions ############

  def next(self, player):
    if player.has_strategy():
      print(f"{player.name}, Your Current Score is {player.score}.")
      player.strategy.decide(player, self)
    else:
      action = input(f"{player.name}, Your Current Score is {player.score}.\nPress 'y' to 'hit', or press any other key to 'stand': \n")
      if action.lower() == 'y':
        card = self._hit(player)

        print(f"{player.name}: Current Score = {player.score}")

      else:
        self._stand(player)

class Blackjack(Game):
  def __init__(self, players:List[BlackjackPlayer]):
    self.dealer = Dealer()
    self._dealer_stand = 17


    super().__init__(players, self.dealer, BlackjackCardComparer)

  def _hit(self, player, verbose = True):
    card = self.deck.draw()
    player.hit(card)

    if verbose:
      print(f"{player.name} drew {str(card)}")

    return card

  def _stand(self, player):
    print(f"{player.name} with score {player.score} has decided to stand, skipping...")
    player.stand()


  def compare(self, player_hand):
    if player_hand > self.dealer.hand:
      return "win"
    elif player_hand < self.dealer.hand:
      return "lose"
    else:
      return "push"

  def get_pending(self):
    return [p for p in self._players if p.is_waiting()]

  def display_cards_drawn(self):
    hands = [p.get_hand() for p in self._all_participants]
    self._all_hands[f"Round {self._game}"] = pd.Series(hands, name = "Hands")
    display(HTML(self._all_hands.T.to_html(escape=False)))

  def _payout(self, player, outcome):
    bet = player.current_bet

    if outcome == "blackjack":
      winnings = bet*3
      out_message = f"{player.name}:\nOutcome: {outcome.capitalize()}! \nWon:{winnings - bet}"

    elif outcome == "win":
      winnings = bet*2
      out_message = f"{player.name}:\nOutcome: Winner\nWon:{winnings - bet}"

    elif outcome == "push":
      out_message = f"{player.name}:\nOutcome: Tied\nBroke Even"
      winnings = bet

    else:
      out_message = f"{player.name}:\nOutcome: Loser\nLost:{bet}"
      winnings = 0
      pass

    player.settle(winnings)
    self.pool -= winnings
    print(out_message)
    return winnings

  def before_round(self):
    if not self.deck:
        self.deck = Shoe()

    self.pot = 0
    self.round = 0

  def deal_opening(self):
    print("Dealing First Two Cards....")
    print("-----------------")
    for _ in range(2):
      self.round += 1
      for p in self._all_players:
          self._hit(p)

    print("-----------------\n")
    peek = None

    for p in self._players:
      if not p.is_blackjack():
        continue

      p._stood = True
      if peek is None:
        peek = self.dealer.peek()

      if not peek:
          winnings = self._payout(p, "blackjack")
          p.current_bet = 0
      else:
          winnings = self._payout(p, "push")

  def loop_turns(self):
    actives = self.get_active_players()

    while actives:
      print("-----------------")
      actives = self._play_round(actives)
      print("-----------------\n")

    print("------------------")
    self.dealer.reveal()

    while self.dealer.score < self._dealer_stand :
      self._hit(self.dealer)
    print("-----------------\n")

  def _play_round(self, active_players:List[BlackjackPlayer]):
    self.round += 1
    print(f"Round {self.round}")
    for p in active_players:
      self.next(p)
      clear_line()
      if p.is_21():
        p.stand()

    return [p for p in active_players if not p.is_done(verbose = False)]

  def settle(self):
    pending_players = self.get_pending()

    if self.dealer.is_bust():
      for player in pending_players:
        self._payout(player, "win")

    elif self.dealer.score < 21:
      for player in pending_players:
        outcome = self.compare(player.hand)
        self._payout(player, outcome)

    else:
      for player in pending_players:
        if player.is_21():
          self._payout(player, "push")
        else:
          self._payout(player, "loser")

    self.dealer.chips += self.pool
    print("Game Over")

  def after_round(self):
      self.display_cards_drawn()
      for p in self._all_players:
        p.reset()
