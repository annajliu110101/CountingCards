from .participants import BlackjackPlayer
from .game import Blackjack
from .visualization import WinRateVisualizer

def run():
  players = [BlackjackPlayer("Anna"), BlackjackPlayer("Noe"), BlackjackPlayer("Daniel")]

  game = Blackjack(players)

  game.play_round()

  
def batched_run():
  players = [BlackjackPlayer("Anna", strategy = HiLoStrategy), BlackjackPlayer("Noe", strategy = HiLoStrategy), BlackjackPlayer("Daniel", strategy = HiLoStrategy)]

  game = Blackjack(players)

  WinRateVisualizer(game).play(50)
  
if __name__ == '__main__':
  batched_run()
  
