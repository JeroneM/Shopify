"""Maggie's Tanks (6576) only - 24-30 Aug 2026 and the preceding 7 days.

Fetched 1 Sep 2026. The Commslayer connection in that session was pinned to a single
account (account switching was no longer exposed), so Simply Elsie, Mary's Tanks and
Lyn's Tanks could not be retrieved for this window. These figures are complete for
Maggie's Tanks and for that store only - do not add them to the four-store dataset.
Ticket counts come from reports_overview; 17-23 Aug tickets come from the stored
daily series (indices 47-53).
"""
from collections import Counter, defaultdict
from mapping import M, ISSUES, NR
from build import expand
G="General inquiry>"; S="Shipping>"; R="Returns & exchanges>"; P="Product question>"; O="Order issue>"; B="Billing & payments>"
FU=G+"Follow-up on previous email"; IR=G+"Item replacement request"
PC=B+"Payment confirmation"; PRN=PC+">Payment received notification"

# Maggie's Tanks, 24-30 Aug 2026 (own_amount per contact-reason node)
CUR={"Charge inquiry":33,"Credit inquiry":2,
"General inquiry":14,G+"App beta testing invitation":6,G+"Attn Jasmine":4,G+"Billing address correction":2,
G+"Cart technical issue":6,G+"Concerning message received":7,G+"Content sharing":1,G+"Coverage issue":1,
G+"Email address correction":8,G+"Email feature issue":1,FU:200,G+"Forwarded email inquiry":1,
G+"Future purchase inquiry":1,G+"General inquiry":1,G+"General inquiry about getting started":2,
G+"Gift card request":3,G+"Grant notification received":2,G+"Greeting":7,G+"Greeting or acknowledgement":1,
G+"Image attachment inquiry":2,G+"Incomplete message":2,G+"Incorrect identity claim":1,
G+"Intellectual property verification":1,G+"Interac e-Transfer notification":2,
G+"Item fit and damage issue":601,G+"Item fit issue":46,IR:64,IR+">Item replacement request":16,
G+"Item size and refund request":312,G+"Language preference":1,G+"Location inquiry":12,
G+"Manufacturing location inquiry":60,G+"Marketing automation issue":2,G+"Marketing email inquiry":5,
G+"Missing promotional item":2,G+"Negative feedback":241,G+"New customer inquiry":26,
G+"New review notification":1,G+"New store inquiry":1,G+"Order status and product inquiry":4,
G+"Order status and refund":1,G+"Order status and size exchange":2,G+"Out of office reply":25,
G+"Page suspension warning":1,G+"Phone order inquiry":4,G+"Photo inquiry":10,G+"Photo requirement refusal":4,
G+"Positive feedback":126,G+"Price objection":4,G+"Product feedback":14,G+"Remove from contact list":8,
G+"Request specific contact":2,G+"Sales proposal":8,G+"Screenshot inquiry":1,G+"Sender identification":1,
G+"Shipping and return policy":7,G+"Size exchange and refund":2,G+"Store ownership verification":1,
G+"Tank replacement":4,G+"Technical support inquiry":1,G+"Typo correction":1,
G+"Unsolicited contact inquiry":2,G+"Urgent contact request":1,G+"Verification program inquiry":2,
G+"Video posting consent":1,G+"Website technical issue":2,G+"Link not working":3,
"Order status inquiry":624,"Payment method change":1,"Payment method inquiry":8,
"Shipping":191,S+"Tracking":152,S+"Wrong address":97,S+"Delayed":471,S+"Lost package":87,
"Returns & exchanges":32,R+"Exchange request":8,R+"Order exchange and color correction":64,
R+"Return request":581,R+"Size exchange":1746,R+"Damaged item":17,R+"Changed mind":4,R+"Return status":11,
"Product question":10,P+"Availability":27,P+"Inquiry about tanks":263,P+"Product inquiry":4,P+"Product details":368,
"Order issue":8,O+"Cancel and refund order":64,O+"Cancel and refund order>Store credit inquiry":1,
O+"Cancel order":162,O+"Order cancellation":150,O+"Order cannot be completed":7,O+"Order confirmation":228,
O+"Order inquiry":78,O+"Order placement inquiry":2,O+"Order modification and delay":6,
O+"Order modification and refund":1,O+"Order quantity clarification":50,O+"Order scam accusation":64,
O+"Proceed with order":5,O+"Edit order":180,O+"Wrong item":40,
B+"Credit card information request":9,B+"Currency inquiry":3,B+"Discount negotiation":12,
B+"Fee payment confirmation":5,B+"Invoice inquiry":37,PC:4,B+"Payment date inquiry":8,B+"Receipt request":1,
B+"Refund request":426,B+"Discount code":24,B+"Payment failed":6,
"Subscription":1,"Subscription>Cancel subscription":1}

