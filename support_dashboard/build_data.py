"""Build the dashboard dataset from the figures pulled out of Commslayer.

Every number in OUT comes from a Commslayer report or list call made on
2026-08-15 (see data/SOURCES.md for the call log). Nothing here is modelled or
estimated; where a figure could not be retrieved it is None and the dashboard
says so rather than filling the gap.
"""

import json
import pathlib

HERE = pathlib.Path(__file__).parent
CUR = ("2026-07-17", "2026-08-15")
PREV = ("2026-06-17", "2026-07-16")

# The unified issue taxonomy. Each store's contact reasons are different trees
# (Commslayer derives them per-account from the conversation text), so every
# leaf is mapped onto this shared set. Composite reasons are filed under their
# leading term, e.g. "Item fit and damage issue" -> Sizing & Fit.
CATEGORIES = [
    "Sizing & Fit",
    "Order Status & Changes",
    "Product Question",
    "Replacement / Exchange",
    "Shipping Delay",
    "Refund",
    "Cancellation",
    "Tracking & Address",
    "Billing & Payments",
    "Unauthorised Charge / Subscription",
    "Product Quality",
    "Trust / Scam Concern",
    "Repeat Contact (chasing us)",
    "Order Not Received",
    "Wrong Item",
    "Missing Item",
    "Feedback",
    "Other / Non-customer",
]

# ---------------------------------------------------------------------------
# Mary's Tanks - leaf -> category (full tree, both periods + 4 weeks)
# ---------------------------------------------------------------------------
MT_MAP = {
    "Size exchange": "Sizing & Fit",
    "Size and address change": "Sizing & Fit",
    "Product size and billing error": "Sizing & Fit",
    "Return and replacement request": "Replacement / Exchange",
    "Returns and exchanges (unspecified)": "Replacement / Exchange",
    "Return status": "Replacement / Exchange",
    "Return and refund request": "Refund",
    "Refund request": "Refund",
    "Refund confirmation": "Refund",
    "Damaged and incorrect item": "Product Quality",
    "Damaged item": "Product Quality",
    "Product issue": "Product Quality",
    "General complaint": "Product Quality",
    "Advertising complaint": "Product Quality",
    "Delayed": "Shipping Delay",
    "Shipping (unspecified)": "Shipping Delay",
    "Tracking": "Tracking & Address",
    "Wrong address": "Tracking & Address",
    "Provide address details": "Tracking & Address",
    "Lost package": "Order Not Received",
    "Order scam accusation": "Trust / Scam Concern",
    "Wrong item": "Wrong Item",
    "Missing product": "Missing Item",
    "Cancel order": "Cancellation",
    "Cancel subscription": "Cancellation",
    "Order inquiry (unspecified)": "Order Status & Changes",
    "Order inquiry about tanks": "Order Status & Changes",
    "Order confirmation": "Order Status & Changes",
    "Order confusion": "Order Status & Changes",
    "Order details inquiry": "Order Status & Changes",
    "Order issue (unspecified)": "Order Status & Changes",
    "General inquiry about order": "Order Status & Changes",
    "Cart not found": "Order Status & Changes",
    "Edit order (unspecified)": "Order Status & Changes",
    "Product modification request": "Order Status & Changes",
    "Follow-up on previous contact": "Repeat Contact (chasing us)",
    "Product details (sizing/materials)": "Product Question",
    "Availability": "Product Question",
    "Product and shipping inquiry": "Product Question",
    "Retail outlet inquiry": "Product Question",
    "Post-mastectomy product inquiry": "Product Question",
    "Product question (unspecified)": "Product Question",
    "Product inquiry (top level)": "Product Question",
    "Product suitability inquiry": "Product Question",
    "Product inquiry (under order)": "Product Question",
    "Screenshot inquiry": "Product Question",
    "Product image inquiry": "Product Question",
    "Billing (unspecified)": "Billing & Payments",
    "Invoice inquiry": "Billing & Payments",
    "Payment confirmation": "Billing & Payments",
    "Provide bank details": "Billing & Payments",
    "Payment method discrepancy": "Billing & Payments",
    "Payment method inquiry": "Billing & Payments",
    "Currency inquiry": "Billing & Payments",
    "Credit usage inquiry": "Billing & Payments",
    "Discount code": "Billing & Payments",
    "Payment failed": "Billing & Payments",
    "Payment by phone inquiry": "Billing & Payments",
    "Statement inquiry": "Billing & Payments",
    "Chargeback inquiry": "Billing & Payments",
    "Order feedback": "Feedback",
    "Survey response": "Feedback",
}
MT_OTHER = [
    "Website technical issue", "Personal circumstances", "General greeting",
    "Unclear inquiry", "Attention to Alex", "General inquiry (misc)",
    "General location inquiry", "Irrelevant subject line",
    "Promotional offer inquiry", "Flash sale inquiry",
    "Update contact information", "Unsubscribe request",
    "Meta verification inquiry", "Out of office notification",
    "Inquiry about text messages", "Beta test invitation",
    "Business opportunity inquiry", "Email address inquiry",
    "Email addition request", "General support request",
    "Connect with team member", "Contact information inquiry",
    "Password reset inquiry", "Performance optimization inquiry",
    "Request to speak with representative", "Webinar registration inquiry",
    "Trademark violation appeal",
]
for _leaf in MT_OTHER:
    MT_MAP[_leaf] = "Other / Non-customer"

