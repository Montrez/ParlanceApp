#!/usr/bin/env python3
"""Spanish journal-style pairs the first COWS train did not teach.

Exact judgment-gold sentences are omitted so eval stays honest.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

TRAINING_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TRAINING_DIR))

from gec_format import build_gec_example  # noqa: E402

OUT = TRAINING_DIR / "data" / "gec" / "es" / "targets.jsonl"


def add(rows: list, sentence: str, status: str, explanation: str, correction: str | None) -> None:
    rows.append(
        build_gec_example(
            "es",
            sentence,
            status=status,
            explanation=explanation,
            correction=correction,
            source="gec_targets",
        )
    )


def pair(rows: list, src: str, tgt: str, expl: str, leave: str) -> None:
    add(rows, src, "Needs Improvement", expl, tgt)
    add(rows, tgt, "Excellent", leave, None)


def main() -> None:
    rows: list[dict] = []
    leave = "The Spanish is already correct. Leave it unchanged."

    masc = [
        ("El problema", "problema"),
        ("El riesgo", "riesgo"),
        ("El hecho", "hecho"),
        ("El inconveniente", "inconveniente"),
        ("El punto positivo", "punto positivo"),
        ("El único problema", "único problema"),
        ("El inconveniente principal", "inconveniente"),
        ("El punto débil", "punto débil"),
        ("El punto negativo", "punto negativo"),
    ]
    fem = [
        ("La ventaja", "ventaja"),
        ("La desventaja", "desventaja"),
        ("La dificultad", "dificultad"),
        ("La razón", "razón"),
        ("La queja", "queja"),
        ("La preocupación", "preocupación"),
    ]
    clauses = [
        "no me preparé bien para la entrevista",
        "la reunión empezó tarde",
        "no me informé sobre la empresa",
        "el cliente no recibió el contrato",
        "calculamos mal el plazo",
        "olvidé confirmar la hora",
        "las dos partes hablaban a la vez",
        "el juez pidió que repitiera",
        "no entendí la dosis",
        "el testigo tenía miedo",
    ]
    for article_noun, noun in masc + fem:
        for clause in clauses:
            pair(
                rows,
                f"{article_noun} que {clause}.",
                f"{article_noun} es que {clause}.",
                f"Spanish needs the copula: «{article_noun} es que…», not «{article_noun} que…».",
                leave,
            )

    encantar = [
        ("Me encanta mis sobrinos", "Me encantan mis sobrinos"),
        ("Me encanta los niños", "Me encantan los niños"),
        ("Me gusta las clases", "Me gustan las clases"),
        ("Me gusta los jueces", "Me gustan los jueces"),
        ("Le encanta las audiencias", "Le encantan las audiencias"),
        ("Nos gusta los turnos", "Nos gustan los turnos"),
        ("Me encanta mis colegas", "Me encantan mis colegas"),
        ("Te gusta las reuniones", "Te gustan las reuniones"),
    ]
    tails = ["de verdad", "mucho", "este año", "en el hospital", "en el juzgado"]
    for src_a, tgt_a in encantar:
        for tail in tails:
            pair(
                rows,
                f"{src_a} {tail}.",
                f"{tgt_a} {tail}.",
                "Gustar and encantar agree with the thing liked, not the person.",
                leave,
            )

    past = [
        ("Ayer yo voy al juzgado", "Ayer yo fui al juzgado"),
        ("Ayer voy al hospital", "Ayer fui al hospital"),
        ("Ayer ella va a la comisaría", "Ayer ella fue a la comisaría"),
        ("Ayer nosotros vamos al palacio", "Ayer nosotros fuimos al palacio"),
        ("La semana pasada yo voy a Madrid", "La semana pasada yo fui a Madrid"),
        ("El año pasado voy a un congreso", "El año pasado fui a un congreso"),
        ("Ayer mañana voy al médico", "Ayer fui al médico"),
    ]
    for src, tgt in past:
        pair(
            rows,
            f"{src}.",
            f"{tgt}.",
            "A finished past event with ayer uses the preterite, not the present.",
            leave,
        )

    y_e = [
        ("fue muy divertido y interesante", "fue muy divertido e interesante"),
        ("es un abogado y intérprete", "es un abogado e intérprete"),
        ("necesito agua y hielo", "necesito agua e hielo"),
        ("habla inglés y italiano", "habla inglés e italiano"),
    ]
    for src, tgt in y_e:
        pair(rows, f"{src.capitalize()}.", f"{tgt.capitalize()}.", "Use e instead of y before a word starting with i.", leave)

    personal_a = [
        (
            "no puede dejar el puercoespín",
            "no puede dejar al puercoespín",
            "Personal a is required before a specific person or animal object.",
        ),
        (
            "vi el juez en el pasillo",
            "vi al juez en el pasillo",
            "Personal a before a person: al juez.",
        ),
        (
            "llamé la paciente por la tarde",
            "llamé a la paciente por la tarde",
            "Personal a before a person: a la paciente.",
        ),
        (
            "ayudé el testigo con el nombre",
            "ayudé al testigo con el nombre",
            "Personal a before a person: al testigo.",
        ),
    ]
    for src, tgt, expl in personal_a:
        pair(rows, f"{src[0].upper()}{src[1:]}.", f"{tgt[0].upper()}{tgt[1:]}.", expl, leave)

    for sentence in (
        "Gracias por su mensaje.",
        "¿Podría llamarme mañana por la mañana?",
        "Por favor, ¿puede confirmar la hora?",
        "Cordialmente,",
        "Las cartas que ella ha escrito están en el expediente.",
        "El punto negativo es que no estudié lo suficiente.",
        "La ventaja es que todos pueden conectarse.",
    ):
        add(rows, sentence, "Excellent", leave, None)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"wrote {len(rows)} → {OUT}")


if __name__ == "__main__":
    main()