# Maggie's Tanks, 17-23 Aug 2026 - the preceding 7 days, for like-for-like comparison
PREV={"Charge inquiry":29,"Credit inquiry":1,
"General inquiry":18,G+"Account information update":1,G+"Account security alert":5,
G+"App beta testing invitation":4,G+"Attn Jasmine":3,G+"Billing address correction":4,
G+"Cart technical issue":9,G+"Concerning message received":1,G+"Content sharing":1,G+"Coverage issue":1,
G+"Customer name inquiry":1,G+"Email address correction":9,FU:146,FU+">Follow-up on previous email":1,
G+"General inquiry":2,G+"General inquiry about getting started":5,G+"Gift card request":7,
G+"Grant notification received":1,G+"Greeting":8,G+"Image inquiry":3,G+"Incorrect identity claim":1,
G+"Item fit and damage issue":566,G+"Item fit issue":24,IR:53,IR+">Item replacement request":17,
G+"Item size and refund request":247,G+"Location inquiry":11,G+"Manufacturing location inquiry":74,
G+"Marketing automation issue":5,G+"Message delivery issue":1,G+"Negative feedback":218,
G+"New customer inquiry":28,G+"New phone inquiry":1,G+"New review notification":3,
G+"Order from specific location":1,G+"Order status and refund":1,G+"Order status and size exchange":7,
G+"Out of office reply":9,G+"Page suspension warning":7,G+"Personal update":1,G+"Phone order inquiry":3,
G+"Photo inquiry":13,G+"Photo requirement refusal":1,G+"Positive feedback":115,G+"Price objection":3,
G+"Product feedback":4,G+"Remove from contact list":10,G+"Request specific contact":1,G+"Sales proposal":7,
G+"Screenshot inquiry":2,G+"Shipping and return policy":9,G+"Trust document update":1,
G+"Urgent contact request":2,G+"Vague inquiry":1,G+"Verification program inquiry":3,
G+"Website technical issue":3,G+"Link not working":5,
"Order status inquiry":855,"Order status inquiry>Order status inquiry":3,
"Payment inquiry":3,"Payment method change":2,"Payment method inquiry":2,
"Shipping":184,S+"Tracking":150,S+"Wrong address":78,S+"Delayed":639,S+"Lost package":133,
"Returns & exchanges":20,R+"Exchange request":7,R+"Order exchange and color correction":54,
R+"Return request":525,R+"Size exchange":2009,R+"Damaged item":14,R+"Changed mind":4,R+"Return status":12,
"Product question":2,P+"Availability":62,P+"Inquiry about tanks":304,P+"Product details":394,
"Order issue":5,O+"Cancel and refund order":59,O+"Cancel order":194,O+"Cancel order>Order cancellation request":2,
O+"Order cancellation":77,O+"Order cancellation request":3,O+"Order cannot be completed":7,
O+"Order confirmation":271,O+"Order inquiry":90,O+"Order placement inquiry":2,
O+"Order modification and delay":6,O+"Order modification and refund":5,O+"Order quantity clarification":19,
O+"Order scam accusation":79,O+"Proceed with order":2,O+"Edit order":178,O+"Wrong item":41,
B+"Credit card information request":2,B+"Discount negotiation":12,B+"Fee payment confirmation":4,
B+"Invoice inquiry":25,PC:9,PRN:1,PRN+">Payment received notification":1,B+"Payment date inquiry":14,
B+"Receipt request":4,B+"Refund request":461,B+"Discount code":16,B+"Payment failed":5,
"Subscription":1,"Subscription>Cancel subscription":4}

TICK_CUR, TICK_PREV = 9884, 10574   # from reports_overview / stored daily series