# ---------------------------------------------------------------------------
# The other four stores - current period only (leaf: [category, count])
# ---------------------------------------------------------------------------
MAGGIES = {
    "Size exchange": ("Sizing & Fit", 2749),
    "Item fit and damage issue": ("Sizing & Fit", 903),
    "Item size and refund request": ("Sizing & Fit", 378),
    "Order status and size exchange": ("Sizing & Fit", 1),
    "Returns & exchanges (unspecified)": ("Replacement / Exchange", 708),
    "Return request": ("Replacement / Exchange", 383),
    "Item replacement request": ("Replacement / Exchange", 106),
    "Return status": ("Replacement / Exchange", 24),
    "Refund request": ("Refund", 731),
    "Order status and refund": ("Refund", 1),
    "Order status inquiry": ("Order Status & Changes", 2835),
    "Order confirmation": ("Order Status & Changes", 805),
    "Edit order": ("Order Status & Changes", 637),
    "Order inquiry": ("Order Status & Changes", 289),
    "Order issue (unspecified)": ("Order Status & Changes", 37),
    "Proceed with order": ("Order Status & Changes", 12),
    "Order modification and delay": ("Order Status & Changes", 7),
    "Order status and product inquiry": ("Order Status & Changes", 3),
    "Order confirmation acknowledgement": ("Order Status & Changes", 2),
    "Order cannot be completed": ("Order Status & Changes", 2),
    "Delayed": ("Shipping Delay", 1473),
    "Shipping (unspecified)": ("Shipping Delay", 398),
    "Tracking": ("Tracking & Address", 535),
    "Wrong address": ("Tracking & Address", 272),
    "Lost package": ("Order Not Received", 182),
    "Order scam accusation": ("Trust / Scam Concern", 279),
    "Wrong item": ("Wrong Item", 147),
    "Cancel order": ("Cancellation", 590),
    "Cancel and refund order": ("Cancellation", 321),
    "Order cancellation": ("Cancellation", 160),
    "Cancel subscription": ("Cancellation", 4),
    "Subscription (unspecified)": ("Cancellation", 3),
    "Follow-up on previous email": ("Repeat Contact (chasing us)", 400),
    "Negative feedback": ("Product Quality", 325),
    "Damaged item": ("Product Quality", 31),
    "Product details": ("Product Question", 1455),
    "Inquiry about tanks": ("Product Question", 418),
    "Shipping and return policy": ("Product Question", 118),
    "Manufacturing location inquiry": ("Product Question", 115),
    "Availability": ("Product Question", 94),
    "Product question (unspecified)": ("Product Question", 26),
    "Discount negotiation": ("Billing & Payments", 64),
    "Discount code": ("Billing & Payments", 54),
    "Invoice inquiry": ("Billing & Payments", 39),
    "Payment method inquiry": ("Billing & Payments", 25),
    "Credit card information request": ("Billing & Payments", 23),
    "Credit inquiry": ("Billing & Payments", 16),
    "Charge inquiry": ("Billing & Payments", 11),
    "Fee payment confirmation": ("Billing & Payments", 9),
    "Payment date inquiry": ("Billing & Payments", 8),
    "Payment confirmation": ("Billing & Payments", 6),
    "Payment failed": ("Billing & Payments", 6),
    "Billing (unspecified)": ("Billing & Payments", 5),
    "Payment confirmation inquiry": ("Billing & Payments", 4),
    "Credit card bill request": ("Billing & Payments", 1),
    "Positive feedback": ("Feedback", 107),
    "Changed mind": ("Other / Non-customer", 47),
    "General inquiry (unspecified)": ("Other / Non-customer", 162),
    "New customer inquiry": ("Other / Non-customer", 121),
    "Out of office reply": ("Other / Non-customer", 70),
    "Cart technical issue": ("Other / Non-customer", 65),
    "Greeting": ("Other / Non-customer", 57),
    "Location inquiry": ("Other / Non-customer", 36),
    "Billing address correction": ("Other / Non-customer", 27),
    "Gift card request": ("Other / Non-customer", 25),
    "Sales proposal": ("Other / Non-customer", 25),
    "Photo inquiry": ("Other / Non-customer", 19),
    "Remove from contact list": ("Other / Non-customer", 19),
    "Screenshot inquiry": ("Other / Non-customer", 13),
    "Website technical issue": ("Other / Non-customer", 12),
    "Marketing automation issue": ("Other / Non-customer", 10),
    "App beta testing invitation": ("Other / Non-customer", 9),
    "Request specific contact": ("Other / Non-customer", 8),
    "Email address correction": ("Other / Non-customer", 7),
    "Incomplete message": ("Other / Non-customer", 7),
    "New review notification": ("Other / Non-customer", 7),
    "Intellectual property verification": ("Other / Non-customer", 5),
    "Phone order inquiry": ("Other / Non-customer", 5),
    "Typo correction": ("Other / Non-customer", 5),
    "Coverage issue": ("Other / Non-customer", 5),
    "Concerning message received": ("Other / Non-customer", 4),
    "Content sharing": ("Other / Non-customer", 3),
    "Page suspension warning": ("Other / Non-customer", 3),
    "Account activation": ("Other / Non-customer", 5),
    "Customer name inquiry": ("Other / Non-customer", 2),
    "Future purchase inquiry": ("Other / Non-customer", 2),
    "New store inquiry": ("Other / Non-customer", 2),
    "General inquiry about getting started": ("Other / Non-customer", 2),
    "Misc single-count reasons": ("Other / Non-customer", 5),
}

