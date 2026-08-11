#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
σLang §AU — Auction Protocol: Sealed-Bid Second-Price (Vickrey)
Implementation A (independent single-file implementation)

Fingerprints: 0xA001 auction_create · 0xA002 bid · 0xA003 auction_close · 0xA004 auction_cancel

Auction state: [item_id, seller_id, reserve, phase, [Bid...], winner, price]
phase: 0=open · 1=closed · 2=cancelled
Bid:   [bidder_id, amount]

Design decisions (documented, per AU.3 intentional ambiguities):
  D1. Bid list order: NEWEST bid is PREPENDED (spec tests in AU.2.2/AU.4 show
      the latest bid first in the list).
  D2. "Last one counts" (same bidder, multiple bids): the latest bid per
      bidder wins; since the list is newest-first, dedup keeps the FIRST
      occurrence of each bidder at close time.
  D3. Tie at top: stable sort by amount desc ⇒ earlier-in-list bidder wins.
  D4. Errors: Python exceptions (ReserveErr / BidAmountErr / ClosedErr),
      raised → ⊥.
  D5. reserve=0: a bid of amount 0 is valid (amount >= reserve).
  D6. auction_close on phase=1 → identity (idempotent, per AU.2.3 law);
      on phase=2 → ClosedErr (void auction cannot be settled).
  D7. auction_cancel on phase=1 → ClosedErr; on phase=2 → identity
      (idempotent no-op, mirroring close's idempotency).
"""

from __future__ import annotations
import sys

# ---------------------------------------------------------------------------
# Errors (⊥)
# ---------------------------------------------------------------------------

class AuctionError(Exception):
    """Base class for all auction protocol errors (⊥)."""

class ReserveErr(AuctionError):
    """Negative reserve price."""

class BidAmountErr(AuctionError):
    """Negative bid amount."""

class ClosedErr(AuctionError):
    """Operation not allowed in current phase (closed/cancelled)."""

# ---------------------------------------------------------------------------
# AU.2.1 auction_create — 0xA001
# ---------------------------------------------------------------------------

def auction_create(item: int, seller: int, reserve: int) -> list:
    """Create an open auction. [item, seller, reserve, 0, [], 0, 0]"""
    if reserve < 0:
        raise ReserveErr(f"reserve must be >= 0, got {reserve}")
    return [item, seller, reserve, 0, [], 0, 0]

# ---------------------------------------------------------------------------
# AU.2.2 bid — 0xA002
# ---------------------------------------------------------------------------

def bid(auction: list, bidder: int, amount: int) -> list:
    """Place a sealed bid. Open phase only, amount >= 0. Bid is prepended."""
    if auction[3] != 0:
        raise ClosedErr(f"cannot bid on auction in phase {auction[3]}")
    if amount < 0:
        raise BidAmountErr(f"bid amount must be >= 0, got {amount}")
    return [auction[0], auction[1], auction[2], 0, [[bidder, amount]] + auction[4], 0, 0]

# ---------------------------------------------------------------------------
# AU.2.3 auction_close — 0xA003
# ---------------------------------------------------------------------------

def _latest_bid_per_bidder(bids: list) -> list:
    """'Last one counts': list is newest-first, so keep first occurrence per bidder."""
    seen = set()
    out = []
    for b in bids:
        if b[0] not in seen:
            seen.add(b[0])
            out.append(b)
    return out

def auction_close(auction: list) -> list:
    """Settle: highest valid bidder wins, pays second-highest (or reserve if sole)."""
    phase = auction[3]
    if phase == 1:
        return auction                      # idempotent (AU.2.3 law)
    if phase == 2:
        raise ClosedErr("cannot close a cancelled auction")

    item, seller, reserve, _, bids, _, _ = auction
    latest = _latest_bid_per_bidder(bids)
    valid = [b for b in latest if b[1] >= reserve]          # D5: >= reserve

    if not valid:
        return [item, seller, reserve, 1, bids, 0, 0]       # no valid bids → no winner

    ordered = sorted(valid, key=lambda b: b[1], reverse=True)  # D3: stable sort
    winner, top_bid = ordered[0]
    price = ordered[1][1] if len(ordered) >= 2 else reserve    # Vickrey
    return [item, seller, reserve, 1, bids, winner, price]

# ---------------------------------------------------------------------------
# AU.2.4 auction_cancel — 0xA004
# ---------------------------------------------------------------------------

def auction_cancel(auction: list) -> list:
    """Void an open auction. Closed → error; already cancelled → identity."""
    phase = auction[3]
    if phase == 1:
        raise ClosedErr("cannot cancel a closed auction")
    if phase == 2:
        return auction                      # D7: idempotent
    return [auction[0], auction[1], auction[2], 2, auction[4], 0, 0]

# ---------------------------------------------------------------------------
# Self-check harness
# ---------------------------------------------------------------------------

_passed = 0
_failed = 0
_results = []

def check(name: str, expected, fn):
    """Run fn(); compare against expected. expected may be an exception type."""
    global _passed, _failed
    try:
        got = fn()
        if isinstance(expected, type) and issubclass(expected, BaseException):
            _failed += 1
            _results.append(f"FAIL  {name}: expected {expected.__name__}, got {got!r}")
        elif got == expected:
            _passed += 1
            _results.append(f"pass  {name}")
        else:
            _failed += 1
            _results.append(f"FAIL  {name}: expected {expected!r}, got {got!r}")
    except Exception as e:
        if isinstance(expected, type) and issubclass(expected, BaseException) and isinstance(e, expected):
            _passed += 1
            _results.append(f"pass  {name} ({type(e).__name__})")
        else:
            _failed += 1
            _results.append(f"FAIL  {name}: raised {type(e).__name__}({e}), expected {expected!r}")

def run_self_check() -> int:
    global _passed, _failed

    print("=" * 64)
    print("σLang AUCTION PROTOCOL — Implementation A self-check")
    print("Fingerprints: 0xA001 create · 0xA002 bid · 0xA003 close · 0xA004 cancel")
    print("=" * 64)

    # ---- AU.2.1 auction_create (3 tests) ---------------------------------
    print("\n[AU.2.1] auction_create")
    check("create(101,1,50) basic",
          [101, 1, 50, 0, [], 0, 0],
          lambda: auction_create(101, 1, 50))
    check("create(202,2,0) zero reserve",
          [202, 2, 0, 0, [], 0, 0],
          lambda: auction_create(202, 2, 0))
    check("create(303,3,-5) negative reserve -> ReserveErr",
          ReserveErr,
          lambda: auction_create(303, 3, -5))

    # ---- AU.2.2 bid (4 tests) --------------------------------------------
    print("\n[AU.2.2] bid")
    check("bid(create(101,1,50),7,80) single",
          [101, 1, 50, 0, [[7, 80]], 0, 0],
          lambda: bid(auction_create(101, 1, 50), 7, 80))
    check("two bids, newest first",
          [101, 1, 50, 0, [[3, 100], [7, 80]], 0, 0],
          lambda: bid(bid(auction_create(101, 1, 50), 7, 80), 3, 100))
    check("bid negative amount -> BidAmountErr",
          BidAmountErr,
          lambda: bid(auction_create(101, 1, 50), 7, -10))
    check("bid on closed auction -> ClosedErr",
          ClosedErr,
          lambda: bid(auction_close(auction_create(101, 1, 50)), 5, 60))

    # ---- AU.2.3 auction_close (8 tests) ----------------------------------
    print("\n[AU.2.3] auction_close")
    a = bid(bid(auction_create(101, 1, 50), 7, 80), 3, 100)
    check("T1 two bids above reserve -> winner=3 price=80",
          [101, 1, 50, 1, [[3, 100], [7, 80]], 3, 80],
          lambda: auction_close(a))

    a3 = [[1, 200], [2, 150], [3, 100]]
    check("T2 three bids -> winner=1 price=150",
          [101, 1, 50, 1, a3, 1, 150],
          lambda: auction_close([101, 1, 50, 0, a3, 0, 0]))

    a1 = [[5, 70]]
    check("T3 sole bid above reserve -> winner=5 price=50 (reserve)",
          [101, 1, 50, 1, a1, 5, 50],
          lambda: auction_close([101, 1, 50, 0, a1, 0, 0]))

    a_none = [[1, 30], [2, 20]]
    check("T4 no bids above reserve -> winner=0 price=0",
          [101, 1, 50, 1, a_none, 0, 0],
          lambda: auction_close([101, 1, 50, 0, a_none, 0, 0]))

    check("T5 zero bids -> winner=0 price=0",
          [101, 1, 50, 1, [], 0, 0],
          lambda: auction_close(auction_create(101, 1, 50)))

    a_tie = [[1, 100], [2, 100], [3, 80]]
    check("T6 tie at top -> winner=1 price=100 (stable sort)",
          [101, 1, 50, 1, a_tie, 1, 100],
          lambda: auction_close([101, 1, 50, 0, a_tie, 0, 0]))

    a_res = [[4, 50]]
    check("T7 bid exactly at reserve -> winner=4 price=50",
          [101, 1, 50, 1, a_res, 4, 50],
          lambda: auction_close([101, 1, 50, 0, a_res, 0, 0]))

    closed = auction_close(auction_create(101, 1, 50))
    check("T8 close already-closed -> identity (idempotent)",
          closed,
          lambda: auction_close(closed))

    # ---- AU.2.4 auction_cancel (2 tests) ---------------------------------
    print("\n[AU.2.4] auction_cancel")
    check("cancel(create(101,1,50)) -> phase=2",
          [101, 1, 50, 2, [], 0, 0],
          lambda: auction_cancel(auction_create(101, 1, 50)))
    check("cancel closed auction -> ClosedErr",
          ClosedErr,
          lambda: auction_cancel(closed))

    # ---- AU.4 Composite scenario (1 test) --------------------------------
    print("\n[AU.4] composite lifecycle")
    def composite():
        x = auction_create(101, 1, 50)
        x = bid(x, 7, 80)
        x = bid(x, 3, 100)
        x = bid(x, 5, 60)
        return auction_close(x)
    check("3 bidders r=50 -> winner=3 price=80",
          [101, 1, 50, 1, [[3, 100], [5, 60], [7, 80]], 3, 80],
          composite)

    # ---- Extra edge cases (task key rules) -------------------------------
    print("\n[extra] edge cases")
    # E1: same bidder multiple bids, last one counts (7 bids 100 then 30)
    def e1():
        x = auction_create(101, 1, 50)
        x = bid(x, 7, 100)
        x = bid(x, 7, 30)      # 7's last bid is 30 (below reserve)
        x = bid(x, 3, 50)      # newest first: [[3,50],[7,30],[7,100]]
        return auction_close(x)
    check("E1 same-bidder last-bid-counts -> winner=3 price=50 (stale 100 ignored)",
          [101, 1, 50, 1, [[3, 50], [7, 30], [7, 100]], 3, 50],
          e1)

    # E2: bid on cancelled auction -> ClosedErr
    cancelled = auction_cancel(auction_create(101, 1, 50))
    check("E2 bid on cancelled auction -> ClosedErr",
          ClosedErr,
          lambda: bid(cancelled, 5, 60))

    # E3: close on cancelled auction -> ClosedErr
    check("E3 close cancelled auction -> ClosedErr",
          ClosedErr,
          lambda: auction_close(cancelled))

    # E4: cancel already-cancelled -> identity
    check("E4 cancel cancelled auction -> identity",
          cancelled,
          lambda: auction_cancel(cancelled))

    # E5: reserve=0, bid of 0 counts as valid
    def e5():
        x = auction_create(202, 2, 0)
        x = bid(x, 9, 0)
        return auction_close(x)
    check("E5 reserve=0 bid=0 valid -> winner=9 price=0",
          [202, 2, 0, 1, [[9, 0]], 9, 0],
          e5)

    # E6: reserve=0, sole bid above zero -> pays reserve (0)
    def e6():
        x = auction_create(202, 2, 0)
        x = bid(x, 9, 5)
        return auction_close(x)
    check("E6 reserve=0 sole bid 5 -> winner=9 price=0",
          [202, 2, 0, 1, [[9, 5]], 9, 0],
          e6)

    # E7: tie at top with same-bidder dedup interplay (stable, newest-first)
    def e7():
        x = auction_create(101, 1, 50)
        x = bid(x, 1, 100)
        x = bid(x, 2, 100)
        return auction_close(x)
    check("E7 tie with 2 bidders -> winner=2 price=100 (first in list)",
          [101, 1, 50, 1, [[2, 100], [1, 100]], 2, 100],
          e7)

    # ---- Report -----------------------------------------------------------
    total = _passed + _failed
    print("\n" + "-" * 64)
    for r in _results:
        print(r)
    print("-" * 64)
    print(f"AUCTION SELF-CHECK: {_passed}/{total} passed")
    print(f"AGENT_A COMPLETE: {_passed}/{total} passed")
    return 0 if _failed == 0 else 1

if __name__ == "__main__":
    sys.exit(run_self_check())
