from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import pandas as pd
from IPython.display import DisplayHandle, display
from ._utils import flash_line, clear_line


class BaseGame(ABC):
  def __init__(self, players:List[BlackjackPlayer], deck_factory):
    self._game = 0
    self._players = players
    self._active_players = players
    self._inactive_players = []
    self._deck = deck_factory()
    self._round_results: List[Dict] = []
    self._handle = display(DisplayHandle(), display_id=True)

  def play_round(self):
    self.before_round()
    if not self._active_players: exit()
    self._game += 1
    for phase, fn in self.phases():
        flash_line(f"{phase}…")
        done_early = fn()
        clear_line()
        if done_early:
            break
    self.after_round()

  @abstractmethod
    def phases(self) -> List[tuple[str, Callable[[], bool]]]:
        """
        Return an ordered list of (phase‑name, phase‑fn) for 
        *this* game’s round. No assumptions about dealers!
        """
  @abstractmethod
    def after_round(self) -> None:
        """Cleanup/reset between rounds."""
  @abstractmethod
    def display(self):

      