LYNS = {
    "Size exchange": ("Sizing & Fit", 170),
    "Fit and refund inquiry": ("Sizing & Fit", 47),
    "Product quality and sizing issues": ("Product Quality", 129),
    "Product origin and quality": ("Product Quality", 3),
    "Product quality complaint": ("Product Quality", 1),
    "Returns & exchanges (unspecified)": ("Replacement / Exchange", 18),
    "Return status": ("Replacement / Exchange", 4),
    "Changed mind": ("Replacement / Exchange", 2),
    "Refund request": ("Refund", 62),
    "Edit order": ("Order Status & Changes", 38),
    "Order status inquiry": ("Order Status & Changes", 36),
    "Order confirmation acknowledgement": ("Order Status & Changes", 21),
    "Order confirmation inquiry": ("Order Status & Changes", 18),
    "Invoice payment confirmation": ("Order Status & Changes", 10),
    "Order issue (unspecified)": ("Order Status & Changes", 8),
    "New order placement": ("Order Status & Changes", 6),
    "Product maintenance inquiry": ("Order Status & Changes", 2),
    "General acknowledgement": ("Order Status & Changes", 1),
    "Delayed": ("Shipping Delay", 45),
    "Shipping (unspecified)": ("Shipping Delay", 28),
    "Tracking": ("Tracking & Address", 30),
    "Wrong address": ("Tracking & Address", 2),
    "Lost package": ("Order Not Received", 8),
    "Wrong item": ("Wrong Item", 2),
    "Missing promotional item": ("Missing Item", 4),
    "Cancel order": ("Cancellation", 16),
    "Unanswered emails": ("Repeat Contact (chasing us)", 42),
    "Product details": ("Product Question", 91),
    "Product question (unspecified)": ("Product Question", 8),
    "Availability": ("Product Question", 3),
    "Payment failed": ("Billing & Payments", 12),
    "Chargeback inquiry": ("Billing & Payments", 12),
    "Payment method inquiry": ("Billing & Payments", 7),
    "Invoice payment request": ("Billing & Payments", 4),
    "Unauthorized card usage": ("Billing & Payments", 2),
    "Discount code": ("Billing & Payments", 2),
    "Guarantee dispute": ("Billing & Payments", 2),
    "Claim submission": ("Billing & Payments", 2),
    "Billing (unspecified)": ("Billing & Payments", 1),
    "Payout speed inquiry": ("Billing & Payments", 1),
    "Positive feedback": ("Feedback", 6),
    "Store inquiry (unspecified)": ("Other / Non-customer", 17),
    "New customer inquiry": ("Other / Non-customer", 14),
    "Website technical issue": ("Other / Non-customer", 15),
    "Abusive customer message": ("Other / Non-customer", 8),
    "Test email": ("Other / Non-customer", 6),
    "Sales inquiry": ("Other / Non-customer", 3),
    "Unwanted marketing emails": ("Other / Non-customer", 3),
    "Direct message": ("Other / Non-customer", 2),
    "Out of office reply": ("Other / Non-customer", 2),
    "AI inquiry": ("Other / Non-customer", 2),
    "Misc single-count reasons": ("Other / Non-customer", 7),
}

