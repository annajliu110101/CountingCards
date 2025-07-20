from abc import ABC, abstractmethod
from typing import List, Optional, Dict
import pandas as pd
from IPython.display import HTML, DisplayHandle, display

from ._utils import flash_line, clear_line
from .playingcards import DefaultCardComparer, BlackjackCardComparer
from .participants import Participant, BlackjackPlayer, Dealer
from .cards import Shoe

class Base(ABC):
	def __init__(self, players:List[Participant], deck: Deck):
		self._game:int = 0
	    self._players: List[Participant] = players
	    self._all_active_players = self._active_players = players
		self._inactive_players = []

		self._deck = deck
		self._round_results: List[Dict] = []
	    self._handle = display(DisplayHandle(), display_id=True)
	
	def play_round(self) -> None:
		if not self._active_players: exit()
		self.before_round()
		for phase, fn in self.phases():
			flash_line(f"{phase}…")
			done_early = fn()
			clear_line()
			if done_early:
				break
		self.after_round()
		
	def compare(self, player_hand:Hand, other_hand:Hand) -> str:
    	return {1: "win", 0: "push", -1:"lose"}[player_hand > other_hand) - (player_hand < other_hand)]
		
	def check_eligibility(self, player:Participant) -> bool:
	    if not player.is_eligible():
		  	self._inactive_players.append(player)
			self._all_active_players.remove(player)
			self._active_players.remove(player)
			return False
	    return True
		
	def add_history(self, player:Participant, outcome:str) -> None:
		self._round_results.append({
            "game": self._game,
            "player": player.name,
            "outcome": outcome
        })
		
	@abstractmethod
	def phases(self): pass
	@abstractmethod
	def before_round(self): pass
	@abstractmethod
	def after_round(self): pass
	@abstractmethod
	def take_bets(self): pass
	@abstractmethod
	def next(self, player): pass
	
	def get_scores(self) -> pd.Series: return pd.Series([player.score for player in self._all_active_players], name = "Scores")
	def get_chips(self) -> pd.Series: return pd.Series([player.chips for player in self._all_active_players], name = "Chips")
	def get_names(self) -> pd.Series: return pd.Series([player.name for player in self._all_active_players], name = "Names")
	def get_hands(self) -> pd.Series: return pd.Series([p.get_hand() for p in self._all_active_players], name = "Hands")
	def get_status(self) -> pd.Series: return pd.Series([not p.is_done() for p in self._all_active_players], name = "Status")
	def get_pending(self): return [p for p in self._active_players if p.is_waiting()]
		
class Game(Base):
  	def __init__(self, players:List[Participant], dealer:Optional[Dealer] = None, comparer = DefaultCardComparer):
	    self._pot = 0
		super().__init__(players, Shoe(comparer = comparer))
		self._dealer = dealer
		if self._dealer:
	    	self._all_active_players.append(self._dealer)
		
	def before_round(self):
	    self._game += 1
	    self._pot = 0
	    self._round = 0
		
	def after_round(self):
      	for p in self._players:
	        p.reset()
			self.check_eligibility(p)
		if self._dealer:
			self._dealer.reset()
				
	def take_bets(self):
	    for player in self._active_players:
	        self._pot += self._prompt_bet(player)

  	def next(self, player, verbose = True):
      	if player.has_strategy():
          	hit = player.strategy.decide(self._deck, verbose = verbose)
      	else:
			hit = input(f"{player.name} [Current Score = {player.score}]: Press 'y' to hit, any other key to stand:\n").strip().lower() == 'y'
		if hit:
        	self.deal(player, verbose=verbose)
        else:
            self.skip(player)
				
  	def _prompt_bet(self, player, prompt = "{} [chips: {}], enter bet ≥ {}: \n", min_bet = 1):
      	if player.has_strategy():
         	return player.strategy.autobet(self._deck)
      	prompt = prompt.format(player.name, player.chips, min_bet)
		while True:
			try:
          		bet = int(input(prompt))
          	except ValueError:
				print("Error:  Please enter a whole number.")
				continue
          	if bet < 1:
              	print(f"Error: Minimum bet is $1.")
				continue
          	if bet > player.chips:
				print(f"Error:  You only have {player.chips} chips.  Betting the rest.")
				bet = player.chips
            return player.bet(bet)

  	def get_active_players(self, verbose = False) -> List[BlackjackPlayer]: return [p for p in self._active_players if not p.is_done(verbose = verbose)]
	@abstractmethod
	def deal(self, player): ...
	@abstractmethod
	def skip(self, player): ...
	@abstractmethod
	def deal_opening(self): ...
	@abstractmethod
	def loop_turns(self): ...
	@abstractmethod
	def settle(self): ...

