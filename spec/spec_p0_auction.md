# §AU — Auction Protocol: Sealed-Bid Second-Price (Vickrey)

> **Status**: Experimental — Protocol implementation consistency benchmark
> **Depends**: core@1.0, error@1.0, math.base@1.0
> **Fingerprint prefix**: `0xA000`–`0xA0FF`
> **Motivation**: A sealed-bid second-price (Vickrey) auction — the classic
> mechanism where the highest bidder wins but pays the *second-highest* bid.
> This is a canonical test of semantic consistency because the payout logic
> is counterintuitive and easy to get wrong.

---

## AU.1 Core Types

```md
ItemId   : Type ≝ ℕ                       # item identity
Bidder   : Type ≝ ℕ                       # bidder identity (ℕ > 0; 0 = unset)
Amount   : Type ≝ ℕ                       # bid amount, must be ≥ 0
Phase    : Type ≝ ℕ                       # 0=open · 1=closed· 2=cancelled
Bid      : List⟨ℕ⟩                        # [bidder_id, amount]
Auction  : List⟨Any⟩                      # [item_id, seller_id, reserve, phase, [Bid...], winner, price]
                                          #  0        1          2       3      4          5       6
```

**Auction 状态机**:

```md
0 = open     (auction_create)        — accepting bids
1 = closed   (auction_close)         — winner determined, payout locked
2 = cancelled (auction_cancel)       — no winner, void
```

---

## AU.2 Operations

### AU.2.1 auction_create — Create Auction

```md
auction_create : ℕ × ℕ × ℕ → Auction
Fingerprint: 0xA001
Definition: auction_create(item, seller, reserve) ≡ [item, seller, reserve, 0, [], 0, 0]
            # phase=0 (open), no bids, winner=0, price=0
```

**Laws**

```md
∀ a . index(auction_create(a, s, r), 3) ≡ 0     # freshly created auction is open
∀ a . index(auction_create(a, s, r), 4) ≡ []    # empty bid list
∀ a . index(auction_create(a, s, r), 5) ≡ 0     # no winner yet
```

**Tests**

| Input | Output |
|-------|--------|
| auction_create(101, 1, 50) | [101,1,50,0,[],0,0] |
| auction_create(202, 2, 0) | [202,2,0,0,[],0,0] |
| auction_create(303, 3, -5) | ⊥ ReserveErr |

### AU.2.2 bid — Place a Sealed Bid

```md
bid : Auction × ℕ × ℕ → Auction
Fingerprint: 0xA002
Definition: bid([i, s, r, 0, bids, 0, 0], b, amt) ≡ [i, s, r, 0, bids ⊕ [[b, amt]], 0, 0]
            # only in open phase; one bidder can bid multiple times (last one counts)
            Precondition: phase ≡ 0 ∧ amt ≥ 0
```

**Laws**

```md
∀ a b m . phase(a) ≡ 0 ⇒ index(bid(a, b, m), 3) ≡ 0       # bid doesn't change phase
∀ a . phase(a) ≡ 1 ⇒ bid(a, b, m) ≡ ⊥ ClosedErr           # cannot bid on closed auction
```

**Tests**

| Input | Output |
|-------|--------|
| bid(auction_create(101, 1, 50), 7, 80) | [101,1,50,0,[[7,80]],0,0] |
| bid(bid(auction_create(101, 1, 50), 7, 80), 3, 100) | [101,1,50,0,[[3,100],[7,80]],0,0] |
| bid(auction_create(101, 1, 50), 7, -10) | ⊥ BidAmountErr |
| bid(closed_auction, 5, 60) | ⊥ ClosedErr |

### AU.2.3 auction_close — Close and Settle

```md
auction_close : Auction → Auction
Fingerprint: 0xA003
Definition:
  auction_close([i, s, r, 0, bids, 0, 0]) ≡
    let valid_bids = filter(lambda b: b[1] ≥ r, bids) in
    if valid_bids ≡ []  then [i, s, r, 1, bids, 0, 0]           -- no valid bids: closed, no winner
    else
      let sorted = sort_by_amount_desc(valid_bids) in
      let (winner, top_bid) = sorted[0] in
      let second_price = if len(sorted) ≥ 2 then sorted[1][1] else r in
      [i, s, r, 1, bids, winner, second_price]                   -- Vickrey: winner pays 2nd price
```

**KEY RULE (Vickrey)**: The winner is the highest bidder, but the price the winner pays
is the *second-highest* bid. If there is only one valid bid, the winner pays the reserve price.

**Laws**

