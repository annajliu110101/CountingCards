from abc import ABC, abstractmethod
from participants import Player, Dealer
from game import Game

class Strategy(ABC):
    """
    Abstract base class for decision-making algorithms.
    Students can create new strategies by subclassing this.
    """
    @abstractmethod
    def decide(self, player:Player, game:Game):
        """
        Implement this method to define how a player should act.
        It should call player.hit() or player.stand() as needed.
        """
        pass

class DealerStrategy(Strategy):
  def __init__(player:Player):
      self.player = player
  def decide(self, game, verbose = False) -> None:
    if self.player.score < 17:
      game.deal(self._player, verbose = verbose)
    else:
      game.skip(self._player, verbose = verbose)

# @title Create a Strategy Here!  Implement method decide(player, game)

class YourStrategy(Strategy):

  def decide(self, player:Player, game:Game) -> None:
    pass

