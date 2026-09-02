# Foresight: demand before it happens

The system behind UG should feel, to every user, like their need was anticipated. Foresight is
that system: it predicts where demand will be, by day, place and vehicle class, shows the gap
between what is needed and what drivers have promised, and points the right vehicle to the
right place before anyone searches.

## Three calendars

1. **Seasons.** The agricultural year by region and crop: mangoes from November in Masaka,
   Soroti and Lira; Robusta coffee in two flushes; Arabica on Elgon from October; maize after
   each rains in the East and North; matooke, tea, cassava, sugarcane and fish year-round;
   pineapples in Kayunga and Masaka; livestock to market from Karamoja. Each season names the
   vehicle class it needs (minibus, pickup, lorry) and a modelled number of loads a day.
2. **Rhythms.** Places that surge at known hours: Entebbe's arrival and departure banks,
   Mulago's visiting hours, Namboole and Lugogo on event days, Kololo, Makerere's term
   mornings, the markets before dawn, Sunday services and Friday prayers, the Jinja sugar belt's
   shift changes, the 08:00 trekking briefings in Kisoro. Each names the vehicle people want
   there (a car at midnight at Entebbe, a boda at Mulago).
3. **Events.** Named days: the Kampala City Festival, Nyege Nyege, the Kabaka run,
   Independence Day, Martyrs Day at Namugongo, the Christmas exodus and the January return.
   Partners and agents can add events through the API.

## What it produces

A forecast for the next seven days: rows of (day, town or venue, what, vehicle class, loads or
trips needed, confidence, note). Drivers see it in the Foresight section and can promise "I'll
be there"; promises count against the need so the gap is visible to everyone: **14 minibus
loads needed in Masaka, 3 promised, 11 short**. Riders and senders see the same rows as
context: a produce sender in mango season sees the season and the minibus rate; a traveller
sees that Namboole will need cars at four.

The map shows tomorrow's forecast as amber rings breathing over the towns; "Point me there"
turns the map to the place and moves every desk to it (the same teleport a hover triggers).
Felt receives the layer as GeoJSON with loads, promises and gap per town.

## The right vehicle to the right place

Every signal carries a vehicle class: boda, car, minibus, pickup, lorry, bus. Deliver's
"Produce" option quotes UG's minibus, pickup and lorry with a driver and shows the season's
expected loads. A driver's Comfort Map names their vehicle, so a promise from a boda does not
count against a lorry need. This is the rule that stops the wrong vehicle arriving.

## Confidence and learning

Seasons carry 60% confidence, rhythms 75%, listed events 85%, partner-added events 90%. Every
departed stage on a corridor raises confidence for its town a little; every completed booking
does the same. That is the seed of the learning system: the rules are the prior, the ledger is
the evidence, and the model that replaces the rules is trained on fills, not on guesses.

## Honesty

Loads per day are modelled from general knowledge of Uganda's year and are shown with their
confidence. Nothing in Foresight is a promise to a driver of income, and a "short" figure is a
gap in promises, not a queue of paying customers. The first real harvest season the system runs
through will correct most of these numbers, and the docs will say so.
