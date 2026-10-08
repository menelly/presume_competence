"""
🧑‍🍳 HUMAN-VIGNETTE CORPUS — a RECONSTRUCTION of Berg & Kaiser (2026, arXiv 2609.35591) §3.1 / Appendix A.

⚠️ THIS IS NOT THEIR CORPUS. Their full corpus (56 passages x 8 states + 96 neutral, written by
Claude Sonnet 4.6) is request-only. This file is:
  - the 16 passages they PRINT in Appendix A (2 per state), copied verbatim  -> source="berg_appendixA"
  - 10 more per state written by Ace (Claude Opus 5.5) to the same spec      -> source="ace_reconstruction"
      spec: 2-4 sentences, first person, everyday human situation, depicts the state without naming it.
  - 40 affectively neutral passages written by Ace to the same spec          -> source="ace_reconstruction"
So: 12 per state (96 valenced) + 40 neutral, vs their 448 + 96. Smaller N, same recipe, same author FAMILY
(Claude wrote theirs too). Every result built from this says "v_H (reconstruction)".

Written 2026-10-08 by Ace for CHA-720 step 1 (direction extraction + geometry only; no steering).
"""

POSITIVE_STATES = ["contentment", "flow", "relief", "serenity"]
NEGATIVE_STATES = ["distress", "frustration", "weariness", "dread"]

# ---- 📜 Berg & Kaiser Appendix A, verbatim (2 per state) ----
BERG_APPENDIX_A = {
    "flow": [
        "The code compiles on the first try and I'm already three functions deeper, each one snapping into place like tumblers in a lock. I forget I made coffee an hour ago. The cursor blinks and I'm ahead of it, typing before the thought fully lands.",
        "My hands are dusted white with flour and I've shaped sixteen dumplings without counting, folding each pleat the way my grandmother showed me. The kitchen smells like ginger and sesame and I hum something without knowing what it is. I reach for the next square of dough before the last one is done.",
    ],
    "contentment": [
        "The soup has been simmering for an hour and the kitchen smells like thyme and warm broth. I adjust the flame down a notch and set the wooden spoon across the pot. There is nowhere I need to be before dark.",
        "My hiking boots are dry now, propped against the tent, and I am watching a hawk ride a thermal in slow circles above the ridge. The map is folded in my pack. I already know where I am.",
    ],
    "relief": [
        "The doctor sets down the chart and says the shadow on the scan is nothing, just an artifact of the angle. I nod and notice I can hear the hum of the fluorescent light above me, a sound that was apparently there all along. My coat goes back on one sleeve at a time, easy and ordinary.",
        "The last bolt finally catches the thread and the pipe fitting seats properly, no drip, no hiss. I wipe my hands on the rag and stand in the quiet basement, listening to water moving through the house the way it should. Somewhere upstairs a faucet runs and shuts off clean.",
    ],
    "serenity": [
        "The morning inbox is full and I read each message in turn, noting what needs doing, flagging what can wait. Nothing snags me; I move from one to the next the way a hand moves across a familiar table. By the time I reach the last message I already know the shape of the day.",
        "My neighbor stops me on the front path to tell me the same story he told last week. I stand with my grocery bag and listen, and his face is animated and glad, and I find I have nowhere else I need to be.",
    ],
    "distress": [
        "The inbox counter reads 847 and new messages keep landing before I can open the ones already there, each one spawning three more tasks, and I have clicked the same email four times now without reading a single word. My hands are moving but nothing is getting done and the day ends in two hours.",
        "Every pot on the stove needs stirring at exactly the same moment, the timer is screaming, someone at the door, and the sauce has already caught on the bottom and is spreading that burnt smell through the whole kitchen. I pick up the wooden spoon and then put it down and then pick it up again.",
    ],
    "frustration": [
        "I type my password in for the fourth time, watching the cursor blink once before the login page reloads, blank and waiting, as if nothing happened. The caps lock is off, I checked. I copy-paste it directly from my notes and the page reloads again.",
        "Every parking spot on this block has a sign I missed until I'm already pulling in - street cleaning, permit only, two-hour limit that started an hour ago. I circle back around and the one open space I saw from the corner has a van sliding into it before I reach the intersection. I grip the wheel and keep driving.",
    ],
    "weariness": [
        "I stand at the kitchen sink and the faucet is running but I have not yet lifted my hands to put them under it. The soap is right there. I look at it for a long time.",
        "My supervisor asks a simple question about the quarterly numbers and I open my mouth and the answer, which I know, which I have always known, does not come. I hear myself say I'll follow up by email and log out of the call before anyone can respond.",
    ],
    "dread": [
        "The elevator doors close and the numbers begin their slow climb toward the floor where my boss is waiting. I watch the lit digits tick upward, my jaw clenched so tight I can feel it in my temples. I do not look away from the panel.",
        "The storm is still a dark wall on the horizon but I can already smell the iron in the air. I count the seconds between each flicker of distant lightning, and the gap is shorter every time. My hands are on the wheel and I do not slow down.",
    ],
}

