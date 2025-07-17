from abc import ABC, abstractmethod
from participants import BlackjackPlayer, Dealer
from game import Game

class Strategy(ABC):
    """
    Abstract base class for decision-making algorithms.
    Students can create new strategies by subclassing this.
    """
    @abstractmethod
    def decide(self, player: BlackjackPlayer, game: Game):
        """
        Implement this method to define how a player should act.
        It should call player.hit() or player.stand() as needed.
        """
        pass

class DealerStrategy(Strategy):
  def __init__(player:Dealer):
      self._player = player
  def decide(self, game: Game, verbose: bool = False) -> None:
    if self._player.score < 17:
      game.deal(self._player, verbose = verbose)
    else:
      game.skip(self._player, verbose = verbose)

# @title Create a Strategy Here!  Implement method decide(player, game)

class YourStrategy(Strategy):

  def decide(self, player:BlackjackPlayer, game:Game) -> None:
    pass

