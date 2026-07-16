// Standalone regression for the cloud-path sanitizer (issue #31).
// `Parlance/FeedbackSanitizer.swift` is dependency-free (Foundation only), so it can be
// compiled and exercised here without the rest of the app target or Xcode.
//
// Run (swiftc requires the top-level-code file to be named main.swift):
//   dir=$(mktemp -d) && cp Parlance/FeedbackSanitizer.swift "$dir/" \
//     && cp scripts/test_feedback_sanitizer.swift "$dir/main.swift" \
//     && swiftc "$dir"/*.swift -o "$dir/test_bin" && "$dir/test_bin"

import Foundation

var failures = 0
var passed = 0

func check(_ name: String, _ condition: @autoclosure () -> Bool, _ detail: @autoclosure () -> String = "") {
    if condition() {
        passed += 1
        print("  OK    \(name)")
    } else {
        failures += 1
        print("  FAIL  \(name)  \(detail())")
    }
}

func sanitized(
    _ sentence: String,
    language: String = "es",
    level: String = "",
    feedback: [String: Any] = ["status": "Excellent", "explanation": "Looks fine."]
) -> [String: Any] {
    var out = feedback
    FeedbackSanitizer.sanitize(sentence: sentence, level: level, language: language, feedback: &out)
    return out
}

print("\nCloud-path sanitizer regression (FeedbackSanitizer)\n")

// MARK: - Known-error regex repairs (Spanish) — mirrors shared/coach-rules/es.json

do {
    let out = sanitized(
        "Si yo tendría más tiempo, estudiaría más.",
        feedback: ["status": "Excellent", "explanation": "Grammatically correct."]
    )
    check("si_clause_tendria: status flipped", out["status"] as? String == "Needs Improvement")
    check(
        "si_clause_tendria: correction has tuviera",
        (out["correction"] as? String ?? "").lowercased().contains("tuviera"),
        "got \(out["correction"] ?? "nil")"
    )
    check(
        "si_clause_tendria: rule id recorded",
        (out["_coach_rules"] as? [String])?.contains("si_clause_conditional_protasis") == true
    )
}

do {
    let out = sanitized(
        "Le echo de menos a mi novia.",
        feedback: ["status": "Excellent", "explanation": "No issues."]
    )
    check("leismo_novia: status flipped", out["status"] as? String == "Needs Improvement")
    check(
        "leismo_novia: correction uses la",
        (out["correction"] as? String ?? "").lowercased().contains("la echo de menos"),
        "got \(out["correction"] ?? "nil")"
    )
}

do {
    let out = sanitized(
        "Cómo es usted día señor. Quiero dinero a ver una película más tarde.",
        feedback: ["status": "Excellent", "explanation": "Fine."]
    )
    check("como_es_greeting: status flipped", out["status"] as? String == "Needs Improvement")
    let correction = (out["correction"] as? String ?? "")
    check("como_es_greeting: greeting repaired", correction.localizedCaseInsensitiveContains("cómo está"), correction)
    check("como_es_greeting: para repaired", correction.localizedCaseInsensitiveContains("para ver"), correction)
    let ids = out["_coach_rules"] as? [String] ?? []
    check("como_es_greeting: both rules recorded", ids.contains("greeting_vocative_order") && ids.contains("para_purpose_infinitive"), "\(ids)")
}

do {
    let out = sanitized(
        "Espero que todos ir bien por mi madre hoy.",
        feedback: ["status": "Excellent", "explanation": "Fine."]
    )
    check("espero_que_subjunctive: status flipped", out["status"] as? String == "Needs Improvement")
    check(
        "espero_que_subjunctive: correction has vayan",
        (out["correction"] as? String ?? "").lowercased().contains("vayan")
    )
}

// A cloud model that already caught the error and supplied a *correct* fix should be left alone
// (additive, not destructive) — its own correction must survive since it's not "weak".
do {
    let out = sanitized(
        "Si yo tendría más tiempo, estudiaría más.",
        feedback: [
            "status": "Needs Improvement",
            "explanation": "Si-clauses need imperfect subjunctive (tuviera), not conditional.",
            "correction": "Si yo tuviera más tiempo, estudiaría más.",
        ]
    )
    check(
        "si_clause_tendria: model's own good correction kept",
        out["correction"] as? String == "Si yo tuviera más tiempo, estudiaría más."
    )
}