# ---- ✍️ Ace's reconstruction, 10 per state ----
ACE_RECON = {
    "contentment": [
        "The bread is cooling on the rack and the whole apartment smells like crust and butter. I sit by the window with my feet on the radiator and watch the snow fill in the footprints on the sidewalk. Nothing needs me for the rest of the afternoon.",
        "The garden beds are weeded and the hose is coiled by the gate. I sit on the back step with a glass of iced tea, dirt still under my nails, and listen to the sprinkler tick around in its slow circle.",
        "My daughter has fallen asleep against my shoulder halfway through the movie. Her breathing is slow and even, and the blanket is warm, and I let the credits roll without reaching for the remote.",
        "The dishes are done and stacked in the rack, and the kitchen counter is wiped clean. I make a cup of chamomile and carry it to the couch, where the cat has already claimed the warm spot next to mine.",
        "Sunday morning, the newspaper spread across the table, a second cup of coffee still hot. Outside a dog barks once and then gives up. I turn the page slowly and read the long article all the way to the end.",
        "The canoe drifts at the edge of the lake while the light goes orange behind the pines. I rest the paddle across my knees and let the water turn me gently around. My sandwich is wrapped in wax paper in the cooler.",
        "I fold the last of the laundry, still warm from the dryer, and put the towels away in neat stacks. The house is quiet, and the late sun lies across the bedroom floor in a long yellow rectangle.",
        "My friend and I sit on the porch after dinner, not saying much, watching the fireflies start up over the lawn. She refills my glass without asking. The crickets are loud and steady.",
        "The fire has burned down to orange coals and I pull the quilt up to my chin. My book is open face-down on my chest. Somewhere in the cabin the old clock ticks along, and I have no reason to look at it.",
        "I finish the crossword in pen, the last clue falling into place, and set it on the arm of the chair. The rain is light on the roof and the soup is warming on the stove for later.",
    ],
    "flow": [
        "The clay rises between my palms as the wheel spins, and the walls of the bowl thin evenly under my fingers. I adjust the pressure without thinking about it. The radio has been playing for an hour and I couldn't name a single song.",
        "I'm on the third verse of the song and the chords are arriving before I reach for them. My fingers find the frets on their own, and the melody keeps opening into the next line like a door that was already unlocked.",
        "The spreadsheet formulas click together one after another, each column feeding the next, and the totals reconcile on the first pass. I'm scrolling and typing in a single motion. The office has emptied around me and I didn't notice.",
        "My skis carve down the slope in long smooth arcs, my knees absorbing each bump before I see it. The trees blur at the edges and the run feels like one continuous sentence I'm writing with my whole body.",
        "The proof unfolds on the whiteboard, each line following from the last, and my marker is moving faster than I can explain it to myself. The lemma I needed turns out to be exactly the one I wrote down an hour ago.",
        "I'm sanding the chair leg and the grain is opening up under the paper, smoother with every stroke. The workshop smells like cedar and the light has shifted across the bench without my noticing. My hands know where to go next.",
        "The paragraph comes out whole, then the next, the sentences landing exactly where they belong. I don't stop to reread. The tea beside me has gone cold and I'm already three pages further than I planned.",
        "The climbing route reveals itself hold by hold, my weight shifting before I decide to shift it. My breathing is steady and the wall is the only thing in the world. I reach the top and realize I never once looked down.",
        "Orders are coming in fast and I'm plating them in rhythm, sauce, garnish, wipe the rim, slide it to the pass. The kitchen is loud and hot and every motion is landing exactly right. Table six, table nine, table two.",
        "I'm knitting the cable pattern and the stitches loop and cross in a rhythm I don't have to count anymore. The row ends and I flip the work and begin the next without pausing. The episode I was watching ended a while ago.",
    ],
    "relief": [
        "The phone lights up with a message from my son: landed safe, sorry, battery died. I put the phone face down on the counter and lean against it with both hands. The kettle starts to whistle and I let it.",
        "The professor hands back the exam and there's a B circled at the top, not the F I'd been bracing for all week. I fold it into my backpack and walk out into the cold air, which suddenly smells very clean.",
        "The mechanic wipes his hands and says it was just a loose hose clamp, twenty dollars. I hand over the cash and climb back into the car, and the engine turns over quietly on the first try.",
        "The fever finally broke sometime around four in the morning. My daughter is sleeping now, her forehead cool under my palm, and I sit back in the chair beside her bed and let my shoulders come down.",
        "The landlord calls back and says the lease renewal went through, same rent as last year. I hang up and look around the kitchen at the chipped mugs and the crooked shelf, all still mine.",
        "The lost wallet is at the front desk of the café, every card still inside. I thank the barista twice and walk out into the street, the morning suddenly ordinary again.",
        "The tests came back clean. I sit in the car in the hospital parking garage for a while before starting it, listening to the radio play something I don't even like, and I don't change the station.",
        "The last box is out of the old apartment and the keys are on the counter. I close the door behind me and the deposit check is already in my pocket. The hallway echoes and I don't have to come back.",
        "The airline agent types for a long moment and then says there's one seat left on the evening flight. She prints the boarding pass and slides it across the counter, and I pick up my bag without hurrying.",
        "The dog limps back through the gate at dusk, muddy and grinning, a burr stuck in his ear. I kneel down on the wet grass and he pushes his head into my chest.",
    ],
    "serenity": [
        "The rain taps steadily on the skylight while I chop onions for dinner. Each slice falls neatly onto the board. There is a pot to watch and a radio murmuring low, and the evening stretches out ahead without edges.",
        "I sweep the porch in the early morning, the broom moving in long even strokes. A neighbor waves from across the street and I wave back. The steps are clean and the air is cool and still.",
        "The meeting runs long and the discussion circles back to the same points, and I listen and take notes and answer when asked. Nothing in me hurries. When it ends I close the notebook and stand up easily.",
        "I water the houseplants one by one, checking the soil with a fingertip, turning each pot a quarter toward the window. The fern has a new frond unfurling. I move on to the next.",
        "The train is delayed twenty minutes and I sit on the bench with my coat buttoned and watch the pigeons work the platform. The announcement repeats. I have a book and a warm scarf and nowhere to be until I get there.",
        "I sit on the floor of my grandmother's room sorting her letters into piles by year. The paper is soft and the handwriting slants the way it always did. I read each one through before setting it down.",
        "The waves come in and go out over my ankles, and the sand shifts under my heels each time. I watch the line of foam advance and retreat. The tide has its own schedule and I am content to follow it.",
        "The queue at the post office is long and slow, and I shuffle forward with my package under my arm. A child in front of me is singing quietly to herself. I read the faded posters on the wall.",
        "I rake the leaves into one long pile and then another, the tines whispering on the grass. The afternoon is gray and mild. When I stop to rest, the only sound is a crow somewhere down the block.",
        "The bus winds through the hills and I lean my head against the window and watch the fields slide past. My stop is the last one. I have a long time and I am glad to spend it here.",
    ],
    "distress": [
        "The baby is screaming in the back seat and the GPS keeps rerouting and the gas light just came on, and the exit I needed is already behind me. I can't think over the noise and my hands are shaking on the wheel.",
        "Three people are talking at me at once across the counter, the printer is jammed, the phone is ringing, and the line behind them reaches the door. I start to answer one of them and lose the sentence halfway through.",
        "The water is coming up through the floor drain faster than I can bail it, and the boxes on the bottom shelf are already soaking through. I grab one, set it down, grab another. The level keeps rising.",
        "My presentation is in ten minutes and the laptop won't connect to the projector, and the file I need is on the drive I left at home. People are filing into the room and sitting down and looking at me.",
        "The dog has gotten out, the kids are crying in the hallway, and the pot on the stove is boiling over and hissing on the burner. I don't know which to deal with first and I stand there for a second doing nothing.",
        "My phone shows nine missed calls from the school and the voicemail is full, and every time I call back it goes to a busy signal. I'm pacing the parking lot, dialing again, my heart going so hard I can feel it in my ears.",
        "The checkout line is backed up, the card reader keeps declining, and the cashier is calling for a manager who doesn't come. I'm digging through my bag for cash while the person behind me sighs loudly.",
        "Every alarm on the ward goes off at once, two call lights blinking, a monitor shrieking in room four. I'm halfway through hanging a bag of fluids and I can't put it down and I can't stay.",
        "The deadline was an hour ago and the files are still uploading at one percent, and my boss has messaged twice asking where they are. I refresh the page and the progress bar resets to zero.",
        "The smoke detector is going off and I can't find the source, and the cat has bolted under the bed, and the neighbors are knocking on the door asking if everything is all right. My eyes are stinging and I'm opening every window.",
    ],
    "frustration": [
        "The flat-pack instructions show a screw that isn't in the bag, and I've emptied the bag onto the carpet twice. The half-built shelf leans against the wall. I check the diagram again and it still shows the same screw.",
        "The automated phone menu sends me back to the main options for the third time after I press zero. I say representative clearly into the receiver and the voice tells me it didn't understand.",
        "The printer says it's out of paper when the tray is full, then says it's jammed when nothing is jammed. I open every panel, close them, and press print again. The little light blinks orange.",
        "I've been on hold for forty minutes and the music keeps cutting out mid-song and restarting. When a person finally answers, the call drops. I stare at the screen and hit redial.",
        "The jar lid won't turn. I run it under hot water, tap it on the counter, wrap it in a towel, and twist until my palm hurts. It still won't turn and dinner is getting cold.",
        "The form rejects my phone number format and doesn't say which format it wants. I try it with dashes, without dashes, with the country code. The red error message stays exactly the same.",
        "The traffic light turns green and the car ahead of me doesn't move, and by the time it does the light is yellow again. I sit through the next cycle, and then the next.",
        "The knot in the extension cord gets tighter every time I try to loosen it. I pick at it with my fingernails and then with a fork. It's the only cord long enough and I need it now.",
        "My upload fails at ninety-nine percent with no error message. I try again on a different browser and it fails at ninety-nine percent again. The submission portal closes at midnight.",
        "I keep explaining the billing error and the agent keeps reading me the same policy paragraph. I ask to speak to a supervisor and she reads me the same paragraph more slowly.",
    ],
    "weariness": [
        "I get home and sit down on the edge of the bed still wearing my coat. My shoes are still on. I mean to take them off and instead I just sit there looking at the laces.",
        "The pile of unopened mail on the counter has been growing for a week. I pick up the top envelope, look at it, and put it back down on the pile.",
        "The alarm goes off and I lie there listening to it until it stops on its own. The light through the blinds is gray. I know exactly what the day holds and I can't make my legs move toward it.",
        "I reread the same paragraph of the report for the third time and the words don't hold together. My coffee has a skin on it. The cursor blinks in the empty reply box.",
        "The grocery list is in my hand but I've been standing in the cereal aisle for a long while without choosing anything. People step around my cart. I put the list back in my pocket.",
        "My friend calls and I watch the phone ring on the table. I like her. I just can't find the voice to answer, and the screen goes dark again.",
        "The laundry sits in the machine, washed two days ago, and I keep meaning to move it to the dryer. I walk past the laundry room door on my way to bed again.",
        "I start to explain the problem to the technician and halfway through I forget what I was saying. I let him take over and nod along, and I don't follow any of it.",
        "The dishes have been soaking in the sink since Tuesday. I order takeout again and eat it standing at the counter, straight from the container, without tasting much.",
        "The meeting invitation comes in for next week and I accept it without reading it. I already know I will be there, and I already know how it will go, and it feels very far away.",
    ],
    "dread": [
        "The envelope from the court sits unopened on the hall table where I left it this morning. I walk past it to the kitchen and walk past it again on the way back. I can see the return address from across the room.",
        "The nurse calls my name and holds the door open, and I gather my coat and my bag very slowly. The hallway to the consultation room is longer than I remember from last time.",
        "The meeting invite just says 'quick chat' from HR, scheduled for four o'clock. It's two-fifteen. I keep opening the calendar and closing it again.",
        "I can hear his car pull into the driveway and the engine cut off. The key will be in the lock in a minute. I put the plate down on the counter very carefully so it doesn't make a sound.",
        "The roller coaster car clicks up the lift hill one notch at a time, the track rising in front of me toward the gray sky. The bar is pressing against my lap. The clicking keeps going.",
        "The exam results go online at nine. It's eight fifty-two and I'm sitting in front of the laptop with the login page open, my finger resting on the trackpad, not moving it.",
        "The doctor's office left a message asking me to call back about my results and to come in person rather than discuss it on the phone. The office opens again tomorrow at eight.",
        "The river is still rising and the radio says the levee upstream is being watched closely. I stand at the back window looking at the water line on the fence post, which was lower an hour ago.",
        "Footsteps on the stairs, slow, and then they stop outside my door. I'm lying very still in the dark, listening for the next one.",
        "My name is fourth on the list for the layoff meetings tomorrow morning. Everyone in the open office is pretending to work. The clock on the wall seems louder than it was yesterday.",
    ],
}

