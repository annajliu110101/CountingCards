from collections import Counter
import base64
import io
import random
from collections import Counter
from typing import List

import matplotlib.pyplot as plt
import numpy as np
from IPython.display import DisplayHandle, display

from _utils import CardInfo
from playingcards import PlayingCard, DefaultCardComparer, BlackjackCardComparer
class Hand():
  def __init__(self):
    self._cards = []

  def __len__(self):
    return len(self._cards)

  def __getitem__(self, position):
    return self._cards[position]

  def __iter__(self):
    return iter(self._cards)

  def __str__(self):
    return ", ".join([str(card) for card in self._cards])

  def __eq__(self, other):
    if isinstance(other, int):
      return self.score == other
    if isinstance(other, Hand):
      return self.score == other.score
    return NotImplemented

  def __gt__(self, other):
    if isinstance(other, int):
      return self.score > other
    if isinstance(other, Hand):
      return self.score > other.score
    return NotImplemented

  def __ge__(self, other):
    if isinstance(other, int):
      return self.score >= other
    if isinstance(other, Hand):
      return self.score >= other.score
    return NotImplemented

  def __lt__(self, other):
    if isinstance(other, int):
      return self.score < other
    if isinstance(other, Hand):
      return self.score < other.score
    return NotImplemented

  def __le__(self, other):
    if isinstance(other, int):
      return self.score <= other
    if isinstance(other, Hand):
      return self.score <= other.score
    return NotImplemented

  def reveal_all(self):
    for card in self._cards:
      if not card.faceup:
        card.reveal()

  def hide_all(self):
    for card in self._cards:
      if card.faceup:
        card.hide()

  def view(self):
    def helper_html(fig):
      buf = io.BytesIO()
      fig.savefig(buf, format='png', bbox_inches='tight')
      buf.seek(0)
      img_bytes = buf.read()
      base64_str = base64.b64encode(img_bytes).decode('utf-8')
      plt.close(fig)
      return base64_str

    fig, axes = plt.subplots(1, len(self._cards), figsize=(len(self._cards)*1.125, 1.5))

    axes = axes.flat if isinstance(axes, np.ndarray) else [axes]
    for ax, card in zip(axes, self._cards):
        ax.imshow(plt.imread(card.get_img()))
        ax.axis('off')

    return f'<img src="data:image/png;base64,{helper_html(fig)}" width="{len(self._cards)*60}px">'

  def add(self, card:PlayingCard):
    self._cards.append(card)

  def true_score(self):
      totals = {0}
      for card in self._cards:
        new_totals = set()
        for t in totals:
            for v in card.values:
                new_totals.add(t + v)
        totals = new_totals
      legal = [t for t in totals if t <= 21]
      return max(legal) if legal else min(totals)

  def copy(self):
    return Hand([card.copy() for card in self._cards])
  @property
  def score(self):
        """
        Return the highest score ≤ 21 (if any), otherwise the minimal score.
        Handles any number of aces by trying all combos the cheap way.
        """
        totals = {0}
        for card in self._cards:
          if not card.faceup:
            continue
          new_totals = set()
          for t in totals:
              for v in card.values:
                  new_totals.add(t + v)
          totals = new_totals
        legal = [t for t in totals if t <= 21]
        return max(legal) if legal else min(totals)
  @property
  def cards(self):
      return self.view()
  @property
  def hand(self):
      return self._cards

  def clear(self):
    self._cards = []

  def has_aces(self):
    if "A" in self._cards:
      return True
    return False

  def tryout(self, card:PlayingCard):
    totals = {self.true_score()}
    if not self.has_aces():
      new_totals = set()
      for t in totals:
        for v in card.values:
          new_totals.add(t + v)
      totals = new_totals
      return max(totals) <= 21

    else:
      new_hand = self.copy().add(card)
      return new_hand.true_score() <= 21

  def _create_deck(self): pass
  def _append(self): pass
  def _extend(self): pass
  def _merge(self): pass
  def draw(self): pass




class Deck(Hand):
  """
  A full 52-card deck (Standard Usage)  Shuffled once upon creation.
  You can draw cards one at a time.
  """
  def __init__(self, build:bool = True, comparer = DefaultCardComparer):

    self._comparer = comparer
    self._info = CardInfo.get_info()
    self._cards = self._create_deck() if build is True else []

  def deck(self):
    return self._cards

  def _create_deck(self):
    deck = []
    comparer = self._comparer
    for card_code, rank_name, suit_name, symbol_code in self._info:
      deck.append(PlayingCard(card_code, rank_name, suit_name, symbol_code, comparer = comparer))

    random.shuffle(deck)
    return deck

  def _extend(self, cards:List[PlayingCard]):
    self._cards += cards

  def _merge(self, deck):
    self._cards += deck._cards
    random.shuffle(self._cards)

  def _append(self, num_decks = 1):
    self._cards += self._create_deck()
    random.shuffle(self._cards)

  def draw(self):
    if len(self._cards) == 0:
      self.reset()
    return self._cards.pop()


class Shoe(Deck):
    def __init__(self, num_decks=1, shuffle_freq=0):
        super().__init__(build=False, comparer=BlackjackCardComparer)
        self._num_decks = num_decks
        self._shuffle_freq = shuffle_freq

        self._cards = []
        self._append(num_decks)
        self.display_handle = display(DisplayHandle(), display_id=True)

        # Counter of PlayingCard objects (one per rank, thanks to __hash__/__eq__)
        self._freq = Counter(self._cards)
    def frequency(self):
        return self._freq

    def draw(self):
        card = super().draw()
        self._freq[card] -= 1
        return card

    def _reset(self):
        self._cards.clear()
        self._append(self._num_decks)
        self._freq = Counter(self._cards)

class ShoeStats:
    def __init__(self, shoe: Shoe, dealer):
        self._shoe = shoe
        self._dealer = dealer
        # Use rank-card mapping for easy lookups
        self._rank_cards = {card.rank: card for card in self._shoe._deck}
        self._freq = shoe.frequency()
        self._hole_card = None

    def update(self):
        # Update hole_card reference based on dealer's hand
        hole = self._dealer._get_hole_card()
        if hole and not hole.faceup:
            self._hole_card = hole
        else:
            self._hole_card = None
        # Always update freq and cards_left from shoe
        self._freq = self._shoe.frequency()

    def card_probs(self):
        # Probability by rank, using a canonical card for each rank as key
        probs = {}
        for rank, card in self._rank_cards.items():
            total_left = self._freq[card]
            probs[rank] = total_left / self.cards_left if self.cards_left > 0 else 0
        # Optionally adjust for unrevealed hole card if needed
        # (Usually not necessary if you follow correct shoe/dealing logic)
        return probs

    def left_by_rank(self):
        # Convenient dict for display: {rank: count}
        return {rank: self._freq[card] for rank, card in self._rank_cards.items()}
