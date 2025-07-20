from abc import ABC, abstractmethod
from typing import List, Optional, Dict
import pandas as pd
from IPython.display import HTML, DisplayHandle, display
from ._utils import flash_line, clear_line
from .playingcards import DefaultCardComparer, BlackjackCardComparer
from .participants import BlackjackPlayer, Dealer
from .cards import Shoe


class Game(ABC):
  def __init__(self, players:List[BlackjackPlayer], dealer:Optional[Dealer] = None, comparer = DefaultCardComparer):
    self._pot = 0
    self._round = 0
    self._game = 0

    self._players = players
    self._dealer = dealer

    self._all_active_players = [dealer] + players
    self._active_players = players
    self._inactive_players = []
    self._deck = Shoe()
    self._round_results: List[Dict] = []
    self._handle = display(DisplayHandle(), display_id=True)
    
  def get_scores(self) -> pd.Series: return pd.Series([player.score for player in self._all_active_players], name = "Scores")
  def get_chips(self) -> pd.Series: return pd.Series([player.chips for player in self._all_active_players], name = "Chips")
  def get_names(self) -> pd.Series: return pd.Series([player.name for player in self._all_active_players], name = "Names")
  def get_hands(self) -> pd.Series: return pd.Series([p.get_hand() for p in self._all_active_players], name = "Hands")
  def get_status(self) -> pd.Series: return pd.Series([not p.is_done() for p in self._all_active_players], name = "Status")
  def get_active_players(self, verbose = False) -> List[BlackjackPlayer]: return [p for p in self._active_players if not p.is_done(verbose = verbose)]
  def get_pending(self): return [p for p in self._active_players if p.is_waiting()]
  def play_round(self):
    if not self._active_players: exit()
    self._game += 1
    for phase, fn in [
        ("Placing Bets", self.take_bets),
        ("Deal Opening", self.deal_opening),
        ("Play Rounds", self.loop_turns),
        ("Payout",self.settle),
    ]:
        flash_line(f"{phase}…")
        done_early = fn()
        clear_line()
        if done_early:
            break
    self.after_round()

  def check_eligible_players(self, player):
    if not player.is_eligible():
      self._inactive_players.append(player)
      self._all_active_players.remove(player)
      self._active_players.remove(player)
      return False
    return True

  def _prompt_bet(self, player):
      """
      Loop until we get a valid integer within the player’s stack.
      """
      if player.has_strategy():
         return player.strategy.autobet(self._deck)
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
              print(f"Error:  You only have {player.chips} chips.  Betting the rest.")
              return player.bet(player.chips)
          else:
              return player.bet(bet)

  def take_bets(self):
    for player in self._active_players:
      bet = self._prompt_bet(player)
      self._pot += bet

  def next(self, player, verbose = False):
      if player.has_strategy():
          if verbose:
              print(f"{player.name}, Your Current Score is {player.score}.")
          if player.strategy.decide(self._deck, verbose = True):
              self.deal(player, verbose = True)
          else:
              self.skip(player, verbose = False)
      else:
          action = input(f"{player.name}, Your Current Score is {player.score}.\nPress 'y' to 'hit', or press any other key to 'stand': \n")
          if action.lower() == 'y':
              card = self.deal(player)
              print(f"{player.name}: Current Score = {player.score}")
          else:
              self.skip(player)

  @abstractmethod
  def deal(self, player): ...
  @abstractmethod
  def skip(self, player): ...
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

class Blackjack(Game):
  def __init__(self, players:List[BlackjackPlayer]):
    self._dealer = Dealer()
    super().__init__(players, self._dealer, BlackjackCardComparer)

  def deal(self, player, verbose = True):
    card = self._deck.draw()
    player.hit(card)
    if verbose:
        flash_line(f"{player.name} drew {str(card)}")

    return card

  def skip(self, player, verbose = True):
    if verbose:
        flash_line(f"{player.name} [Score: {player.score}] has decided to stand, skipping...")
    player.stand()

  def before_round(self):
    if not self._deck:
        self._deck = Shoe()

    self._pool = 0
    self._round = 0

  def deal_opening(self):
      flash_line("Dealing First Two Cards....")
      for _ in range(2):
          self._round += 1
          for p in self._all_active_players:
              self.deal(p)
    
      blackjack_players = [p for p in self._active_players if p.is_blackjack()]
      
      if not blackjack_players:
        return False

      peek = self._dealer.peek()

      if peek:
          for p in self._active_players:
              if p not in blackjack_players:
                  self._payout(p, "loser")
                  continue
              self._payout(p, "push")
          self.exit_game()
          return True
      else:
          for p in blackjack_players:
              self._payout(p, "blackjack")
              p.current_bet = 0
          return False

  def loop_turns(self):
      while (actives:=self.get_active_players()):
          self._play_round(actives)
      self._dealer.reveal()
      while self._dealer.is_playing():
          self.next(self._dealer)


  def exit_game(self):
      if (self._pot < 0):
          dealer_outcome = "loser"
      elif (self._pot > 0):
          dealer_outcome = "win"
      else:
          dealer_outcome = "push"

      self._round_results.append({
              "game": self._game,
              "player": self._dealer.name,
              "outcome": dealer_outcome
          })
      self._dealer.settle(self._pot)

  def _play_round(self, active_players:List[BlackjackPlayer]):
      self._round += 1
      print(f"Round {self._round}:")
      for p in active_players:
          self.next(p)
          clear_line()
          if p.is_21():
              p.stand()

  def settle(self):
      pending_players = self.get_pending()

      if self._dealer.is_bust():
          for player in pending_players:
              self._payout(player, "win")

      elif self._dealer.score < 21:
          for player in pending_players:
              outcome = self.compare(player.hand)
              self._payout(player, outcome)

      else:
          for player in pending_players:
              if player.is_21():
                  self._payout(player, "push")
              else:
                  self._payout(player, "loser")
      self.exit_game()

  def compare(self, player_hand):
    if player_hand > self._dealer.hand:
      return "win"
    elif player_hand < self._dealer.hand:
      return "lose"
    else:
      return "push"

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
    self._pot -= winnings
    flash_line(out_message)
    self._round_results.append({
            "game": self._game,
            "player": player.name,
            "outcome": outcome
        })
    return winnings

  def after_round(self):
      for p in self._players:
        p.reset()
        if not self.check_eligible_players(p):
          continue
      self._dealer.reset()