MJ = {
    "Unauthorized charge cancellation": ("Unauthorised Charge / Subscription", 212),
    "Cancel subscription": ("Unauthorised Charge / Subscription", 209),
    "Refund and subscription cancellation": ("Unauthorised Charge / Subscription", 94),
    "Cancel order and subscription": ("Unauthorised Charge / Subscription", 33),
    "Cancel recurring charge": ("Unauthorised Charge / Subscription", 28),
    "Billing dispute and refund": ("Unauthorised Charge / Subscription", 19),
    "Unauthorized charge and subscription cancellation": ("Unauthorised Charge / Subscription", 10),
    "Account cancellation request": ("Unauthorised Charge / Subscription", 9),
    "Unauthorized charge and return": ("Unauthorised Charge / Subscription", 4),
    "Membership fee inquiry": ("Unauthorised Charge / Subscription", 1),
    "Damaged item and unauthorized charge": ("Unauthorised Charge / Subscription", 1),
    "Subscription (unspecified)": ("Unauthorised Charge / Subscription", 1),
    "Scam report": ("Trust / Scam Concern", 166),
    "Order status inquiry": ("Order Status & Changes", 159),
    "Order confirmation response": ("Order Status & Changes", 100),
    "Screenshot submission": ("Order Status & Changes", 10),
    "Edit order": ("Order Status & Changes", 6),
    "Order issue (unspecified)": ("Order Status & Changes", 4),
    "VIP portal location": ("Order Status & Changes", 1),
    "Cancel order": ("Cancellation", 58),
    "Refund request": ("Refund", 51),
    "General dissatisfaction": ("Product Quality", 56),
    "Damaged item": ("Product Quality", 6),
    "Size exchange": ("Sizing & Fit", 10),
    "Returns & exchanges (unspecified)": ("Replacement / Exchange", 3),
    "Changed mind": ("Replacement / Exchange", 1),
    "Tracking": ("Tracking & Address", 28),
    "Wrong address": ("Tracking & Address", 11),
    "Shipping (unspecified)": ("Shipping Delay", 20),
    "Delayed": ("Shipping Delay", 3),
    "Lost package": ("Order Not Received", 1),
    "Wrong item": ("Wrong Item", 6),
    "Product inquiry about rings": ("Product Question", 16),
    "Product details": ("Product Question", 3),
    "Product question (unspecified)": ("Product Question", 3),
    "Availability": ("Product Question", 2),
    "Pricing inquiry": ("Product Question", 2),
    "Payment option unavailable": ("Billing & Payments", 10),
    "Billing (unspecified)": ("Billing & Payments", 1),
    "Gratitude and personal story": ("Feedback", 77),
    "Free product request": ("Other / Non-customer", 56),
    "Greeting": ("Other / Non-customer", 42),
    "Shopify store audit": ("Other / Non-customer", 12),
    "Beta test invitation": ("Other / Non-customer", 11),
    "Collaboration proposal": ("Other / Non-customer", 11),
    "Sales territory inquiry": ("Other / Non-customer", 11),
    "Commission inquiry": ("Other / Non-customer", 10),
    "Copyright infringement notice": ("Other / Non-customer", 7),
    "Out of office reply": ("Other / Non-customer", 6),
    "Data erasure request": ("Other / Non-customer", 4),
    "Account verification": ("Other / Non-customer", 2),
    "Misc single-count reasons": ("Other / Non-customer", 5),
}

