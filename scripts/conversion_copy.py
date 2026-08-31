# -*- coding: utf-8 -*-
"""
Conversion copy for the HAS-NOT-ORDERED branch: subjects and preheaders.

THE LADDER. Four emails at day 0, 1, 3 and 5, and the pressure builds rather
than starting at maximum:

  day 0   name the offer, no countdown          welcome, not a deadline
  day 1   offer plus "4 days left"              first nudge
  day 3   "only 2 days left" leads the subject   the offer is now the headline
  day 5   "last day"                            final call

THE NUMBERS ARE NOT INVENTED. The body of each email already carries a
day-accurate countdown - welcome-01 "Expires in 5 days", 02 "Expires in 4 days",
03 "2 days left", 04 "Last day!" - which matches the 0/1/3/5 cadence. The
subjects and preheaders reuse those exact figures so the subject line cannot
contradict the email it opens.

NO COUPON CODE IN THIS COPY, deliberately. Putting "HELLO10" in four preheaders
across six languages would mean 24 more places to edit when the code changes.
The literal code stays in exactly one place, the code box in welcome-01. This
copy says "your 10%" instead.

THE ORDERED BRANCH MUST NOT SEE ANY OF IT. welcome-02, 03 and 04 share one
preheader between both branches - only welcome-01 replaced its own in the
no-discount variant. So each email now also has a pre_ordered, which is the
neutral text that used to be the preheader, and the variant swaps it in. Without
that, someone who had just ordered would get an inbox snippet pushing a discount
they cannot use, which is the exact thing the B branch exists to avoid.
"""
NB = " "   # French groups thousands with a non-breaking space

# The conversion preheaders, replacing each email's `pre`.
PRE = {
 "welcome-01": {
  "en": "Your 10% code is inside, and you have 5 days to use it.",
  "nl": "Je 10%-code zit erin, en je hebt 5 dagen om hem te gebruiken.",
  "fr": "Votre code 10% est à l'intérieur, et vous avez 5 jours pour l'utiliser.",
  "de": "Ihr 10%-Code ist enthalten, und Sie haben 5 Tage Zeit.",
  "es": "Tu código del 10% está dentro, y tienes 5 días para usarlo.",
  "it": "Il tuo codice 10% è dentro, e hai 5 giorni per usarlo."},
 "welcome-02": {
  "en": "Printed closer to you by a certified B Corp. Your 10% has 4 days left.",
  "nl": "Gedrukt dichter bij jou door een gecertificeerde B Corp. Je 10% is nog 4 dagen geldig.",
  "fr": "Imprimé plus près de vous par une B Corp certifiée. Vos 10% sont valables encore 4 jours.",
  "de": "Näher bei Ihnen gedruckt von einer zertifizierten B Corp. Ihre 10% gelten noch 4 Tage.",
  "es": "Impreso más cerca de ti por una B Corp certificada. Tu 10% vale 4 días más.",
  "it": "Stampato più vicino a te da una B Corp certificata. Il tuo 10% vale altri 4 giorni."},
 "welcome-03": {
  "en": "Rated 4.5 from 34,000+ reviews. Only 2 days left to use your 10%.",
  "nl": "Beoordeeld met 4,5 uit 34.000+ reviews. Nog maar 2 dagen om je 10% te gebruiken.",
  "fr": "Noté 4,5 sur 34" + NB + "000+ avis. Plus que 2 jours pour utiliser vos 10%.",
  "de": "Bewertet mit 4,5 aus 34.000+ Bewertungen. Nur noch 2 Tage für Ihre 10%.",
  "es": "Valorado con 4,5 de 34.000+ opiniones. Solo 2 días para usar tu 10%.",
  "it": "Valutato 4,5 su 34.000+ recensioni. Solo 2 giorni per usare il tuo 10%."},
 "welcome-04": {
  "en": "Artwork or just an idea, we take it from there. Last day for your 10%.",
  "nl": "Een ontwerp of alleen een idee, wij nemen het over. Laatste dag voor je 10%.",
  "fr": "Un visuel ou juste une idée, on prend le relais. Dernier jour pour vos 10%.",
  "de": "Eine Druckdatei oder nur eine Idee, wir übernehmen. Letzter Tag für Ihre 10%.",
  "es": "Un diseño o solo una idea, nos encargamos. Último día para tu 10%.",
  "it": "Un file o solo un'idea, ci pensiamo noi. Ultimo giorno per il tuo 10%."},
}

# Two new subjects. Day 0 and day 5 already read the way the ladder wants, so
# subj.wel1 and subj.wel4 are left alone.
SUBJ = {
 "subj.wel2": {
  "en": "Your 10% is waiting, and 4 days left to use it",
  "nl": "Je 10% staat klaar, en je hebt nog 4 dagen",
  "fr": "Vos 10% vous attendent, et il reste 4 jours",
  "de": "Ihre 10% warten, und Sie haben noch 4 Tage",
  "es": "Tu 10% te espera, y quedan 4 días",
  "it": "Il tuo 10% ti aspetta, e restano 4 giorni"},
 "subj.wel3": {
  "en": "Only 2 days left on your 10%",
  "nl": "Nog maar 2 dagen voor je 10%",
  "fr": "Plus que 2 jours pour vos 10%",
  "de": "Nur noch 2 Tage für Ihre 10%",
  "es": "Solo quedan 2 días para tu 10%",
  "it": "Solo 2 giorni per il tuo 10%"},
}

# The English preheader currently in each hand-written source file, which the
# substitution has to find in order to replace it.
OLD_EN_PRE = {
 "welcome-01": "Your 10% code is inside, and the prints most businesses start with.",
 "welcome-02": "Printed closer to you, a B Corp certification, and over 10,000 products.",
 "welcome-03": "Rated 4.5 on Trustpilot from 34,000+ reviews. Here is what a few of them say.",
 "welcome-04": "Artwork or just an idea. Send either and John&rsquo;s team takes it from there.",
}
