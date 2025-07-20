from pathlib import Path
from typing import Optional

ROOT = Path(__file__).parent.resolve()


class DefaultCardComparer:
  @staticmethod
  def equals(card1:PlayingCard, card2:PlayingCard):
      return card1.code == card2.code

  @staticmethod
  def hash(card:PlayingCard):
      return hash(card.code)

  @staticmethod
  def get_score(card:PlayingCard):
    if card.rank == "A":
      return 11
    elif card.rank.isdigit():
      return int(card.rank)
    else:
      return 10

class BlackjackCardComparer:
  @staticmethod
  def equals(card1:PlayingCard, card2:PlayingCard):
      return card1.rank == card2.rank

  @staticmethod
  def hash(card:PlayingCard):
      return hash(card.rank)

  @staticmethod
  def get_score(card:PlayingCard):
    if card.rank == "A":
      return 11
    elif card.rank.isdigit():
      return int(card.rank)
    else:
      return 10

  @staticmethod
  def get_values(card:PlayingCard):
    if card.rank == "A":
      return (1, 11)
    return (BlackjackCardComparer.get_score(card),)


class PlayingCard():
  def __init__(self, code:str, name:str, suit_name:str, symbol_code:Optional[str] = None, faceup:bool = False, comparer = DefaultCardComparer): # eg. PlayingCard('10H', '10', 'hearts', '♥')

    self._code, self._name, self._suit = code, name, suit_name     
    self._symbol = symbol_code   # e.g. '♥'
    self._faceup = faceup
    self._comparer = comparer
    self._rank = code[:-1]
    self._img = f"{ROOT}/content/{self.name}_of_{self.suit}.png"
    self._back = f'{ROOT}/content/back.png'


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
  @property
  def values(self): return self._comparer.get_values(self)
  @property
  def faceup(self): return self._faceup

  def __eq__(self, other):return self._comparer.equals(self, other) 
  def __ne__(self, other): return not self.__eq__(other)
  def __hash__(self): return self._comparer.hash(self)
  def __str__(self): return f"{self.rank}{self.symbol}" if self._faceup and self.symbol else (self.code if self._faceup else '░░░░░░')
  def copy(self): return PlayingCard(self._code, self._name, self._suit, self._symbol, self._faceup, self._comparer)
  def get_score(self) -> int: self._comparer.get_score(self)
  def is_facecard(self): return self._name in ['jack', 'queen', 'king', 'ace']
  def get_img(self): return self._back if not self._faceup else self._img

  def reveal(self):
      self._faceup = True
      return self

  def hide(self):
      self._faceup = False
      return self