ELSIE = {
    "Size exchange": ("Sizing & Fit", 65),
    "Returns & exchanges (unspecified)": ("Replacement / Exchange", 70),
    "Return status": ("Replacement / Exchange", 2),
    "Changed mind": ("Replacement / Exchange", 1),
    "Refund request": ("Refund", 42),
    "Order update inquiry": ("Order Status & Changes", 79),
    "Edit order": ("Order Status & Changes", 11),
    "Order issue (unspecified)": ("Order Status & Changes", 2),
    "New order inquiry": ("Order Status & Changes", 1),
    "Cart management issue": ("Order Status & Changes", 1),
    "Delayed": ("Shipping Delay", 88),
    "Shipping (unspecified)": ("Shipping Delay", 43),
    "Tracking": ("Tracking & Address", 52),
    "Wrong address": ("Tracking & Address", 8),
    "Lost package": ("Order Not Received", 26),
    "Scam suspicion": ("Trust / Scam Concern", 14),
    "Damaged item": ("Product Quality", 4),
    "Wrong item": ("Wrong Item", 2),
    "Cancel order": ("Cancellation", 20),
    "Subscription (unspecified)": ("Cancellation", 2),
    "Product details": ("Product Question", 68),
    "Availability": ("Product Question", 8),
    "Brand verification": ("Product Question", 6),
    "Product question (unspecified)": ("Product Question", 5),
    "Authorization code request": ("Product Question", 1),
    "Billing (unspecified)": ("Billing & Payments", 4),
    "Payment failed": ("Billing & Payments", 3),
    "Discount code": ("Billing & Payments", 2),
    "Payout speed inquiry": ("Billing & Payments", 2),
    "General inquiry (unspecified)": ("Other / Non-customer", 62),
    "Sales inquiry": ("Other / Non-customer", 39),
    "International shipping availability": ("Other / Non-customer", 24),
    "Website performance inquiry": ("Other / Non-customer", 2),
    "Theme license verification": ("Other / Non-customer", 2),
    "Misc single-count reasons": ("Other / Non-customer", 2),
}


def roll(simple_map):
    out = {c: 0 for c in CATEGORIES}
    for _leaf, (cat, n) in simple_map.items():
        out[cat] += n
    return out


def roll_mt(period):
    raw = json.loads((HERE / "data" / "reasons_marys_tanks.json").read_text())
    out = {c: 0 for c in CATEGORIES}
    leaves = {c: [] for c in CATEGORIES}
    for leaf, counts in raw["counts"].items():
        cat = MT_MAP[leaf]
        out[cat] += counts[period]
        if counts[period]:
            leaves[cat].append((leaf, counts[period]))
    for cat in leaves:
        leaves[cat].sort(key=lambda x: -x[1])
    return out, leaves


# ---------------------------------------------------------------------------
# Store-level facts
# ---------------------------------------------------------------------------
DAILY_DATES = [f"2026-{m:02d}-{d:02d}" for m, d in
               [(7, d) for d in range(17, 32)] + [(8, d) for d in range(1, 16)]]

