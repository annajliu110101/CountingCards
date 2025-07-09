# @title Participant
class Participant():

  def __init__(self, name, chips):
    self.name = name
    self.chips = chips
    self._hand = Hand()
    self.display_handle = display(DisplayHandle(), display_id=True) # display_id=True automatically generates a unique id
    self._scoreboard = None

    self.current_bet = 0

    self._settled = True
    self._skip_game = False
    self._skip_rounds = False
  # settled == Either lost or won blackjack (both will settle immediately)
  # skip rounds == Will skip being dealt cards

  # current bet is 0 when settled

  def is_waiting(self):
    # not settled == their outcome has not been determined yet, skip_rounds == they're no longer drawing -> either they've won (not blackjack), or have stood
    return not self._settled and self._skip_rounds

  def is_playing(self):
    return not self._settled and not self._skip_game and not self._skip_round

  def is_watching(self):
    return self._skip_game

  def is_eligible(self):
    return self.chips > 0

  def _set_scoreboard(self, commands:Dict):
    self._scoreboard = pd.DataFrame(commands)

  def _add_scoreboard(self, commands:Dict):
    self._scoreboard = pd.concat([self._scoreboard, self._set_scoreboard(commands)])

  def _update_display(self):
    self.display_handle.update(HTML(self._scoreboard.to_html(escape=False)))

  def display(self): pass

  def _bet(self, bet):
    self._settled = False
    self.current_bet = bet
    self.chips -= bet
    return bet

  def show_hand(self):
    print(self.hand)

  def is_settled(self):
    return self._settled

  def reset(self):
    self.hand = Hand()
    self.current_bet = 0
    self._settled = True
    self._skip_game = False
    self._skip_round = False

  def settle(self, winnings = 0):
    self.add_chips(winnings)
    self._settled = True
    self._skip_rounds = True

  def buy_chips(self, payment):
    if payment > 0:
      self.chips += payment
    else:
      raise ValueError("Payment must be a positive integer")

  def add_chips(self, payment):
    self.chips += payment

  @property
  def score(self):
    return self.hand.score

  def get_hand(self, view:bool = True) -> str:
    if view:
      return self.hand.cards
    return self.hand

  @property
  def true_score(self):
      totals = {0}
      for card in self.hand:
        new_totals = set()
        for t in totals:
            for v in card.values:
                new_totals.add(t + v)
        totals = new_totals
      legal = [t for t in totals if t <= 21]
      return max(legal) if legal else min(totals)

  def hit(self): pass
  def stand(self):pass
  def bet(self):pass
  def lost(self): pass




class BlackjackPlayer(Participant):
  def __init__(self, name, chips = 1000, strategy = None):
    super().__init__(name, chips)
    self._strategy = strategy

    self._lost = False

  def has_strategy(self):
    return self._strategy is not None

  @property
  def strategy(self):
    return self._strategy

  @strategy.setter
  def set_strategy(self, strategy):
    self._strategy = strategy

  def hit(self, card:PlayingCard):
    self.hand.add(card)

    if self.is_bust():
      self._lost = True
      self.settle()

    self.display()

  def stand(self) -> None:
    self._skip_rounds = True

  @property
  def _stood(self):
    return self._skip_rounds

  def bet(self, bid) -> int:
    return super()._bet(bid)

  def _set_scoreboard(self):
    super()._set_scoreboard({
            "Names": self.name,
            "Hands": self.get_hand(),
            "Score": self.score,
            "Chips": self.chips,
            "Bid": self.current_bet,
            "Active": not self.is_done()
        })

  def _add_scoreboard(self):
    super()._add_scoreboard(self._commands)

  def display(self):
    self._set_scoreboard()
    self._update_display()

  ############### status functions #############
  def is_done(self, verbose = True) -> bool:
    if self._lost:
      flash_line(f"{self.name} has lost, skipping...")
      return True
    if not self.is_waiting():
      flash_line(f"{self.name} has already won blackjack, skipping...")
      return True
    if self.is_21():
      flash_line(f"{self.name} has already won, skipping...")
      return True
    if not self.is_21():
      flash_line(f"{self.name} has stood, skipping...")
      return True

    return False


  def reset(self):
    super().reset()
    self._lost = False

  def is_blackjack(self):
    """
    Checks if the hand is a blackjack (an Ace and a 10-value card).
    """
    return len(self.hand.hand) == 2 and self.true_score == 21


############### PRIVATE FUNCTIONS ###############
  def is_bust(self):
    return self.hand > 21

  def is_21(self):
      return self.hand == 21

  def _get_up_card(self): pass
  def _get_hole_card(self): pass
  def peek(self): pass
  def reveal(self): pass
class Dealer(BlackjackPlayer):

  def __init__(self, stand_on = 17):
    super().__init__("Dealer", 10000)
    self._reveal = False

    self._stand_on = stand_on
############### PRIVATE FUNCTIONS ###############
  @property
  def hand(self):
    return self._hand

  def hit(self, card:PlayingCard):
    if len(self.hand) == 1 and not self._reveal:
       card.hide()
    super().hit(card)

  def _get_up_card(self):
    return self.hand[0]

  def _get_hole_card(self):
    return self.hand[1]

  def is_done(self):
    super().is_done(verbose = False)

############### PUBLIC FUNCTIONS #####################
  def peek(self):
    if self._reveal or not self._get_up_card().is_facecard():
      return False

    if self.true_score == 21:
      self.reveal()
      return True

    return False

  def reveal(self):
    if self._reveal:
      return

    self._reveal = True

    card = self._get_hole_card().reveal()

    if self.is_bust():
      self._lost = True
