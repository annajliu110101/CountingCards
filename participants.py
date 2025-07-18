from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from strategy import Strategy, DealerStrategy
  
from typing import Dict, Optional, Union
import pandas as pd
from IPython.display import HTML, DisplayHandle, display

from cards import Hand
from playingcards import PlayingCard
from strategy import Strategy
from _utils import flash_line

class Participant:
  def __init__(self, name:str, chips:int):
    self.name, self.chips = name, chips
    self._hand = Hand()
    
    self.display_handle = display(DisplayHandle(), display_id=True) # display_id=True automatically generates a unique id
    self._scoreboard = None
    self.current_bet = 0

    self._settled = True
    self._skip_rounds = False
    self._skip_game = False

  def is_settled(self) -> bool: return self._settled
  def is_waiting(self) -> bool: return not self._settled and self._skip_rounds
  def is_playing(self) -> bool: return not self._settled and not self._skip_game and not self._skip_rounds
  def is_watching(self) -> bool: return self._skip_game
  def is_eligible(self) -> bool:
      if self.chips > 0:
          self._skip_game = False
          return True
      self._skip_game = True
      return False


  def _set_scoreboard(self, commands:Dict) -> None: self._scoreboard = pd.DataFrame([commands])
  def _add_scoreboard(self, commands:Dict) -> None: self._scoreboard = pd.concat([self._scoreboard, self._set_scoreboard(commands)])
  def _update_display(self) -> None: self.display_handle.update(HTML(self._scoreboard.to_html(escape=False)))

  def _bet(self, bet:int) -> int:
      self._settled = False
      self.chips -= bet
      self.current_bet = bet
      return bet

  def reset(self) -> None:
      self._hand.reset()
      self.current_bet = 0
      self._settled = True
      self._skip_rounds = False

  def settle(self, winnings:int = 0) -> None:
      self.add_chips(winnings)
      self._settled = True
      self._skip_rounds = True

  def add_chips(self, payment:int) -> None: 
      self.chips += payment
      self.is_eligible()

  def show_hand(self) -> str: print(self._hand)
  def get_hand(self) -> Union[str, Hand]: return self._hand.cards

  @property
  def hand(self) -> Hand: return self._hand
  @property
  def score(self) -> int: return self._hand.score
  @property
  def true_score(self) -> int: return self._hand.true_score()

  def hit(self): pass
  def stand(self):pass
  def bet(self):pass
  def lost(self): pass
  def display(self): pass

class BlackjackPlayer(Participant):
  def __init__(self, name, chips = 10000, strategy = None):
        super().__init__(name, chips)
        self._strategy = strategy(self)
        self._lost = False

  def stand(self) -> None: self._skip_rounds = True
  def bet(self, bid) -> int: return super()._bet(bid) 
  def has_strategy(self) -> bool: return self._strategy is not None
  def _add_scoreboard(self) -> None: super()._add_scoreboard(self._commands)
  
  def is_blackjack(self) -> bool: return len(self._hand) == 2 and self.true_score == 21
  def is_bust(self): return self._hand > 21
  def is_21(self): return self._hand == 21

  @property
  def strategy(self) -> "Strategy": return self._strategy
  @strategy.setter
  def set_strategy(self, strategy) -> None: self._strategy = strategy
  @property
  def _stood(self) -> bool: return self._skip_rounds

  def hit(self, card:PlayingCard) -> PlayingCard:
      self._hand.add(card)
      if self.is_bust():
          self._lost = True
          self.settle()
      self.display()
      return card

  def display(self) -> None :
    super()._set_scoreboard({
            "Names": self.name,
            "Hands": self.get_hand(),
            "Score": self.score,
            "Chips": self.chips,
            "Status/Active": not self.is_done()
        })
    self._update_display()
    
  
  def is_done(self, verbose=True) -> bool:
      if self.is_bust():
          if verbose:
              flash_line(f"{self.name} has lost, skipping...")
          return True
      if not self.is_waiting() and self.is_21():
          if verbose: 
              flash_line(f"{self.name} has already won blackjack, skipping...")
          return True
      if self.is_21() and self.is_waiting():
          if verbose:
              flash_line(f"{self.name} has already won, skipping...")
          return True
      if not self.is_21() and self.is_waiting():
          if verbose:
              flash_line(f"{self.name} has stood, skipping...")
          return True
      return False

  def reset(self) -> None:
      super().reset()
      self._lost = False

  def _get_up_card(self): pass
  def _get_hole_card(self): pass
  def peek(self): pass
  def reveal(self): pass

class Dealer(BlackjackPlayer):
    def __init__(self):
        super().__init__("Dealer", 10000, DealerStrategy)
        self._reveal = False

    def hit(self, card:PlayingCard):
        if len(self._hand) == 1 and not self._reveal: card.hide()
        super().hit(card)

    def _get_up_card(self) -> PlayingCard: return self._hand[0]
    def _get_hole_card(self) -> PlayingCard: return self._hand[1]

    def settle(self, winnings = 0):
        super().settle(winnings)
        flash_line("Game Over")
    
    def reset(self):
        super().reset()
        self._reveal = False

    def peek(self) -> bool:
        if self._reveal or not self._get_up_card().is_facecard(): return False     
        return self.hand.scoring_algorithm(False).__contains__(21) and self.reveal()
        return False

    def reveal(self) -> PlayingCard:
        if self._reveal: 
          return None
        self._reveal = True
        card = self._get_hole_card().reveal()
        if self.is_bust(): 
          self._lost = True
        return card