STORES = {
    "maggies": {
        "name": "Maggies Tanks",
        "region": "US",
        "created_cur": 25884, "created_prev": 4088,
        "closed_cur": 21513,
        "open": 1383, "pending": 2, "snoozed": 4358, "resolved_lifetime": 25593,
        "res_time_s": 18315,
        "email_created": 22072, "email_res_s": 8381,
        "fb_created": 3812, "fb_replies": 212, "fb_res_s": 172880,
        "orders_cur": None, "orders_prev": None,
        "issues_cur": roll(MAGGIES), "issues_prev": None,
        "created_daily": [217, 236, 213, 277, 337, 357, 377, 446, 419, 606, 796,
                          759, 752, 1009, 947, 877, 772, 1213, 1164, 1484, 1810,
                          1123, 1173, 961, 1207, 1442, 1516, 1560, 1578, 256],
        "closed_daily": [223, 216, 212, 222, 321, 353, 335, 389, 330, 418, 417,
                         723, 674, 938, 952, 989, 747, 951, 965, 1567, 1390,
                         1046, 1082, 964, 1348, 1287, 1516, 1551, 1806, 496],
        "res_daily": [12370, 5515, 3125, 5926, 7082, 13436, 9371, 13138, 3014,
                      3155, 974, 18559, 37176, 31730, 36092, 27517, 11290, 1503,
                      3780, 1031, 775, 63146, 35286, 73270, 172868, 42787,
                      63827, 135034, 172877, 174391],
    },
    "marys": {
        "name": "Mary's Tanks",
        "region": "AU",
        "created_cur": 9362, "created_prev": 6348,
        "closed_cur": 8756,
        "open": 247, "pending": 0, "snoozed": 1402, "resolved_lifetime": 19528,
        "res_time_s": 14369,
        "email_created": 8661, "email_res_s": 10615,
        "fb_created": 702, "fb_replies": 121, "fb_res_s": 170000,
        "orders_cur": None, "orders_prev": None,
        "issues_cur": None, "issues_prev": None,  # filled below
        "created_daily": [195, 146, 138, 231, 277, 312, 324, 237, 219, 276, 374,
                          336, 376, 392, 339, 288, 306, 368, 374, 356, 360, 360,
                          282, 260, 387, 482, 446, 346, 318, 192],
        "closed_daily": [311, 223, 187, 309, 376, 390, 436, 332, 292, 339, 461,
                         397, 325, 365, 374, 356, 297, 333, 376, 315, 339, 363,
                         292, 242, 440, 515, 516, 387, 561, 444],
        "res_daily": [7639, 7397, 7379, 7370, 7360, 7368, 7399, 7408, 7385,
                      7383, 7360, 7368, 18227, 15816, 55293, 39215, 5602, 5798,
                      12202, 23938, 61025, 66645, 80530, 113836, 148872, 77274,
                      110526, 173115, 184062, 176733],
    },
    "mj": {
        "name": "Mary and James",
        "region": "US",
        "created_cur": 2215, "created_prev": None,
        "closed_cur": 2265,
        "open": 44, "pending": 14, "snoozed": 19, "resolved_lifetime": 4266,
        "res_time_s": 25475,
        "email_created": 1763, "email_res_s": 9989,
        "fb_created": 452, "fb_replies": 11, "fb_res_s": 86500,
        "orders_cur": None, "orders_prev": None,
        "issues_cur": roll(MJ), "issues_prev": None,
        "created_daily": None, "closed_daily": None, "res_daily": None,
    },
    "lyns": {
        "name": "Lyn's Tanks",
        "region": "US/NZ",
        "created_cur": 1252, "created_prev": 3308,
        "closed_cur": 1028,
        "open": 18, "pending": 0, "snoozed": 506, "resolved_lifetime": 6531,
        "res_time_s": 13837,
        "email_created": 1252, "email_res_s": 13837,
        "fb_created": 0, "fb_replies": 0, "fb_res_s": None,
        "orders_cur": 1376, "orders_prev": 3972,
        "issues_cur": roll(LYNS), "issues_prev": None,
        "created_daily": [42, 25, 38, 47, 38, 45, 49, 55, 41, 38, 44, 46, 71,
                          55, 116, 27, 41, 40, 44, 42, 38, 32, 28, 26, 41, 37,
                          35, 31, 29, 11],
        "closed_daily": [42, 25, 20, 32, 32, 49, 47, 59, 40, 24, 45, 62, 52, 50,
                         151, 33, 64, 31, 48, 30, 46, 27, 17, 25, 56, 22, 46,
                         58, 11, 23],
        "res_daily": [41155, 3704, 9029, 4885, 11216, 25802, 9849, 19719, 6750,
                      16667, 21789, 26498, 10990, 9943, 104, 17807, 40102, 4896,
                      17211, 8794, 11723, 10256, 49811, 10760, 81309, 18509,
                      10382, 177934, 334, 72854],
    },
    "elsie": {
        "name": "Simply Elsie",
        "region": "UK",
        "created_cur": 976, "created_prev": None,
        "closed_cur": 862,
        "open": 73, "pending": 0, "snoozed": 85, "resolved_lifetime": 852,
        "res_time_s": 15899,
        "email_created": 976, "email_res_s": 15899,
        "fb_created": 0, "fb_replies": 0, "fb_res_s": None,
        "orders_cur": None, "orders_prev": None,
        "issues_cur": roll(ELSIE), "issues_prev": None,
        "created_daily": [4, 6, 8, 16, 13, 18, 16, 32, 25, 24, 25, 26, 32, 32,
                          33, 41, 37, 38, 45, 45, 59, 58, 50, 35, 45, 46, 46,
                          65, 42, 14],
        "closed_daily": [8, 7, 8, 17, 14, 18, 10, 18, 16, 13, 14, 19, 25, 20,
                         15, 142, 34, 30, 36, 61, 51, 28, 57, 52, 51, 51, 53,
                         83, 28, 34],
        "res_daily": [2914, 1948, 2356, 3310, 1161, 1804, 4585, 954, 7320, 5704,
                      5075, 6308, 3009, 3275, 896, 309705, 25693, 6001, 1584,
                      22991, 4369, 1260, 38351, 81932, 46172, 75485, 48135,
                      11706, 2555, 189531],
    },
}

mt_cur, mt_leaves = roll_mt("cur30")
mt_prev, _ = roll_mt("prev30")
STORES["marys"]["issues_cur"] = mt_cur
STORES["marys"]["issues_prev"] = mt_prev
STORES["marys"]["issue_leaves"] = {k: v[:5] for k, v in mt_leaves.items() if v}

