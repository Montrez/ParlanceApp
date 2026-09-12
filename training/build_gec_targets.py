#!/usr/bin/env python3
"""Journal-style French pairs for errors the first train could not have learned.

These are training examples, not inference rules. Exact judgment-gold sentences
are omitted so eval stays honest.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

TRAINING_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TRAINING_DIR))

from gec_format import build_gec_example, pair_to_example  # noqa: E402

OUT = TRAINING_DIR / "data" / "gec" / "fr" / "targets.jsonl"


def add(rows: list, sentence: str, status: str, explanation: str, correction: str | None) -> None:
    rows.append(
        build_gec_example(
            "fr",
            sentence,
            status=status,
            explanation=explanation,
            correction=correction,
            source="gec_targets",
        )
    )


def pair(rows: list, src: str, tgt: str, expl: str, leave_expl: str) -> None:
    """Always keep both sides. pair_to_example drops low-overlap calques."""
    add(rows, src, "Needs Improvement", expl, tgt)
    add(rows, tgt, "Excellent", leave_expl, None)


def main() -> None:
    rows: list[dict] = []

    nouns = [
        "problème",
        "souci",
        "avantage",
        "inconvénient",
        "risque",
        "constat",
        "fait",
        "point positif",
        "seul regret",
    ]
    clauses = [
        "je n'ai pas assez préparé le dossier",
        "la réunion a commencé en retard",
        "je ne me suis pas renseigné sur l'entreprise",
        "le client n'a pas reçu le contrat",
        "nous avons mal estimé le délai",
        "j'ai oublié de confirmer l'heure",
    ]
    for noun in nouns:
        for clause in clauses:
            src = f"Le {noun} que {clause}."
            tgt = f"Le {noun} est que {clause}."
            example = pair_to_example(
                "fr",
                src,
                tgt,
                explanation=(
                    f"French needs the copula: «Le {noun} est que…», not «Le {noun} que…»."
                ),
                source="gec_targets",
            )
            if example:
                rows.append(example)
            add(
                rows,
                tgt,
                "Excellent",
                f"«Le {noun} est que» is the correct copula. Leave it unchanged.",
                None,
            )

    participle_pairs = [
        (
            "Je me suis levé et habiller rapidement.",
            "Je me suis levé et habillé rapidement.",
            "After a pronominal passé composé, the coordinated verb stays a participle: habillé.",
        ),
        (
            "Elle s'est assise et regarder le contrat.",
            "Elle s'est assise et regardé le contrat.",
            "Keep the second verb as a participle after s'est assise: regardé.",
        ),
        (
            "Nous nous sommes préparés et renseigner sur le client.",
            "Nous nous sommes préparés et renseignés sur le client.",
            "After nous nous sommes préparés, use renseignés, not the infinitive renseigner.",
        ),
        (
            "Je me suis mal préparé et informer trop tard.",
            "Je me suis mal préparé et informé trop tard.",
            "Coordinated verb after être/se is a participle: informé.",
        ),
        (
            "Il s'est présenté et expliquer le projet.",
            "Il s'est présenté et expliqué le projet.",
            "After s'est présenté, the next verb is expliqué, not expliquer.",
        ),
        (
            "Je me suis rendu à l'entretien et présenter mon CV.",
            "Je me suis rendu à l'entretien et présenté mon CV.",
            "After je me suis rendu, keep présenté as a participle.",
        ),
    ]
    for src, tgt, expl in participle_pairs:
        example = pair_to_example("fr", src, tgt, explanation=expl, source="gec_targets")
        if example:
            rows.append(example)
        add(rows, tgt, "Excellent", "The participles already agree. Leave the sentence unchanged.", None)

    truncations = [
        (
            "Pouvez-vous m'envoyer l'appel d'offr demain matin ?",
            "Pouvez-vous m'envoyer l'appel d'offre demain matin ?",
            "The noun is truncated: offr → offre. Keep the rest of the request.",
        ),
        (
            "Voici l'appel d'offr pour le marché public.",
            "Voici l'appel d'offre pour le marché public.",
            "Spelling: appel d'offre, not appel d'offr.",
        ),
        (
            "J'ai lu l'offr d'emploi hier soir.",
            "J'ai lu l'offre d'emploi hier soir.",
            "Restore the missing letter: offre, not offr.",
        ),
        (
            "Merci de transmettre l'appel d offr au service achats.",
            "Merci de transmettre l'appel d'offre au service achats.",
            "Complete the noun offre and keep the polite request.",
        ),
        (
            "Je travaille dans cette sociét depuis mars.",
            "Je travaille dans cette société depuis mars.",
            "Spelling: société, not sociét.",
        ),
        (
            "Le rendez-vou est confirmé à 10 h.",
            "Le rendez-vous est confirmé à 10 h.",
            "The noun is truncated: rendez-vous, not rendez-vou.",
        ),
        (
            "Pouvez-vous signer le contra aujourd'hui ?",
            "Pouvez-vous signer le contrat aujourd'hui ?",
            "Spelling: contrat, not contra.",
        ),
        (
            "J'attends encore la factur de la traduction.",
            "J'attends encore la facture de la traduction.",
            "Spelling: facture, not factur.",
        ),
        (
            "Le documen est en pièce jointe.",
            "Le document est en pièce jointe.",
            "Spelling: document, not documen.",
        ),
        (
            "Nous avons reçu l'entrepris ce matin.",
            "Nous avons reçu l'entreprise ce matin.",
            "Spelling: entreprise, not entrepris in this noun slot.",
        ),
    ]
    for src, tgt, expl in truncations:
        example = pair_to_example("fr", src, tgt, explanation=expl, source="gec_targets")
        if example:
            rows.append(example)
        add(rows, tgt, "Excellent", "The professional wording is already complete. Leave it unchanged.", None)

    leave = "The French is already correct. Leave it unchanged."

    actors = [
        "Je dois",
        "Tu dois",
        "Il doit",
        "Elle doit",
        "Nous devons",
        "Vous devez",
        "Ils doivent",
        "On doit",
        "Le juge doit",
        "La patiente doit",
        "Mon collègue doit",
        "L'interprète doit",
    ]
    when = [
        "aujourd'hui",
        "avant lundi",
        "avant l'audience",
        "ce soir",
        "en fin de journée",
        "avant de partir",
        "avec l'équipe",
        "rapidement",
        "avant le verdict",
        "ce matin",
        "sans attendre",
        "avant vendredi",
    ]
    for actor in actors:
        for w in when:
            pair(
                rows,
                f"{actor} faire une décision {w}.",
                f"{actor} prendre une décision {w}.",
                "French says prendre une décision, not faire une décision.",
                leave,
            )
    past_actors = [
        ("J'ai fait", "J'ai pris"),
        ("Tu as fait", "Tu as pris"),
        ("Il a fait", "Il a pris"),
        ("Elle a fait", "Elle a pris"),
        ("Nous avons fait", "Nous avons pris"),
        ("Vous avez fait", "Vous avez pris"),
        ("Ils ont fait", "Ils ont pris"),
        ("On a fait", "On a pris"),
        ("Le client a fait", "Le client a pris"),
        ("L'équipe a fait", "L'équipe a pris"),
    ]
    past_when = [
        "trop vite",
        "hier soir",
        "ensemble",
        "pendant la pause",
        "après l'audience",
        "sans consulter le dossier",
        "ce matin",
        "en cinq minutes",
    ]
    for src_a, tgt_a in past_actors:
        for w in past_when:
            pair(
                rows,
                f"{src_a} une décision {w}.",
                f"{tgt_a} une décision {w}.",
                "Use prendre une décision, not faire une décision.",
                leave,
            )
    besoin_actors = [
        "J'ai besoin de",
        "Tu as besoin de",
        "Il a besoin de",
        "Elle a besoin de",
        "Nous avons besoin de",
        "Vous avez besoin de",
        "On a besoin de",
        "Le juge a besoin de",
        "La patiente a besoin de",
    ]
    besoin_when = [
        "ce soir",
        "avant lundi",
        "avant l'audience",
        "rapidement",
        "ce matin",
        "avant vendredi",
        "sans attendre",
        "en équipe",
    ]
    for actor in besoin_actors:
        for w in besoin_when:
            pair(
                rows,
                f"{actor} faire une décision {w}.",
                f"{actor} prendre une décision {w}.",
                "French says prendre une décision, not faire une décision.",
                leave,
            )

    future_actors = [
        ("Il va faire", "Il va prendre"),
        ("Elle va faire", "Elle va prendre"),
        ("Nous allons faire", "Nous allons prendre"),
        ("Je vais faire", "Je vais prendre"),
        ("On va faire", "On va prendre"),
        ("Le juge va faire", "Le juge va prendre"),
    ]
    for src_a, tgt_a in future_actors:
        for w in ("en équipe", "demain", "ce soir", "avant midi"):
            pair(
                rows,
                f"{src_a} une décision {w}.",
                f"{tgt_a} une décision {w}.",
                "English 'make a decision' is prendre une décision.",
                leave,
            )

    excited = [
        ("Je suis excité pour", "J'ai hâte d'aller à"),
        ("Tu es excité pour", "Tu as hâte d'aller à"),
        ("Il est excité pour", "Il a hâte d'aller à"),
        ("Elle est excitée pour", "Elle a hâte d'aller à"),
        ("Nous sommes excités pour", "Nous avons hâte d'aller à"),
        ("Vous êtes excités pour", "Vous avez hâte d'aller à"),
        ("Ils sont excités pour", "Ils ont hâte d'aller à"),
        ("On est excité pour", "On a hâte d'aller à"),
    ]
    events = [
        "la formation",
        "la réunion",
        "l'audience",
        "le stage",
        "le congrès",
        "la conférence",
        "le cours",
        "la visite",
        "l'entretien",
        "la séance",
    ]
    event_when = ["de demain", "de lundi", "de cet après-midi", "de la semaine prochaine"]
    for src_a, tgt_a in excited:
        for event in events:
            for w in event_when:
                pair(
                    rows,
                    f"{src_a} {event} {w}.",
                    f"{tgt_a} {event} {w}.",
                    "Excité is a false friend here. Use avoir hâte.",
                    leave,
                )
    add(
        rows,
        "L'enfant est trop excité pour s'endormir.",
        "Excellent",
        "Excité is correct for overstimulated. Leave it unchanged.",
        None,
    )
    add(
        rows,
        "Le chien est excité par le bruit dans le couloir.",
        "Excellent",
        "Excité is correct for agitated. Leave it unchanged.",
        None,
    )

    realized = [
        ("J'ai réalisé que", "Je me suis rendu compte que"),
        ("Tu as réalisé que", "Tu t'es rendu compte que"),
        ("Il a réalisé que", "Il s'est rendu compte que"),
        ("Elle a réalisé que", "Elle s'est rendu compte que"),
        ("Nous avons réalisé que", "Nous nous sommes rendu compte que"),
        ("Vous avez réalisé que", "Vous vous êtes rendu compte que"),
        ("Ils ont réalisé que", "Ils se sont rendu compte que"),
        ("On a réalisé que", "On s'est rendu compte que"),
        ("Le juge a réalisé que", "Le juge s'est rendu compte que"),
        ("La patiente a réalisé que", "La patiente s'est rendu compte que"),
        ("Mon collègue a réalisé que", "Mon collègue s'est rendu compte que"),
    ]
    realized_clauses = [
        "le délai était trop court",
        "le patient avait peur",
        "la consigne était floue",
        "le contrat n'était pas signé",
        "nous étions en retard",
        "le mot manquait",
        "l'horaire avait changé",
        "le témoin ne comprenait pas",
        "la salle était pleine",
        "le dossier était incomplet",
        "j'avais oublié le nom",
        "elle ne pouvait plus attendre",
    ]
    for src_a, tgt_a in realized:
        for clause in realized_clauses:
            pair(
                rows,
                f"{src_a} {clause}.",
                f"{tgt_a} {clause}.",
                "For 'realized that', use se rendre compte, not réaliser.",
                leave,
            )
    for sentence in (
        "Elle a réalisé un documentaire sur l'hôpital.",
        "Nous avons réalisé le projet à temps.",
        "Ils ont réalisé une étude de marché.",
        "Cette équipe a réalisé un travail remarquable.",
        "Il a réalisé son premier film l'an dernier.",
    ):
        add(rows, sentence, "Excellent", "Réaliser a project or work is correct French. Leave it unchanged.", None)

    other_calques = [
        (
            "Je dois supporter mon collègue pendant l'audience.",
            "Je dois soutenir mon collègue pendant l'audience.",
            "Supporter means to endure. To support a person is soutenir.",
        ),
        (
            "Elle va supporter sa mère à l'hôpital.",
            "Elle va soutenir sa mère à l'hôpital.",
            "To support a person is soutenir, not supporter.",
        ),
        (
            "Actuellement, je voulais dire le contraire.",
            "En fait, je voulais dire le contraire.",
            "Actuellement means currently, not actually.",
        ),
        (
            "Actuellement, ce n'est pas ce que j'ai dit.",
            "En fait, ce n'est pas ce que j'ai dit.",
            "Actuellement means currently, not actually.",
        ),
        (
            "Peux-tu payer attention au registre ?",
            "Peux-tu faire attention au registre ?",
            "French says faire attention, not payer attention.",
        ),
        (
            "Il faut payer attention aux dates.",
            "Il faut faire attention aux dates.",
            "Use faire attention, not payer attention.",
        ),
        (
            "Je vais visiter mon oncle à l'hôpital.",
            "Je vais rendre visite à mon oncle à l'hôpital.",
            "Visiter a person is rendre visite. Visiter is for places.",
        ),
        (
            "Nous visitons la juge demain matin.",
            "Nous rendons visite à la juge demain matin.",
            "Rendre visite à someone. Visiter is for places.",
        ),
        (
            "Elle a demandé une question au juge.",
            "Elle a posé une question au juge.",
            "Pose a question: poser une question, not demander une question.",
        ),
        (
            "J'ai demandé une question au médecin.",
            "J'ai posé une question au médecin.",
            "Use poser une question, not demander une question.",
        ),
    ]
    for src, tgt, expl in other_calques:
        pair(rows, src, tgt, expl, leave)

    nouns_bq = [
        ("la situation", "difficile"),
        ("le dossier", "incomplet"),
        ("l'audience", "longue"),
        ("la réunion", "tendue"),
        ("le délai", "court"),
        ("la consigne", "floue"),
        ("le contrat", "prêt"),
        ("l'horaire", "fixe"),
        ("la salle", "pleine"),
        ("le verdict", "clair"),
    ]
    tails_bq = [
        "nous continuons",
        "nous avançons",
        "je reste calme",
        "le travail continue",
        "on prépare la suite",
        "je prends des notes",
    ]
    for noun, adj in nouns_bq:
        for tail in tails_bq:
            pair(
                rows,
                f"Bien que {noun} est {adj}, {tail}.",
                f"Bien que {noun} soit {adj}, {tail}.",
                "Bien que takes the subjunctive: soit, not est.",
                leave,
            )
    think_verbs = ["pense", "crois", "trouve"]
    think_who = [
        ("il a", "il ait"),
        ("elle a", "elle ait"),
        ("on a", "on ait"),
        ("le juge a", "le juge ait"),
        ("la patiente a", "la patiente ait"),
    ]
    think_tails = [
        "raison",
        "compris la consigne",
        "déjà signé",
        "vu le dossier",
        "fini le compte rendu",
        "entendu le nom",
    ]
    for verb in think_verbs:
        for src_w, tgt_w in think_who:
            for tail in think_tails:
                pair(
                    rows,
                    f"Je ne {verb} pas qu'{src_w} {tail}.",
                    f"Je ne {verb} pas qu'{tgt_w} {tail}.",
                    "Negated belief takes the subjunctive: ait, not a.",
                    leave,
                )
    faut_pairs = [
        ("nous faisons", "nous fassions", "plus d'efforts"),
        ("vous faites", "vous fassiez", "le résumé ce soir"),
        ("tu viens", "tu viennes", "avec moi"),
        ("il vient", "il vienne", "demain matin"),
        ("elle finit", "elle finisse", "avant midi"),
        ("on part", "on parte", "tout de suite"),
        ("ils restent", "ils restent", "dans la salle"),
    ]
    for src_v, tgt_v, tail in faut_pairs:
        if src_v == tgt_v:
            add(
                rows,
                f"Il faut que {src_v} {tail}.",
                "Excellent",
                "The subjunctive is already correct. Leave it unchanged.",
                None,
            )
            continue
        pair(
            rows,
            f"Il faut que {src_v} {tail}.",
            f"Il faut que {tgt_v} {tail}.",
            "Il faut que takes the subjunctive.",
            leave,
        )
    pair(
        rows,
        "Je veux que tu viens avec moi ce soir.",
        "Je veux que tu viennes avec moi ce soir.",
        "Vouloir que takes the subjunctive: viennes.",
        leave,
    )
    pair(
        rows,
        "Pour que le client comprend, je ralentis.",
        "Pour que le client comprenne, je ralentis.",
        "Pour que takes the subjunctive: comprenne.",
        leave,
    )
    add(
        rows,
        "Avant que le juge commence, je prépare mes notes.",
        "Excellent",
        "Avant que already has the subjunctive. Leave it unchanged.",
        None,
    )

    future_cmds = [
        ("Appelle-moi", "arrives", "arriveras", "à la gare"),
        ("Préviens-moi", "arrives", "arriveras", "à l'hôpital"),
        ("Dis-lui", "rentres", "rentreras", "ce soir"),
        ("Écris-moi", "finis", "finiras", "le compte rendu"),
        ("Préviens-nous", "pars", "partiras", "demain matin"),
        ("Appelle-la", "sors", "sortiras", "du tribunal"),
        ("Dis-moi", "reviens", "reviendras", "de pause"),
        ("Préviens-moi", "termines", "termineras", "l'entretien"),
    ]
    future_when = ["demain", "demain soir", "cet après-midi", "lundi", "tout à l'heure"]
    for cmd, src_v, tgt_v, place in future_cmds:
        for w in future_when:
            pair(
                rows,
                f"{cmd} quand tu {src_v} {place} {w}.",
                f"{cmd} quand tu {tgt_v} {place} {w}.",
                "Quand with a future event takes the future tense.",
                leave,
            )
    imparfait = [
        ("enfant", "lis", "lisais", "tous les soirs"),
        ("stagiaire", "prends", "prenais", "des notes tous les jours"),
        ("étudiant", "vais", "allais", "à la bibliothèque"),
        ("petit", "joue", "jouais", "dans la cour"),
        ("apprenti", "écoute", "écoutais", "le juge"),
        ("débutant", "fais", "faisais", "beaucoup d'erreurs"),
        ("enfant", "regarde", "regardais", "les mêmes films"),
        ("collégien", "écris", "écrivais", "un journal"),
    ]
    for when_i, src_v, tgt_v, tail in imparfait:
        pair(
            rows,
            f"Quand j'étais {when_i}, je {src_v} {tail}.",
            f"Quand j'étais {when_i}, je {tgt_v} {tail}.",
            "Habitual past after quand j'étais needs the imparfait.",
            leave,
        )
    past_pc = [
        ("Hier", "je vais au commissariat", "je suis allé au commissariat"),
        ("Hier", "je vais au tribunal", "je suis allé au tribunal"),
        ("Hier soir", "je vais à l'hôpital", "je suis allé à l'hôpital"),
        ("L'année dernière", "je vais à Lyon pour un congrès", "je suis allé à Lyon pour un congrès"),
        ("La semaine dernière", "je vais à Paris", "je suis allé à Paris"),
        ("Hier", "nous allons au palais", "nous sommes allés au palais"),
        ("Hier matin", "elle va chez le médecin", "elle est allée chez le médecin"),
    ]
    for when_p, src, tgt in past_pc:
        pair(
            rows,
            f"{when_p} {src}.",
            f"{when_p} {tgt}.",
            "A finished past event uses passé composé, not the present.",
            leave,
        )

    places = [
        "à l'hôpital",
        "au palais de justice",
        "en cardiologie",
        "en correctionnelle",
        "au commissariat",
        "en simultanée",
        "pour un témoin",
        "pour une patiente",
        "au tribunal",
        "en consultation",
    ]
    for place in places:
        pair(
            rows,
            f"Demain je dois interpreter {place}.",
            f"Demain je dois interpréter {place}.",
            "The verb is interpréter, not interpreter.",
            leave,
        )
        pair(
            rows,
            f"Ce matin j'ai interpreter {place}.",
            f"Ce matin j'ai interprété {place}.",
            "Past participle of interpréter is interprété.",
            leave,
        )
        pair(
            rows,
            f"Je vais interpreter {place} cet après-midi.",
            f"Je vais interpréter {place} cet après-midi.",
            "Spelling: interpréter.",
            leave,
        )
    ne_drop = [
        ("j'étais pas sûr du mot", "je n'étais pas sûr du mot"),
        ("j'étais pas certain du terme", "je n'étais pas certain du terme"),
        ("j'étais pas prêt pour le discours rapide", "je n'étais pas prêt pour le discours rapide"),
        ("j'étais pas capable de suivre", "je n'étais pas capable de suivre"),
        ("j'étais pas à l'aise", "je n'étais pas à l'aise"),
        ("je savais pas le mot", "je ne savais pas le mot"),
        ("je pouvais pas interrompre", "je ne pouvais pas interrompre"),
        ("c'était pas clair", "ce n'était pas clair"),
    ]
    heads = [
        "Le juge m'a demandé de répéter, mais",
        "Le médecin m'a demandé de ralentir, mais",
        "L'avocate m'a interrompu, mais",
        "Le client a parlé trop vite, mais",
    ]
    for head in heads:
        for src, tgt in ne_drop[:5]:
            pair(
                rows,
                f"{head} {src}.",
                f"{head} {tgt}.",
                "Written French keeps ne in the negation.",
                leave,
            )
    for src, tgt in ne_drop[5:]:
        pair(rows, f"{src.capitalize()}.", f"{tgt[0].upper() + tgt[1:]}.", "Restore ne in written French.", leave)
    subjects_pl = [
        ("les deux", "parlait", "parlaient"),
        ("les deux avocats", "parlait", "parlaient"),
        ("les deux parties", "parlait", "parlaient"),
        ("les médecins", "parlait", "parlaient"),
        ("les interprètes", "arrivait", "arrivaient"),
        ("les témoins", "répondait", "répondaient"),
        ("les collègues", "prenait", "prenaient"),
    ]
    for subj, src_v, tgt_v in subjects_pl:
        pair(
            rows,
            f"J'ai eu du mal à suivre parce que {subj} {src_v} en même temps.",
            f"J'ai eu du mal à suivre parce que {subj} {tgt_v} en même temps.",
            "Plural subject takes the plural verb.",
            leave,
        )
    for sentence in (
        "La patiente m'a remercié et j'ai gardé une distance professionnelle.",
        "Le juge a parlé lentement et j'ai pris des notes.",
        "J'ai interprété en consécutive pendant une heure.",
        "Après l'audience j'ai noté les termes à revoir.",
        "Le médecin a expliqué le traitement et j'ai tout rendu.",
        "Je suis resté neutre pendant toute la séance.",
        "Nous avons préparé le glossaire avant l'entretien.",
        "La famille a posé beaucoup de questions.",
    ):
        add(rows, sentence, "Excellent", "This journal sentence is already correct French. Leave it unchanged.", None)

    politeness = [
        "Merci beaucoup.",
        "Je vous remercie pour votre retour.",
        "Bien à vous.",
        "Cordialement,",
        "S'il vous plaît, pouvez-vous confirmer ?",
        "Pourriez-vous m'appeler s'il vous plaît ?",
        "Merci d'avance.",
        "Je vous prie d'agréer mes salutations distinguées.",
    ]
    for sentence in politeness:
        add(
            rows,
            sentence,
            "Excellent",
            "This is correct polite French. Do not rewrite the closing or the courtesy formula.",
            None,
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"wrote {len(rows)} → {OUT}")


if __name__ == "__main__":
    main()
