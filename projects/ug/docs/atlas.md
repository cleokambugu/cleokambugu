# The Atlas: how it all ties together

UG grew fast: a compare desk, a stage, a driver map, deliveries, buses, flights, ferries, a
railway, Signature cars, stays, plug-ins, an opening animation, an install path. The risk of a
build this size is that it becomes a bag of features. The tie is a set of **ones**. Every part
of UG is an instance of one of them, and anything new must be too.

## One table

Every way to move in Uganda is a row in one table, `ATLAS`, keyed by mode: air, bus, water,
rail, signature, stay; the road modes (ride-hailing, boda, matatu, special hire, pool, rent) are
the older `PROVIDERS` table and will fold into it in v2. A row has an operator, what it does,
where it goes, a modelled fare with a unit, a **state**, a colour and a provenance note. Nothing
appears anywhere in UG that is not a row.

## One truth about state

Every row is in exactly one of four states, and the state is shown, never hidden:

| State | Means | Button |
| --- | --- | --- |
| **Book on UG** | UG has a channel (an API, a business console, a staffed line) and the concierge places it | Book on UG |
| **Call ahead** | The operator runs, has no channel yet; UG shows the number, the SafariShare rule | Call ahead · number |
| **Listed** | Recognised so it exists in the picture; nothing is booked | Ask UG to add it |
| **Coming** | Being built: the SGR, Kabaale airport, a metre-gauge revival | Tell me when |

The compare desk applies the same honesty to routes: a provider that does not serve a route is
still listed, greyed, with the reason ("bodas do not take trips over 60 km"). The promise
"every ride, one screen" is visibly true because the absences are on the screen too.

## One desk

The compare desk is the only place a price is ranked. It quotes the road modes, the stage, the
rental, and, where the route allows, the flight to the nearest airstrip, the helicopter, the
ferry, the train, and the Signature car the customer picked. Every quote carries its provenance
in words. The cheapest live quote is "Cheapest" if it is UG's own price and "Likely cheapest"
if it is an estimate.

## One rail

Whatever is booked, from a boda to a helicopter to a hotel night, runs on the same trip rail:
requested, placed with the partner, driver or courier assigned with a plate, arriving, on trip,
done. The rail lives in the nav as a pill and opens as a sheet. Nobody is sent away to finish
what they started; the partner's app is a quiet link for those who want it. Production replaces
the rail's timers with partner channels (see `stay-on-ug.md`).

## One formula

Pool seats, stage seats, parcels in the boot, empty legs and driver offers all come from
`poolSeatCost`: road cost plus a driver wage, divided by paying seats, plus UG's fee, shown in
shillings on both sides. A parcel is a quarter of a seat. An empty leg is forty percent of a
seat. An offer to a driver is the whole car, road plus wage, in one number.

## One map

The particle map in the hero is built from Natural Earth geometry and carries the towns, the
parks, the Pulse heat layer, and the pins the Atlas points to. The opening animation draws the
same map from scattered particles and runs the same modes across it: cars and bodas on the
corridors, three flights arcing from Entebbe to Kidepo, Bwindi and Gulu, a boat to Ssese, a train
to Namanve. The map you watch assemble is the map you land on.

## One wallet, one crest, one link

Every payment is a Flutterwave checkout in UGX, sandboxed until a live key and a settled float
arrangement exist. Every surface wears the Crest. The site and the app are one link: install it
from the page, or scan the code, and the same account, stages and rail are there.

## One forecast

Foresight reads the seasons, the venue rhythms and the events of the year and produces one
forecast by day, place and vehicle class. Drivers promise against it, the gap shows, the map
breathes amber where demand is coming, and Deliver's produce quotes name the season. The same
rows come from the server when the app is live. See `foresight.md`.

## One place at a time

Hover or tap a town on the map and the whole app is there: the compare desk, the stages, the
parcel destination, the weekend, the buses on that corridor, the map turned to face it, a pill
in the nav saying where you are. One teleport, every desk.

## One voice, six languages

The same strings in English, Swahili, Luganda, Runyankore-Rukiga, Acholi and Ateso, with the
confidence of each shown and English as the honest fallback. See `languages.md`.

## One rule for adding anything

Before a feature ships it must answer: which row of the table is it, what state is it in, does
it price through the desk, does it book through the rail, does it price through the formula,
does it appear on the map, does it pay through the wallet, does it wear the crest. If the
answer to any is "it is special", it is not ready.

## What is real in v1.1

The table is real and the states are honest. The operators in it are real names from search
snippets and general knowledge; their fares and timetables are modelled and marked so. Booking
is simulated. The concierge is simulated. The Signature fleet is UG's own proposition. The
airports and railway lines "coming" are described from general knowledge and must be verified.
Nothing here is a live fare, a licensed service, or a contract with any operator.
