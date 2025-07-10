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

class GeneralStrategy(Strategy):
  def decide(self, player:Player, game:Game) -> None:
    if player.score < 17:
      game._hit(player)
    else:
      game._stand(player)

# @title Create a Strategy Here!  Implement method decide(player, game)

class YourStrategy(Strategy):

  def decide(self, player:Player, game:Game) -> None:
    pass