# Weekly issue series - Mary's Tanks is the one account for which per-week
# contact-reason counts were pulled, so the over-time chart is scoped to it.
mt_weeks = []
for wk, label in [("w4", "Jul 19-25"), ("w3", "Jul 26-Aug 1"),
                  ("w2", "Aug 2-8"), ("w1", "Aug 9-15")]:
    counts, _ = roll_mt(wk)
    mt_weeks.append({"label": label, "counts": counts})

# ---------------------------------------------------------------------------
# Unresolved ticket rows
# ---------------------------------------------------------------------------
open_raw = json.loads((HERE / "data" / "open_tickets_marys_tanks.json").read_text())

LABEL_TO_ISSUE = {
    "return-exchange": "Replacement / Exchange",
    "size_replacement": "Replacement / Exchange",
    "refund-request": "Refund",
    "refund-approved": "Refund",
    "refund-insist": "Refund",
    "order-status": "Order Status & Changes",
    "where_is_my_order": "Order Status & Changes",
    "shipping-issue": "Shipping Delay",
    "delay": "Shipping Delay",
    "damaged-item": "Product Quality",
    "damaged": "Product Quality",
    "fulfilment-error": "Wrong Item",
    "fulfillment_issue": "Wrong Item",
    "payment-issue": "Billing & Payments",
    "chargeback": "Billing & Payments",
    "discount-code": "Billing & Payments",
    "cancel-order": "Cancellation",
    "product-question": "Product Question",
    "size_issue": "Sizing & Fit",
    "wrong_size": "Sizing & Fit",
    "ai-size-swap": "Sizing & Fit",
    "pfg-ready": "Replacement / Exchange",
    "positive-feedback": "Feedback",
    "thank-you": "Feedback",
}
# Labels that record what was actually done, not what the customer asked about.
ACTION_LABELS = {
    "pfg-ready": "Replacement approved, awaiting fulfilment",
    "pfg-ready-processed": "Replacement confirmed to customer",
    "refund-approved": "Refund agreed, awaiting processing in Shopify",
    "ai-edited-order": "Order edited by AI agent",
    "ai-size-swap": "Size swapped by AI agent",
    "ai-replacement": "Replacement order raised by AI agent",
    "pre-chargeback-risk": "Flagged as chargeback risk",
    "priority-refunds": "Queued for priority refund processing",
}
NOW = "2026-08-15T11:00"


def to_min(ts):
    d = ts[:10].split("-")
    t = ts[11:].split(":")
    days = int(d[0]) * 372 + int(d[1]) * 31 + int(d[2])
    return days * 1440 + int(t[0]) * 60 + int(t[1])


now_min = to_min(NOW)
rows = []
for tk, created, last, prio, inbox, cust, agent, labels in open_raw["tickets"]:
    ls = [l for l in labels.split(",") if l]
    issue = next((LABEL_TO_ISSUE[l] for l in ls
                  if l in LABEL_TO_ISSUE and l != "pfg-ready"), None)
    if issue is None:
        issue = next((LABEL_TO_ISSUE[l] for l in ls if l in LABEL_TO_ISSUE),
                     "Unclassified (no label)")
    actions = [ACTION_LABELS[l] for l in ls if l in ACTION_LABELS]
    age_d = round((now_min - to_min(created)) / 1440, 1)
    idle_d = round((now_min - to_min(last)) / 1440, 1)
    if actions:
        action, action_state = "; ".join(actions), "pending"
    elif agent == "UNASSIGNED":
        action, action_state = "No action recorded", "none"
    elif agent == "AI (Lovely)":
        action, action_state = "AI agent handling, no human action recorded", "ai"
    else:
        action, action_state = f"Assigned to {agent}", "assigned"
    rows.append({
        "ticket": tk, "created": created, "last": last, "priority": prio,
        "channel": inbox, "customer": cust, "agent": agent, "issue": issue,
        "labels": ls, "action": action, "action_state": action_state,
        "age_days": age_d, "idle_days": idle_d,
    })
rows.sort(key=lambda r: -r["age_days"])

# ---------------------------------------------------------------------------
# Group-level roll-ups
# ---------------------------------------------------------------------------
group_issues_cur = {c: 0 for c in CATEGORIES}
for s in STORES.values():
    for c, n in s["issues_cur"].items():
        group_issues_cur[c] += n