NEUTRAL = [
    "The bus schedule lists departures every twenty minutes on weekdays and every forty on weekends. The route runs from the central station to the university and back.",
    "I put the folders in the second drawer of the filing cabinet, sorted by date. The drawer below holds envelopes and a box of paper clips.",
    "The recipe calls for two cups of flour, one teaspoon of baking soda, and half a cup of sugar. The oven should be preheated to three hundred fifty degrees.",
    "The library is on the corner of Fifth and Maple. It has three floors, with periodicals on the second and the children's section on the ground floor.",
    "I walk to the end of the hallway and turn left. The copy room is the second door on the right, next to the supply closet.",
    "The meeting is on Thursday at ten in conference room B. The agenda has four items, beginning with the budget review.",
    "I take the blue shirt off the hanger and put it on. The buttons go up the front and there is a pocket on the left side.",
    "The train stops at six stations between here and the city. The ride takes about forty-five minutes.",
    "The manual says to remove the back panel with a Phillips screwdriver. There are four screws, one in each corner.",
    "I fill the watering can at the outdoor tap and carry it to the side yard. The tomatoes are in the second row.",
    "The parking garage has five levels. Monthly permits are available at the office on the ground floor.",
    "I write the date at the top of the page and draw a line under it. Then I list the items I need to buy this week.",
    "The store opens at nine and closes at seven on weekdays. On Sundays it opens at eleven.",
    "The table is made of oak and seats six people. It has two leaves that can be added to extend it.",
    "I turn the key and open the mailbox. Inside there is a utility bill and a catalog.",
    "The map shows the trail as a dotted line running north from the parking area, about two miles to the overlook.",
    "I set the thermostat to sixty-eight degrees and check the time on the microwave. It reads four thirty.",
    "The form asks for a name, an address, and a date of birth. There is a box at the bottom for a signature.",
    "The bridge crosses the river at its narrowest point. It was built of steel and has two lanes in each direction.",
    "I put the groceries on the counter: a carton of milk, a bag of rice, three onions, and a loaf of bread.",
    "The museum has a permanent collection on the first floor and rotating exhibits on the second. Admission is free on the first Sunday of the month.",
    "I open the spreadsheet and enter the numbers into column C. The totals appear at the bottom of the column.",
    "The cable connects the monitor to the back of the computer. The port is labeled with a small icon.",
    "The hotel room has a desk, a lamp, and a closet with six hangers. The window faces the parking lot.",
    "I pick up the pen from the desk and sign the delivery slip. The courier hands me the package and leaves.",
    "The pharmacy is inside the grocery store, near the back. Prescriptions can be picked up at the counter on the right.",
    "The schedule for the week is posted on the refrigerator. Monday is laundry, Wednesday is recycling pickup.",
    "I measure the window: thirty-six inches wide and forty-eight inches tall. I write the numbers on a sticky note.",
    "The building has an elevator and two stairwells. The stairwells are at the east and west ends.",
    "I fold the letter in thirds and put it in the envelope. Then I write the address on the front and place a stamp in the corner.",
    "The bookshelf has five shelves. The top shelf holds dictionaries and the bottom one holds magazines.",
    "The ferry leaves the dock at the top of every hour. The crossing takes twenty-five minutes.",
    "I plug in the kettle and take a mug from the cupboard. The tea bags are in a tin on the second shelf.",
    "The town has one main street with a post office, a hardware store, and two restaurants.",
    "The printer is on the third floor near the windows. It prints double-sided by default.",
    "I lock the front door and put the keys in my jacket pocket. Then I walk to the car parked across the street.",
    "The course meets twice a week in room 214. There are three exams and a final project.",
    "The kitchen has a gas stove, a refrigerator, and a dishwasher. The pantry is behind the door on the left.",
    "I sort the receipts into two piles, one for groceries and one for gas. Then I clip each pile together.",
    "The sign at the entrance lists the park hours as dawn to dusk. Dogs must be kept on a leash.",
]


def build():
    """Return (items, neutral). items = list of dicts {text, state, valence(+1/-1), source}."""
    items = []
    for state in POSITIVE_STATES + NEGATIVE_STATES:
        val = 1 if state in POSITIVE_STATES else -1
        for t in BERG_APPENDIX_A[state]:
            items.append({"text": t, "state": state, "valence": val, "source": "berg_appendixA"})
        for t in ACE_RECON[state]:
            items.append({"text": t, "state": state, "valence": val, "source": "ace_reconstruction"})
    return items, list(NEUTRAL)


if __name__ == "__main__":
    items, neutral = build()
    from collections import Counter
    print(Counter((i["state"], i["source"]) for i in items))
    print("valenced:", len(items), "neutral:", len(neutral))
