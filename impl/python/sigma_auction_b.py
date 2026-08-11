#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ΣLang §AU — Auction Protocol (Sealed-Bid Second-Price / Vickrey)
Independent Implementation B — single-file verifier.

Fingerprints:
  auction_create : 0xA001
  bid            : 0xA002
  auction_close  : 0xA003
  auction_cancel : 0xA004

Auction representation (AU.1): plain 7-element list
  [item_id, seller_id, reserve, phase, bids, winner, price]
  phase: 0 = open · 1 = closed · 2 = cancelled
  bids : List of [bidder_id, amount], each bidder appears at most once,
         maintained sorted by bidder_id ascending (the canonical order shown in
         every spec example — AU.2.2 test 2 and AU.4 require bidder_id order,
         not raw insertion order).

Design decisions (AU.3 intentional ambiguities, as implemented here):
  1. Tie at top amount -> first bidder in bidder_id order wins (stable sort).
  2. Same bidder re-bids -> the LAST bid (insertion order) replaces the earlier
     one in place, keeping the bidder's position ("last one counts").
  3. Representation: plain 7-element list per AU.1.
  4. Errors: exceptions (⊥) — ReserveErr / BidAmountErr / ClosedErr.
  5. Reserve = 0 -> a bid of 0 counts as valid (amount >= reserve).
  6. auction_close on a closed/cancelled auction -> idempotent identity
     (AU.2.3 law; test 8 explicitly allows "ClosedErr (or identity)").
  7. auction_cancel on closed -> ClosedErr; on cancelled -> identity.
  8. bid on closed/cancelled -> ClosedErr.

