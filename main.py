from participants import BlackjackPlayer
from game import Blackjack

if __name__ == '__main__':
  players = [BlackjackPlayer("Anna"), BlackjackPlayer("Noe"), BlackjackPlayer("Daniel")]

  game = Blackjack(players)

  game.play_round()