```md
# Phase transition
∀ a . phase(a) ≡ 0 ⇒ phase(auction_close(a)) ≡ 1

# No valid bids above reserve → no winner
∀ a . phase(a) ≡ 0 ∧ all_valid_below_reserve(a) ⇒ winner(auction_close(a)) ≡ 0

# Winner is highest bidder
∀ a . phase(a) ≡ 0 ∧ has_valid_bids(a) ⇒ winner(auction_close(a)) ≡ top_bidder(a)

# Vickrey pricing: winner pays second-highest price (or reserve if sole bidder)
∀ a . phase(a) ≡ 0 ∧ len(valid_bids(a)) ≥ 2 ⇒
    price(auction_close(a)) ≡ second_highest_bid(a)
∀ a . phase(a) ≡ 0 ∧ len(valid_bids(a)) ≡ 1 ⇒
    price(auction_close(a)) ≡ reserve(a)

# Price never exceeds winner's bid
∀ a . phase(a) ≡ 0 ∧ has_valid_bids(a) ⇒
    price(auction_close(a)) ≤ winner_bid(a)

# Idempotent: closing an already-closed auction returns same result
∀ a . phase(a) ≡ 1 ⇒ auction_close(a) ≡ a

# Seller payout: seller receives the winner's payment
∀ a . phase(a) ≡ 0 ∧ has_valid_bids(a) ⇒
    seller_proceeds(auction_close(a)) ≡ price(auction_close(a))
```

**Tests**

| # | Scenario | Input | Output (winner, price) |
|---|----------|-------|----------------------|
| 1 | Two bids, both above reserve | bids: [[3,100],[7,80]] r=50 | winner=3, price=80 |
| 2 | Three bids | bids: [[1,200],[2,150],[3,100]] r=50 | winner=1, price=150 |
| 3 | Sole bid above reserve | bids: [[5,70]] r=50 | winner=5, price=50 |
| 4 | No bids above reserve | bids: [[1,30],[2,20]] r=50 | winner=0, price=0 |
| 5 | Zero bids | bids: [] r=50 | winner=0, price=0 |
| 6 | Tie at top | bids: [[1,100],[2,100],[3,80]] r=50 | winner=1, price=100 |
| 7 | Bid exactly at reserve | bids: [[4,50]] r=50 | winner=4, price=50 |
| 8 | Already closed | phase=1 | ⊥ ClosedErr (or identity) |

### AU.2.4 auction_cancel — Cancel Auction

```md
auction_cancel : Auction → Auction
Fingerprint: 0xA004
Definition: auction_cancel([i, s, r, 0, bids, 0, 0]) ≡ [i, s, r, 2, bids, 0, 0]
            # only cancellable in open phase
```

**Laws**

```md
∀ a . phase(a) ≡ 0 ⇒ phase(auction_cancel(a)) ≡ 2
∀ a . phase(a) ≡ 1 ⇒ auction_cancel(a) ≡ ⊥ ClosedErr
```

**Tests**

| Input | Output |
|-------|--------|
| auction_cancel(auction_create(101, 1, 50)) | [101,1,50,2,[],0,0] |
| auction_cancel(closed_auction) | ⊥ ClosedErr |

---

## AU.3 Design Decisions (Intentional Ambiguities for Cross-Implementation Test)

The spec is intentionally NOT fully determinate on these points — different
implementers may make different reasonable choices:

1. **Sort stability for ties**: When two bids have the same amount, which bidder
   is declared winner? The spec says "first in sorted order" but doesn't define
   sort stability.

2. **Same-bidder multiple bids**: "last one counts" — but is it last by insertion
   order or last by amount? The spec says insertion order.

3. **Data representation**: Auction as `List⟨Any⟩` allows different internal
   representations — some may use dicts, some tuples, some classes.

4. **Error handling style**: Some implementations may use exceptions, some
   may use `Result` monads, some may return error strings.

5. **Reserve price at zero**: `bids with amount >= reserve` — when reserve=0,
   does a bid of 0 count as valid? The spec says "yes" (amount ≥ reserve).

These are intentional — the point of independent implementation is to see
where reasonable engineers diverge when working from the same spec.

---

## AU.4 Composite Scenario (Full Auction Lifecycle)

```md
# Scenario: 3 bidders, reserve=50
let a = auction_create(101, 1, 50)       # → [101,1,50,0,[],0,0]
let a = bid(a, 7, 80)                    # → [...,[[7,80]],...]
let a = bid(a, 3, 100)                   # → [...,[[3,100],[7,80]],...]
let a = bid(a, 5, 60)                    # → [...,[[3,100],[5,60],[7,80]],...]
let a = auction_close(a)                 # EXPECT: winner=3, price=80 (second was 80)
```

---

## AU.5 Verifier Implementation Requirements

Each verifier must:

1. Implement all 4 operations (`auction_create`, `bid`, `auction_close`, `auction_cancel`)
2. Include self-tests that cover all 8 test scenarios in AU.2.3
3. Return a structured verdict (pass/fail count)
4. Run as a single-file script: `python3 impl/python/sigma_auction.py`
5. Print clearly formatted test results

**Verdict format** (output at end of run):
```
AUCTION SELF-CHECK: N/M passed
```

Exit code 0 = all passed, 1 = any failure.