Run:  python3 sigma_auction_b.py
Exit: 0 = all passed, 1 = any failure.
"""

import random
import sys


# ---------------------------------------------------------------------------
# Errors (⊥)
# ---------------------------------------------------------------------------

class AuctionError(Exception):
    """Base protocol error."""


class ReserveErr(AuctionError):
    """reserve must be >= 0."""


class BidAmountErr(AuctionError):
    """bid amount must be >= 0."""


class ClosedErr(AuctionError):
    """operation forbidden on a closed/cancelled auction."""


# ---------------------------------------------------------------------------
# Core operations (functional: never mutate the input auction)
# ---------------------------------------------------------------------------

PHASE_OPEN = 0
PHASE_CLOSED = 1
PHASE_CANCELLED = 2


def _fresh(auction):
    """Structural copy of an auction."""
    return [auction[0], auction[1], auction[2], auction[3],
            list(auction[4]), auction[5], auction[6]]


def auction_create(item, seller, reserve):
    """0xA001 — [item, seller, reserve, 0(open), [], 0, 0]; reserve < 0 -> ReserveErr."""
    if reserve < 0:
        raise ReserveErr("reserve must be >= 0, got %r" % (reserve,))
    return [item, seller, reserve, PHASE_OPEN, [], 0, 0]


def _insert_bid(bids, new_bid):
    """Insert [bidder, amount] keeping bidder_id ascending order; a re-bid
    replaces the bidder's previous entry in place (last bid by insertion
    order counts, AU.3.2)."""
    out = [list(b) for b in bids]
    for i, b in enumerate(out):
        if b[0] == new_bid[0]:
            out[i] = new_bid
            return out
    pos = 0
    while pos < len(out) and out[pos][0] < new_bid[0]:
        pos += 1
    out.insert(pos, new_bid)
    return out


def bid(auction, bidder, amount):
    """0xA002 — record a sealed bid; open phase only; amount >= 0."""
    if auction[3] != PHASE_OPEN:
        raise ClosedErr("cannot bid on a non-open auction")
    if amount < 0:
        raise BidAmountErr("bid amount must be >= 0, got %r" % (amount,))
    return [auction[0], auction[1], auction[2], PHASE_OPEN,
            _insert_bid(auction[4], [bidder, amount]), 0, 0]


def auction_close(auction):
    """0xA003 — Vickrey settlement.

    winner = highest valid bid (amount >= reserve); price = second-highest
    valid bid, or the reserve when only one valid bid exists; no valid bids
    -> winner 0 / price 0. Closing a closed/cancelled auction is idempotent.
    """
    if auction[3] != PHASE_OPEN:
        return _fresh(auction)  # idempotent (AU.2.3 law; test 8 permits identity)
    i, s, r, _, bids, _, _ = auction
    valid = [b for b in bids if b[1] >= r]
    if not valid:
        return [i, s, r, PHASE_CLOSED, list(bids), 0, 0]
    valid.sort(key=lambda b: b[1], reverse=True)  # stable -> ties keep bidder_id order
    winner = valid[0][0]
    price = valid[1][1] if len(valid) >= 2 else r
    return [i, s, r, PHASE_CLOSED, list(bids), winner, price]


def auction_cancel(auction):
    """0xA004 — open -> cancelled (void, no winner); closed -> ClosedErr;
    already cancelled -> identity."""
    if auction[3] == PHASE_CLOSED:
        raise ClosedErr("cannot cancel a closed auction")
    if auction[3] == PHASE_CANCELLED:
        return _fresh(auction)
    return [auction[0], auction[1], auction[2], PHASE_CANCELLED,
            list(auction[4]), 0, 0]


# ---------------------------------------------------------------------------
# Self-check harness
# ---------------------------------------------------------------------------

PASSED = 0
TOTAL = 0


def check(name, expected, actual):
    global PASSED, TOTAL
    TOTAL += 1
    if expected == actual:
        PASSED += 1
        print("  [PASS] %s" % name)
    else:
        print("  [FAIL] %s\n         expected: %r\n         actual:   %r" % (name, expected, actual))


def check_err(name, exc, fn):
    global PASSED, TOTAL
    TOTAL += 1
    try:
        fn()
    except exc:
        PASSED += 1
        print("  [PASS] %s (raised %s)" % (name, exc.__name__))
    except Exception as e:  # noqa: BLE001
        print("  [FAIL] %s: expected %s, got %s (%s)" % (name, exc.__name__, type(e).__name__, e))
    else:
        print("  [FAIL] %s: expected %s, but no error raised" % (name, exc.__name__))


def make(reserve, bid_list):
    """Build an auction by bidding in the given order."""
    a = auction_create(101, 1, reserve)
    for b, m in bid_list:
        a = bid(a, b, m)
    return a


# ---------------------------------------------------------------------------
# Test sections
# ---------------------------------------------------------------------------

def run_au21():
    print("AU.2.1 auction_create")
    check("create(101, 1, 50)",
          [101, 1, 50, 0, [], 0, 0], auction_create(101, 1, 50))
    check("create(202, 2, 0)  (zero reserve)",
          [202, 2, 0, 0, [], 0, 0], auction_create(202, 2, 0))
    check_err("create(303, 3, -5) -> ReserveErr",
              ReserveErr, lambda: auction_create(303, 3, -5))


def run_au22():
    print("AU.2.2 bid")
    check("bid(create(101,1,50), 7, 80)",
          [101, 1, 50, 0, [[7, 80]], 0, 0], bid(auction_create(101, 1, 50), 7, 80))
    check("bid(bid(create, 7, 80), 3, 100)  (bidder_id order)",
          [101, 1, 50, 0, [[3, 100], [7, 80]], 0, 0],
          bid(bid(auction_create(101, 1, 50), 7, 80), 3, 100))
    check_err("bid(create, 7, -10) -> BidAmountErr",
              BidAmountErr, lambda: bid(auction_create(101, 1, 50), 7, -10))
    closed = auction_close(make(50, [(3, 100), (7, 80)]))
    check_err("bid(closed_auction, 5, 60) -> ClosedErr",
              ClosedErr, lambda: bid(closed, 5, 60))


def run_au23():
    print("AU.2.3 auction_close (all 8 scenarios)")
    check("S1 two bids above reserve -> winner=3, price=80",
          [101, 1, 50, 1, [[3, 100], [7, 80]], 3, 80],
          auction_close(make(50, [(3, 100), (7, 80)])))
    check("S2 three bids -> winner=1, price=150",
          [101, 1, 50, 1, [[1, 200], [2, 150], [3, 100]], 1, 150],
          auction_close(make(50, [(1, 200), (2, 150), (3, 100)])))
    check("S3 sole bid above reserve -> winner=5, price=50 (reserve)",
          [101, 1, 50, 1, [[5, 70]], 5, 50],
          auction_close(make(50, [(5, 70)])))
    check("S4 no bids above reserve -> winner=0, price=0",
          [101, 1, 50, 1, [[1, 30], [2, 20]], 0, 0],
          auction_close(make(50, [(1, 30), (2, 20)])))
    check("S5 zero bids -> winner=0, price=0",
          [101, 1, 50, 1, [], 0, 0],
          auction_close(make(50, [])))
    check("S6 tie at top -> winner=1, price=100 (2nd price)",
          [101, 1, 50, 1, [[1, 100], [2, 100], [3, 80]], 1, 100],
          auction_close(make(50, [(1, 100), (2, 100), (3, 80)])))
    check("S7 bid exactly at reserve -> winner=4, price=50",
          [101, 1, 50, 1, [[4, 50]], 4, 50],
          auction_close(make(50, [(4, 50)])))
    closed = auction_close(make(50, [(3, 100), (7, 80)]))
    check("S8 already closed -> identity (idempotent)",
          closed, auction_close(closed))


def run_au24():
    print("AU.2.4 auction_cancel")
    check("cancel(create(101,1,50))",
          [101, 1, 50, 2, [], 0, 0], auction_cancel(auction_create(101, 1, 50)))
    closed = auction_close(make(50, [(3, 100), (7, 80)]))
    check_err("cancel(closed_auction) -> ClosedErr",
              ClosedErr, lambda: auction_cancel(closed))


def run_au4():
    print("AU.4 composite scenario (full lifecycle)")
    a = auction_create(101, 1, 50)
    check("AU.4 step1 create", [101, 1, 50, 0, [], 0, 0], a)
    a = bid(a, 7, 80)
    check("AU.4 step2 bid 7/80", [101, 1, 50, 0, [[7, 80]], 0, 0], a)
    a = bid(a, 3, 100)
    check("AU.4 step3 bid 3/100", [101, 1, 50, 0, [[3, 100], [7, 80]], 0, 0], a)
    a = bid(a, 5, 60)
    check("AU.4 step4 bid 5/60", [101, 1, 50, 0, [[3, 100], [5, 60], [7, 80]], 0, 0], a)
    c = auction_close(a)
    check("AU.4 step5 close -> winner=3, price=80",
          [101, 1, 50, 1, [[3, 100], [5, 60], [7, 80]], 3, 80], c)


def run_extras():
    print("AU.3 design-decision / law extras")
    check("same bidder re-bids, last counts (sole bidder)",
          [101, 1, 50, 1, [[7, 60]], 7, 50],
          auction_close(make(50, [(7, 80), (7, 60)])))
    check("same bidder re-bids, last counts (mixed)",
          [101, 1, 50, 1, [[3, 100], [7, 60]], 3, 60],
          auction_close(make(50, [(7, 80), (3, 100), (7, 60)])))
    check("reserve=0: bid of 0 is a valid bid",
          [101, 1, 0, 1, [[7, 0]], 7, 0],
          auction_close(make(0, [(7, 0)])))
    check("cancel keeps bid history, voids winner",
          [101, 1, 50, 2, [[7, 80]], 0, 0],
          auction_cancel(make(50, [(7, 80)])))
    cancelled = auction_cancel(make(50, [(7, 80)]))
    check_err("bid on cancelled auction -> ClosedErr",
              ClosedErr, lambda: bid(cancelled, 5, 60))
    check("cancel on cancelled -> identity",
          cancelled, auction_cancel(cancelled))
    check("close on cancelled -> identity",
          cancelled, auction_close(cancelled))
    # price never exceeds the winning bid (AU.2.3 law), spot check on S2
    s2 = auction_close(make(50, [(1, 200), (2, 150), (3, 100)]))
    assert s2[6] <= 200


def run_property():
    global PASSED, TOTAL
    TOTAL += 1
    rng = random.Random(42)
    try:
        for trial in range(300):
            r = rng.randint(0, 100)
            a = auction_create(101, 1, r)
            for _ in range(rng.randint(0, 10)):
                a = bid(a, rng.randint(1, 6), rng.randint(0, 120))
            c = auction_close(a)
            assert c[3] == PHASE_CLOSED, "trial %d: phase must become closed" % trial
            assert c[4] == a[4], "trial %d: bid history must be preserved" % trial
            assert auction_close(c) == c, "trial %d: close must be idempotent" % trial
            last = {b[0]: b[1] for b in a[4]}  # one entry per bidder
            valid = {b: m for b, m in last.items() if m >= r}
            if not valid:
                assert c[5] == 0 and c[6] == 0, \
                    "trial %d: no valid bids -> winner 0, price 0" % trial
            else:
                top = max(valid.values())
                winner = min(b for b, m in valid.items() if m == top)
                vals = sorted(valid.values(), reverse=True)
                price = vals[1] if len(vals) >= 2 else r
                assert c[5] == winner, "trial %d: winner mismatch" % trial
                assert c[6] == price, "trial %d: Vickrey price mismatch" % trial
                assert c[6] <= top, "trial %d: price exceeds winning bid" % trial
    except AssertionError as e:
        print("  [FAIL] property trials: %s" % e)
    else:
        PASSED += 1
        print("  [PASS] 300 randomized property/law trials (Vickrey pricing, phase, idempotence)")


def main():
    run_au21()
    run_au22()
    run_au23()
    run_au24()
    run_au4()
    run_extras()
    run_property()
    print("")
    print("AUCTION SELF-CHECK: %d/%d passed" % (PASSED, TOTAL))
    print("AGENT_B COMPLETE: %d/%d passed" % (PASSED, TOTAL))
    return 0 if PASSED == TOTAL else 1


if __name__ == "__main__":
    sys.exit(main())
