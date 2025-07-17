import pandas as pd
import matplotlib.pyplot as plt

from typing import List, Dict

from game import Blackjack
from participants import BlackjackPlayer

class WinRateVisualizer:
    """Utility class to plot win rates versus the dealer."""

    def __init__(self, game: LoggedBlackjack):
        self.game = game

    def play(self, rounds: int = 1):
        for _ in range(rounds):
            self.game.play_round()

    def plot(self):
        if not self.game.round_results:
            raise ValueError("No results to plot. Run play() first.")

        df = pd.DataFrame(self.game.round_results)
        df["win"] = df["outcome"].isin(["win", "blackjack"])
        df["round"] = df.groupby("player").cumcount() + 1
        df["rate"] = df.groupby("player")["win"].cumsum() / df["round"]

        for name, group in df.groupby("player"):
            plt.plot(group["round"], group["rate"], label=name)

        plt.xlabel("Round")
        plt.ylabel("Win Rate")
        plt.title("Win Rate vs Dealer")
        plt.legend()
        plt.tight_layout()
        plt.show()
