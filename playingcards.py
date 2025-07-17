from typing import Optional
class DefaultCardComparer:
  @staticmethod
  def equals(card1, card2):return card1.code == card2.code

  @staticmethod
  def hash(card): return hash(card.code)

  @staticmethod
  def get_score(card):
    if card.rank == "A":
      return 11
    elif card.rank.isdigit():
      return int(card.rank)
    else:
      return 10

class BlackjackCardComparer:
  @staticmethod
  def equals(card1, card2): return card1.rank == card2.rank

  @staticmethod
  def hash(card): return hash(card.rank)

  @staticmethod
  def get_score(card):
    if card.rank == "A":
      return 11
    elif card.rank.isdigit():
      return int(card.rank)
    else:
      return 10

class PlayingCard():
  def __init__(self, code:str, name:str, suit_name:str, symbol_code:Optional[str] = None, faceup:bool = False, comparer = DefaultCardComparer): # eg. PlayingCard('10H', '10', 'hearts', '♥')
  # Save the basic info
    self._code   = code     # e.g. '10H'
    self._name   = name     # e.g. '10'
    self._suit   = suit_name    # e.g. 'spades'
    self._comparer = comparer

    self._symbol = symbol_code   # e.g. '♥'
    self._faceup = faceup

    self._rank = code[:-1]
    self._img = f"/content/{self.name}_of_{self.suit}.png"
    self._back = '/content/back.png'

  @property
  def code(self): return self._code
  @property
  def name(self): return self._name
  @property
  def suit(self): return self._suit
  @property
  def symbol(self): return self._symbol
  @property
  def rank(self): return self._rank
  def __eq__(self, other): return self._comparer.equals(self, other)
  def __ne__(self, other): return not self.__eq__(other)
  def __hash__(self): return self._comparer.hash(self)
  
  def __str__(self):
    """
    When you print a card object, you get something like 'A♠' or '10♥'.  Or, if symbol_code was not specified, the actual code is supplemented.
    """
    if self._symbol:
      return f"{self._code[:-1]}{self._symbol}" if self._faceup else '░░░░░░'
    return self._code if self._faceup else '░░░░░░'

  def copy(self): return PlayingCard(self._code, self._name, self._suit, self._symbol, self._faceup, self._comparer)

  def get_score(self) -> int: self._comparer.get_score(self)

  def flip(self):
    self._faceup = not self._faceup
    return self
    
  def reveal(self):
    self._faceup = True
    return self

  def hide(self):
    self._faceup = False
    return self

  @property
  def values(self):
    if self._rank == 'A':
      return (1, 11)
    return (self._comparer.get_score(self),)

  @property
  def faceup(self): return self._faceup

  def get_img(self):
    """
    Returns the raw image array you can show with matplotlib.
    """
    return self._img if self._faceup else self._back

  def is_facecard(self):
    return self._name in ['jack', 'queen', 'king', 'ace']

