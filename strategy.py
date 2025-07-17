from abc import ABC, abstractmethod
from participants import BlackjackPlayer, Dealer
from game import Game


class Strategy(ABC):
    """
    🎯 This is the base Strategy class — the 'brain blueprint' for Blackjack.

    ⚠️ You never need to touch this class directly.
    It’s already connected to the rest of the game behind the scenes.

    ✅ You *will not* call this like: Strategy(player) — that would crash.
    Instead, you'll use: YourStrategy(player)

    Every Strategy has access to:
    - self._player: the player it controls
    - self._autobet: the default bet amount (100)

    You *must* fill in the 'decide()' method in your strategy.
    That's where you write your decision logic.

    ✅ This is already wired into the game loop.
    ✅ You do NOT need to write a game or modify other files.
    ✅ You ONLY need to define the logic inside YourStrategy.decide().
    """

    def __init__(self, player: BlackjackPlayer): 
        self._player = player
        self._autobet = 100

    def autobet(self):
        return self._player.bet(self._autobet)

    @abstractmethod
    def decide(self, game: Game):
        """
        You must implement this method in your own strategy.
        This is where your Blackjack player decides what to do.

        When the game reaches your turn, it will automatically call:

            your_strategy.decide(game)

        In this method, you should call:
        - game.deal(self._player)  → to hit
        - game.skip(self._player)  → to stand
        """
        pass


class DealerStrategy(Strategy):
    """
    🃏 This is the built-in strategy used by the Dealer.
    The dealer follows standard Blackjack rules:
    - Hit if score is < 17
    - Stand otherwise

    You can use this as an example!
    """

    def __init__(player: Dealer):
        super().__init__(player)

    def autobet(self):
        pass  # dealer doesn't bet

    def decide(self, game: Game, verbose: bool = False) -> None:
        if self._player.score < 17:
            game.deal(self._player, verbose=verbose)
        else:
            game.skip(self._player, verbose=verbose)

class HiLoStrategy(Strategy):
    """
    🔢 Hi-Lo Strategy: A simple card-counting Blackjack strategy.

    This uses the "Hi-Lo" counting system:
    - Low cards (2–6) → +1
    - Mid cards (7–9) → 0
    - High cards (10–A) → -1

    The count is based on the remaining cards in the shoe.

    Basic idea:
    - If count is HIGH (positive), good cards are left → play more aggressively
    - If count is LOW (negative), mostly bad cards left → play conservatively

    This strategy is already integrated — no need to change anything.
    It plays automatically based on the current count.

    Example usage:
    -------------------
    player = BlackjackPlayer()
    hilo_brain = HiLoStrategy(player)
    hilo_brain.decide(game)
    -------------------
    """
    def autobet(self):
        """
        💰 Smarter betting using card counts.

        We'll increase our bet when the deck is rich in 10s and Aces
        (this means more blackjacks are possible and the dealer is more likely to bust)

        We'll decrease our bet when the shoe is filled with low cards.

        This works *exactly* like our Hi-Lo count from the decide() method.
        """

        card_counts = self._player._game._cards.stats.count_remaining_cards()

        count = 0
        for card, qty in card_counts.items():
            rank = str(card.rank)
            if rank in ['2', '3', '4', '5', '6']:
                count += qty
            elif rank in ['10', 'J', 'Q', 'K', 'A']:
                count -= qty

        # Normalize to get "true count" if you want (not shown here)

        if count > 10:
            return self._player.bet(500)  # 🔥 very favorable — bet big
        elif count > 5:
            return self._player.bet(300)
        elif count > 0:
            return self._player.bet(200)
        elif count > -5:
            return self._player.bet(100)
        else:
            return self._player.bet(25)   # ❄️ not favorable — play cautious
            
    
    def decide(self, game: Game) -> None:
        """
        Called automatically during the game when it’s this player’s turn.
        """
        score = self._player.score
        
        card_counts = game.stats.count_all_cards_dealt()
        count = 0

        for card, qty in card_counts.items():
            rank = str(card.rank)
            if rank in ['2', '3', '4', '5', '6']:
                count += qty
            elif rank in ['10', 'J', 'Q', 'K', 'A']:
                count -= qty
            # 7, 8, 9 → count += 0 (ignored)

        """
        Now use the Hi-Lo count to make a decision.

        - If the count is HIGH (lots of high cards left), try to go for 21!
        - If the count is LOW, assume you’ll bust — play it safe.
        """

        if count > 5:
            # Be aggressive
            if score < 18:
                game.deal(self._player)
            else:
                game.skip(self._player)
        elif count < -5:
            # Be cautious
            if score < 12:
                game.deal(self._player)
            else:
                game.skip(self._player)
        else:
            # Neutral
            if score < 16:
                game.deal(self._player)
            else:
                game.skip(self._player)

class YourStrategy(Strategy):
    """
    🧠 This is YOUR strategy! You get to program the brain of your Blackjack player.

    🔧 Everything is already set up. You don’t have to change anything outside this file.
    Just fill in the 'decide' method below to control how your player acts during the game.

    🎲 Here’s what you can use in your logic:

    self._player.score
        → Your current score (e.g. 13, 17, etc.)

    game.get_dealer_card()
        → The dealer’s *face-up* card (you can peek at it!)

    game.stats.win_rate(self._player)
        → Your overall win rate in the game so far

    game.stats.average_score(self._player)
        → Your average score over previous rounds

    game.stats.card_counter()
        → Gives you a simplified count of remaining high/low cards in the shoe

    game.round_num
        → Which round you're in (0 = first round, 1 = second round, ...)

    ✏️ Example logic:
        if self._player.score < 15:
            game.deal(self._player)
        else:
            game.skip(self._player)

    🚀 Once you write your logic, run the simulation and watch how it plays out!
    """

    def decide(self, game: Game) -> None:
        """
        Write your Blackjack strategy here!

        Use info from the game or stats to decide:
        - Should you hit (take another card)?
        - Or stand (keep your current score)?

        Remember:
        - game.deal(self._player)  → to hit
        - game.skip(self._player)  → to stand
        """
        pass
