import time
import sys

def flash_line(msg: str, pause: float = 1.5) -> None:
    """
    Show `msg` on a single console line for `pause` seconds, then
    leave the cursor at column-0 ready for the next update.
    """
    sys.stdout.write("\r" + msg.ljust(80))
    sys.stdout.flush()
    time.sleep(pause)

def clear_line() -> None:
    sys.stdout.write("\r" + " " * 80 + "\r")
    sys.stdout.flush()

class CardInfo:
  SUITS =  {'S':
                      {'name': 'spades',
                        'symbol': '\u2660'}, # this is the unicode format -> ♠ when printed
                  'D':
                      {'name': 'diamonds',
                        'symbol': '\u2666'},
                  'C':
                      {'name': 'clubs',
                        'symbol': '\u2663'},
                  'H':
                      {'name': 'hearts',
                        'symbol': '\u2665'}
                  }
  NAMES = {'A': 'ace', '2':'2', '3':'3','4':'4', '5':'5',
           '6':'6','7':'7','8':'8','9':'9','10':'10',
           'J':'jack','Q':'queen','K':'king'}

  INFO = []

  for rank_letter, rank_name in NAMES.items(): # eg. 'A', 'ace'
    for char_suit, values in SUITS.items(): # eg. 'S', {'name': 'spades', 'symbol': '\u2660'}
      card_code = str(rank_letter) + str(char_suit) # eg. AS
      INFO.append([card_code, rank_name, *values.values()])

  @staticmethod
  def get_info():
    return CardInfo.INFO
