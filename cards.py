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
    def __init__(self, cards = None):
        self._cards = cards or []

    def _cmp(self, other, op):
          s = self.score
          o = other.score if isinstance(other, Hand) else int(other)
          return op(s, o)

    def __len__(self): return len(self._cards)
    def __getitem__(self, position): return self._cards[position]
    def __iter__(self): return iter(self._cards)
    def __str__(self): return ", ".join([str(card) for card in self._cards])

    def __eq__(self, other): return self._cmp(other, lambda a, b: a == b)
    def __gt__(self, other): return self._cmp(other, lambda a, b: a >  b)
    def __ge__(self, other): return self._cmp(other, lambda a, b: a >= b)
    def __lt__(self, other): return self._cmp(other, lambda a, b: a <  b)
    def __le__(self, other): return self._cmp(other, lambda a, b: a <= b)

    def reveal_all(self): [card.reveal() for card in self._cards if not card.faceup]
    def hide_all(self): [card.hide() for card in self._cards if card.faceup]
    def add(self, card:PlayingCard): self._cards.append(card)
    def copy(self): return Hand([card.copy() for card in self._cards])
    def reset(self): self._cards = []

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

    def scoring_algorithm(self, ignore_hidden = True):
        totals = {0}
        for card in self._cards:
            if ignore_hidden and not card.faceup:
                continue
            totals = {t + v for t in totals for v in c.values}
        return totals

    def true_score(self):
        totals = self.scoring_algorithm(ignore_hidden = False)
        legal = [t for t in totals if t <= 21]
        return max(legal) if legal else min(totals)

    @property
    def score(self):
          totals = self.scoring_algorithm()
          legal = [t for t in totals if t <= 21]
          return max(legal) if legal else min(totals)

    @property
    def cards(self): return self.view()
    @property
    def hand(self): return self._cards


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

  def reset(self): self._cards = []

class Shoe(Deck):
    def __init__(self, num_decks = 4):
        super().__init__(build=False, comparer=BlackjackCardComparer)
        self._num_decks = num_decks
        self.reset()

    def draw(self, flip = True):
      card = super().draw()
      if flip:
        card.reveal()
      return card

    def reset(self):
        super().reset()
        self._append(self._num_decks)
        self._stats = Stats(self._cards)

    @property
    def stats(self): return self._stats



class Stats:
    def __init__(self, all_cards):
        self._all_cards = all_cards
        self.display_handle = display(DisplayHandle(), display_id=True) # display_id=True automatically generates a unique id

    def outcome_odds(self, hand: Hand):
        """Return bust/safe/blackjack odds if the player hits."""
        bust = blackjack = safe = 0
        curr_scores = set(hand.scoring_algorithm())
        values_left = self.counter(mode="values")
        total = 0

        for value, count in values_left.items():
            if count <= 0:
                continue
            score = self.try_value(curr_scores, value)
            if score > 21:
                bust += count
            elif score == 21:
                blackjack += count
            else:
                safe += count
            total += count

        return {
            "bust": bust / total,
            "safe": safe / total,
            "blackjack": blackjack / total,
        }

    def try_value(self, score_candidates, value):
        totals = {0}
        new_totals = set()
        for t in score_candidates:
            for v in value:
               new_totals.add(t + v)
            totals = new_totals
        score_candidates = totals
        legal = [t for t in score_candidates if t <= 21]
        return max(legal) if legal else min(score_candidates)

    def counter_df(self, mode = ""):
        rank_counts = self.counter(mode)
        return pd.Series(rank_counts, dtype=int).reindex(ALL_RANKS, fill_value=0).to_frame().T

    def count_all_cards_dealt(self, nice_print_format = False):
        if nice_print_format:
            return self.counter_df(mode = "faceup")
        return self.counter(mode = "faceup")

    def count_remaining_cards(self, nice_print_format = False):
        if nice_print_format:
            return self.counter_df(mode = "facedown")
        return self.counter(mode = "facedown")

    def count_values(self,  nice_print_format = False):
        if nice_print_format:
            return self.counter_df(mode = "values")
        return self.counter(mode = "values")

    def counter(self, mode = ""):
        counts = defaultdict(int)
        for card in self._all_cards:
            if mode == "faceup" and not card.faceup: continue           
            if mode == "facedown" and card.faceup: continue

            key = card.values if mode == "values" else card
            counts[key] += 1
        return counts