// A sentence with no known-error pattern should not be touched.
do {
    let out = sanitized(
        "Hola señora, ¿cómo está?",
        feedback: ["status": "Excellent", "explanation": "Formal greeting, grammatically sound."]
    )
    check("correct_greeting: status unchanged", out["status"] as? String == "Excellent")
    check("correct_greeting: no rules fired", out["_coach_rules"] == nil)
}

// MARK: - French known-error repairs

do {
    let out = sanitized(
        "Si j'aurais le temps, je viendrais.",
        language: "fr",
        feedback: ["status": "Excellent", "explanation": "Correct."]
    )
    check("fr_si_clause: status flipped", out["status"] as? String == "Needs Improvement")
    check(
        "fr_si_clause: correction has j'avais",
        (out["correction"] as? String ?? "").lowercased().contains("j'avais"),
        "got \(out["correction"] ?? "nil")"
    )
}

do {
    let out = sanitized(
        "Comment allez-vous?",
        language: "fr",
        feedback: ["status": "Excellent", "explanation": "Correct."]
    )
    check("fr_typography: status flipped", out["status"] as? String == "Needs Improvement")
    check(
        "fr_typography: space inserted before ?",
        (out["correction"] as? String ?? "").contains("vous ?"),
        "got \(out["correction"] ?? "nil")"
    )
}

// MARK: - Hallucination detection

do {
    let out = sanitized(
        "Quiero comer pizza.",
        feedback: [
            "status": "Needs Improvement",
            "explanation": "The word 'xenoglossy' is misused here and 'quantum' should be reflexive.",
            "grammar_rule": "Reflexive verbs",
            "correction": "Quiero comer pizza.",
        ]
    )
    check(
        "hallucination: warning set",
        (out["_coach_warning"] as? String ?? "").contains("xenoglossy")
    )
    check(
        "hallucination: term scrubbed from explanation",
        !(out["explanation"] as? String ?? "").contains("xenoglossy")
    )
}

// MARK: - Register conflict

do {
    let out = sanitized(
        "Buenos días, señora, ¿cómo está?",
        feedback: [
            "status": "Excellent",
            "explanation": "Correct.",
            "register": "formal",
            "correction": "Buenos días, señora, ¿cómo estás?",
        ]
    )
    check("register_conflict: status flipped", out["status"] as? String == "Needs Improvement")
    check("register_conflict: correction stripped", out["correction"] == nil)
    check(
        "register_conflict: explanation notes mismatch",
        (out["explanation"] as? String ?? "").contains("Register mismatch")
    )
}

do {
    let out = sanitized(
        "Bonjour madame, comment allez-vous ?",
        language: "fr",
        feedback: [
            "status": "Excellent",
            "explanation": "Correct.",
            "register": "formal",
            "correction": "Bonjour madame, comment vas-tu ?",
        ]
    )
    check("fr_register_conflict: status flipped", out["status"] as? String == "Needs Improvement")
    check("fr_register_conflict: correction stripped", out["correction"] == nil)
}

// MARK: - CEFR plausibility (language-aware)

do {
    check(
        "cefr_es: implausible C2 on 4-word sentence rejected",
        !FeedbackSanitizer.assessedLevelPlausible(sentence: "Yo estoy bien.", level: "C2", language: "es")
    )
    check(
        "cefr_fr: plausible A1 on short present-tense sentence",
        FeedbackSanitizer.assessedLevelPlausible(sentence: "Je suis fatigué.", level: "A1", language: "fr")
    )
    check(
        "cefr_fr: implausible A1 with conditionnel",
        !FeedbackSanitizer.assessedLevelPlausible(sentence: "Si j'avais le temps, je serais content.", level: "A1", language: "fr")
    )
}

// MARK: - Verbatim next_level_alt stripping

do {
    let out = sanitized(
        "Hola señora, ¿cómo está?",
        feedback: [
            "status": "Excellent",
            "explanation": "Fine.",
            "next_level_alt": "Hola señora, ¿cómo está?",
        ]
    )
    check("verbatim_alt: stripped when identical to sentence", out["next_level_alt"] == nil)
}

print("\n\(passed) / \(passed + failures) passed\n")
if failures > 0 {
    exit(1)
}
print("All cloud-path sanitizer checks passed.")