totals = {
    "created_cur": sum(s["created_cur"] for s in STORES.values()),
    "closed_cur": sum(s["closed_cur"] for s in STORES.values()),
    "open": sum(s["open"] for s in STORES.values()),
    "pending": sum(s["pending"] for s in STORES.values()),
    "snoozed": sum(s["snoozed"] for s in STORES.values()),
    "created_prev": sum(s["created_prev"] for s in STORES.values()
                        if s["created_prev"]),
    "fb_created": sum(s["fb_created"] for s in STORES.values()),
    "fb_replies": sum(s["fb_replies"] for s in STORES.values()),
    "email_created": sum(s["email_created"] for s in STORES.values()),
}
# Volume-weighted average resolution time across the group.
totals["res_time_s"] = round(
    sum(s["res_time_s"] * s["closed_cur"] for s in STORES.values())
    / totals["closed_cur"])
totals["res_time_email_s"] = round(
    sum(s["email_res_s"] * s["email_created"] for s in STORES.values())
    / totals["email_created"])
totals["repeat_contact"] = group_issues_cur["Repeat Contact (chasing us)"]
totals["categorised"] = sum(group_issues_cur.values())

# Actual resolution status. A closed ticket only counts as genuinely resolved if
# somebody replied and the customer did not come back about the same thing.
# Two deductions, both measured rather than assumed:
#   1. Facebook tickets that auto-closed at the 48h no-activity rule without a
#      reply (created minus replies sent on those inboxes).
#   2. Tickets whose contact reason IS the customer chasing an earlier one
#      ("Follow-up on previous contact", "Unanswered emails").
closed_no_reply = totals["fb_created"] - totals["fb_replies"]
totals["resolution"] = {
    "closed": totals["closed_cur"],
    "closed_no_reply": closed_no_reply,
    "repeat_contact": totals["repeat_contact"],
    "genuinely_resolved": totals["closed_cur"] - closed_no_reply - totals["repeat_contact"],
    "still_open": totals["open"] + totals["pending"],
    "parked_snoozed": totals["snoozed"],
    "nominal_rate": round(100 * totals["closed_cur"] / totals["created_cur"], 1),
    "actual_rate": round(100 * (totals["closed_cur"] - closed_no_reply
                                - totals["repeat_contact"]) / totals["created_cur"], 1),
}

OUT = {
    "generated": "2026-08-15",
    "period": {"cur": CUR, "prev": PREV},
    "daily_dates": DAILY_DATES,
    "categories": CATEGORIES,
    "stores": STORES,
    "group_issues_cur": group_issues_cur,
    "totals": totals,
    "marys_weeks": mt_weeks,
    "unresolved": rows,
    "unresolved_meta": {"total_open": open_raw["total_open"],
                        "captured": len(rows)},
}

(HERE / "data" / "dashboard_data.json").write_text(json.dumps(OUT, indent=1))

# ---------------------------------------------------------------------------
# Console summary - the figures the written summary quotes
# ---------------------------------------------------------------------------
print("GROUP created cur/prev:", totals["created_cur"], totals["created_prev"])
print("  like-for-like (stores with both periods):",
      sum(s["created_cur"] for s in STORES.values() if s["created_prev"]),
      "vs", totals["created_prev"])
print("  open:", totals["open"], " snoozed:", totals["snoozed"],
      " pending:", totals["pending"], " closed:", totals["closed_cur"])
print("  avg res time all: %.1fh  email only: %.1fh"
      % (totals["res_time_s"] / 3600, totals["res_time_email_s"] / 3600))
print("  FB tickets:", totals["fb_created"], "replies:", totals["fb_replies"])
print("  repeat-contact tickets:", totals["repeat_contact"])
print()
print("TOP GROUP ISSUES")
for c, n in sorted(group_issues_cur.items(), key=lambda x: -x[1])[:10]:
    print("  %-36s %6d  %4.1f%%" % (c, n, 100 * n / sum(group_issues_cur.values())))
print()
print("MARY'S TANKS cur vs prev (30d)")
for c in CATEGORIES:
    a, b = mt_prev[c], mt_cur[c]
    if max(a, b) < 40:
        continue
    d = "n/a" if a == 0 else "%+.1f%%" % (100 * (b - a) / a)
    print("  %-36s %5d -> %5d  %s" % (c, a, b, d))
print()
print("UNRESOLVED: rows %d  no action %d  aged>7d %d  idle>2d %d"
      % (len(rows),
         sum(1 for r in rows if r["action_state"] == "none"),
         sum(1 for r in rows if r["age_days"] > 7),
         sum(1 for r in rows if r["idle_days"] > 2)))
print("LYN'S issue rate cur %.1f%%  prev %.1f%%"
      % (100 * 1252 / 1376, 100 * 3308 / 3972))