class Blackjack(Game):
	def __init__(self, players:List[BlackjackPlayer]):
		self._dealer = Dealer()
		super().__init__(players, self._dealer, BlackjackCardComparer)
	
	def phases(self):
		phases = {"Dealing First Two Cards": self.deal_opening,
				  "Play Rounds": self.loop_turns,
				  "Settling": self.settle}
		return phases.items()
			
  	def deal(self, player, verbose = True):
	    card = player.hit(self._deck.draw())
	    if verbose:
	        flash_line(f"{player.name} drew {str(card)}")
	    return card

	def skip(self, player, verbose = True):
		if verbose:
			flash_line(f"{player.name} [Score: {player.score}] has decided to stand, skipping...")
		player.stand()

  	def deal_opening(self):
		for _ in range(2):
			self._round += 1
			for p in self._all_active_players:
				self.deal(p)
		blackjack_players = [p for p in self._active_players if p.is_blackjack()]
		if not blackjack_players:
			return False
		if self._dealer.peek():
			for p in self._active_players:
				if p not in blackjack_players:
					self._payout(p, "loser")
				  	continue
			  	self.payout(p, "push")
		  	self.exit_game()
		  	return True
		else:
		  	for p in blackjack_players:
			  	self.payout(p, "blackjack")
			  	p.current_bet = 0
		  	return False

	def loop_turns(self):
		while (actives:=self.get_active_players()):
			self._round += 1
			print(f"Round {self._round}:")
			for player in actives:
				self.next(player)
				if player.is_21():
					player.stand()
		self._dealer.reveal()
		while self._dealer.is_playing():
			self.next(self._dealer)
	
	def settle(self):
		if self._dealer.is_bust():
			for player in self.get_pending():
				self.payout(player, "win")
	  	elif self._dealer.is_21():
		   	for player in self.get_pending():
			   	outcome = "push" if player.is_21() else "loser"
			   	self.payout(player, outcome)
	  	else:
		  	dealer_hand = self._dealer.score
		  	for player in self.get_pending():
			  	outcome = self.compare(player.hand, dealer_hand)
			  	self.payout(player, outcome)
	  	dealer_outcome = self.compare(self._pot, 0)
	  	self.add_history(self._dealer, dealer_outcome)
	  	self._dealer.settle(self._pot)

  	def payout(self, player, outcome):
		self.add_history(player, outcome)
		if outcome == "blackjack":
			multiplier = 3
			out_message = "{}:\nOutcome: Blackjack! \nWon:{}"
		elif outcome == "win":
			multiplier = 2
		  	out_message = "{}:\nOutcome: Winner\nWon:{}"	
		elif outcome == "push":
			multiplier = 1
		 	out_message = "{}:\nOutcome: Tied\nBroke Even, Net: {}"
		else:
			multiplier = 0
		  	out_message = "{}:\nOutcome: Loser\nLost:{}"
		winnings = player.current_bet * multiplier
		net = winnings - player.current_bet
    	flash_line(out_message.format(player.name, net)
    	player.settle(winnings)
    	self._pot -= winnings
  
