import Foundation

/// Cloud-path parity layer for `ExternalAnalyzer` (issue #31): hallucination detection,
/// known-error regex repairs, and register-conflict repair — the same class of checks the
/// on-device validator applies (`ParlanceSLMFeedbackValidator.swift`). Known-error detect/repair
/// now delegates to `CoachRulesEngine`, which loads the *full* shared rule packs
/// (`shared/coach-rules/{es,fr}.json`) instead of a hand-ported subset — Phase 1 of the
/// consolidation plan in `docs/coach-heuristic-consolidation.md` (issue #30/#32).
///
/// Deliberately Foundation-only and dependency-free (no `AIProvider`/`LanguageRegistry`) so it
/// can be exercised by a standalone script (see `scripts/test_feedback_sanitizer.swift`) without
/// pulling in the rest of the app target, and so it is a candidate single sanitizer for both the
/// cloud and on-device paths per the consolidation note in issue #31.
enum FeedbackSanitizer {

    // MARK: - CEFR plausibility (language-aware)

    static let validCEFRLevels = ["A1", "A2", "B1", "B2", "C1", "C2"]

    static func normalizeAssessedLevel(_ raw: String?) -> String? {
        guard let raw else { return nil }
        let u = raw.uppercased().trimmingCharacters(in: .whitespacesAndNewlines)
        return validCEFRLevels.contains(u) ? u : nil
    }

    /// Reject CEFR labels that clearly mismatch sentence structure — never invent levels, only
    /// filter obvious mismatches. Mirrors `ParlanceSLMFeedbackValidator.assessedLevelPlausible*`.
    static func assessedLevelPlausible(sentence: String, level: String, language: String) -> Bool {
        switch language {
        case "fr":
            return assessedLevelPlausibleFrench(sentence: sentence, level: level)
        case "en":
            return assessedLevelPlausibleEnglish(sentence: sentence, level: level)
        default:
            return assessedLevelPlausibleSpanish(sentence: sentence, level: level)
        }
    }

    /// Rougher than the ES/FR heuristics (no fine-tuned on-device English model exists yet —
    /// see issue #11 — so there's no training-data-derived vocabulary list to lean on), but
    /// keeps the same "never invent, only reject implausible" philosophy: word count plus
    /// coarse subordinator/conditional/modal-perfect signals.
    private static func assessedLevelPlausibleEnglish(sentence: String, level: String) -> Bool {
        let norm = normalizeForCompare(sentence)
        let wordCount = sentence.split(whereSeparator: { $0.isWhitespace }).count
        let hasSub = norm.range(
            of: #"\b(because|since|although|though|while|when|whereas|if)\b"#,
            options: .regularExpression
        ) != nil
        let hasConditional = norm.range(of: #"\bwould\b"#, options: .regularExpression) != nil
        let hasModalPerfect = norm.range(
            of: #"\b(had|would have|could have|should have|might have)\b"#,
            options: .regularExpression
        ) != nil

        switch level.uppercased() {
        case "A1":
            return wordCount <= 8 && !hasSub && !hasConditional && !hasModalPerfect
        case "A2":
            return wordCount <= 12 && !hasConditional
        case "B1", "B2":
            return true
        case "C1":
            return hasConditional || (hasSub && wordCount >= 12) || hasModalPerfect
        case "C2":
            if wordCount >= 14, hasSub,
               norm.range(
                   of: #"\b(nonetheless|notwithstanding|albeit|insofar|whereby)\b"#,
                   options: .regularExpression
               ) != nil {
                return true
            }
            return hasConditional || (hasSub && wordCount >= 12) || hasModalPerfect
        default:
            return false
        }
    }

    private static func assessedLevelPlausibleSpanish(sentence: String, level: String) -> Bool {
        let norm = normalizeForCompare(sentence)
        let wordCount = sentence.split(whereSeparator: { $0.isWhitespace }).count
        let hasSub = hasSubordinator(sentence)
        let hasSubjunctive = norm.range(
            of: #"\b(hubiera|tuviera|fuera|pudiera|quisiera|hiciera|hubiese|tuviese)\b"#,
            options: .regularExpression
        ) != nil
        let hasConditional = norm.range(
            of: #"\b(habria|tendria|seria|podria)\b"#,
            options: .regularExpression
        ) != nil
        let hasPreterite = norm.range(
            of: #"\b(fui|fue|hice|hizo|estuve|estuvo|pude|pudo|quise|quiso|vine|vino|dije|dijo)\b"#,
            options: .regularExpression
        ) != nil

        switch level.uppercased() {
        case "A1":
            return wordCount <= 8 && !hasSub && !hasSubjunctive && !hasConditional && !hasPreterite
        case "A2":
            return wordCount <= 12 && !hasSubjunctive
        case "B1", "B2":
            return true
        case "C1":
            if isMedicalRegister(sentence, language: "es"), wordCount >= 8 { return true }
            return hasSubjunctive || (hasSub && wordCount >= 12) || hasConditional
        case "C2":
            if wordCount >= 14, hasSub,
               norm.range(
                   of: #"\b(arbitraje|vinculante|renuncien|estipulado|medida en que)\b"#,
                   options: .regularExpression
               ) != nil {
                return true
            }
            return hasSubjunctive || (hasSub && wordCount >= 12) || hasConditional
        default:
            return false
        }
    }

    private static func assessedLevelPlausibleFrench(sentence: String, level: String) -> Bool {
        let norm = normalizeForCompare(sentence)
        let wordCount = sentence.split(whereSeparator: { $0.isWhitespace }).count
        let hasSub = hasSubordinator(sentence)
        let hasSubjunctive = norm.range(
            of: #"\b(eut|fut|soit|ait|eussent|fussent|vinssent)\b"#,
            options: .regularExpression
        ) != nil
        let hasConditional = norm.range(
            of: #"\b(aurais|aurait|aurions|auriez|serais|serait|ferais|ferait)\b"#,
            options: .regularExpression
        ) != nil
        let hasPasse = norm.range(of: #"\b(suis alle|est alle)\b"#, options: .regularExpression) != nil

        switch level.uppercased() {
        case "A1":
            return wordCount <= 8 && !hasSub && !hasSubjunctive && !hasConditional && !hasPasse
        case "A2":
            return wordCount <= 12 && !hasSubjunctive
        case "B1", "B2":
            return true
        case "C1":
            if isMedicalRegister(sentence, language: "fr"), wordCount >= 8 { return true }
            return hasSubjunctive || (hasSub && wordCount >= 12) || hasConditional
        case "C2":
            if isMedicalRegister(sentence, language: "fr"), wordCount >= 8 { return true }
            if wordCount >= 14, hasSub,
               norm.range(of: #"\b(arbitrage|stipulations|obligatoire)\b"#, options: .regularExpression) != nil {
                return true
            }
            return hasSubjunctive || (hasSub && wordCount >= 12) || hasConditional
        default:
            return false
        }
    }

    private static func isMedicalRegister(_ sentence: String, language: String) -> Bool {
        let norm = normalizeForCompare(sentence)
        if language == "fr" {
            return norm.range(
                of: #"\b(patient|ains|medicament|chirurg|intervention|diagnostic)\b"#,
                options: .regularExpression
            ) != nil
        }
        return norm.range(
            of: #"\b(paciente|aines|medicamento|cirugia|intervencion|diagnostico)\b"#,
            options: .regularExpression
        ) != nil
    }

    private static func hasSubordinator(_ sentence: String) -> Bool {
        let n = " " + normalizeForCompare(sentence) + " "
        let markers = [
            " porque ", " pues ", " que ", " qu ", " cuando ", " si ", " aunque ",
            " mientras ", " lo cual ", " donde ", " como ", " sino ",
            " lorsque ", " puisque ", " bien que ", " fait que ", " fait qu ", " el hecho de que ",
        ]
        return markers.contains { n.contains($0) }
    }

    // MARK: - Normalization / tokens

    static func normalizeForCompare(_ text: String) -> String {
        text.lowercased()
            .folding(options: .diacriticInsensitive, locale: .current)
            .replacingOccurrences(of: #"[^\w\s]"#, with: " ", options: .regularExpression)
            .replacingOccurrences(of: #"\s+"#, with: " ", options: .regularExpression)
            .trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private static let stopwords: Set<String> = [
        "the", "and", "for", "with", "requires", "appropriate", "correct", "formal",
        "informal", "professional", "grammar", "spanish", "french", "english", "sentence", "learner",
        "a", "al", "con", "de", "del", "el", "en", "es", "la", "las", "lo", "los", "que", "y",
    ]

    private static func tokens(_ text: String) -> Set<String> {
        Set(
            normalizeForCompare(text)
                .split(separator: " ")
                .map(String.init)
                .filter { $0.count >= 3 && !stopwords.contains($0) }
        )
    }

    static func isUnrelatedRewrite(sentence: String, alt: String?) -> Bool {
        guard let alt, !alt.trimmingCharacters(in: .whitespaces).isEmpty else { return false }
        let sw = tokens(sentence)
        let aw = tokens(alt)
        guard !sw.isEmpty, !aw.isEmpty else { return false }
        let overlap = sw.intersection(aw)
        let minOverlap = sw.count >= 3 ? 2 : 1
        return overlap.count < minOverlap
    }

    // MARK: - Hallucination detection

    /// Find quoted terms in the model's own explanatory text that don't actually appear in the
    /// learner's sentence — a strong signal the model hallucinated a word or phrase.
    static func findHallucinatedTerms(sentence: String, texts: [String]) -> [String] {
        let sentNorm = normalizeForCompare(sentence)
        let sentTokens = tokens(sentence)
        var bad: [String] = []
        let pattern = #"'([^']{3,})'|"([^"]{3,})"|«([^»]{3,})»"#
        guard let regex = try? NSRegularExpression(pattern: pattern) else { return [] }

        for text in texts {
            let ns = text as NSString
            let matches = regex.matches(in: text, range: NSRange(location: 0, length: ns.length))
            for m in matches {
                let term: String
                if m.range(at: 1).location != NSNotFound {
                    term = ns.substring(with: m.range(at: 1))
                } else if m.range(at: 2).location != NSNotFound {
                    term = ns.substring(with: m.range(at: 2))
                } else {
                    term = ns.substring(with: m.range(at: 3))
                }
                let core = normalizeForCompare(term)
                guard core.count >= 3 else { continue }
                if sentNorm.contains(core) || sentTokens.contains(core) { continue }
                let parts = core.split(separator: " ").map(String.init).filter { $0.count >= 4 }
                if parts.contains(where: { sentNorm.contains($0) }) { continue }
                bad.append(term)
            }
        }
        return bad
    }

    // MARK: - Register conflict

    /// True when the sentence's evidenced register (formal usted/vous vs informal tú/vos/tu)
    /// conflicts with what the model's `correction` or `register` field claims.
    static func detectRegisterConflict(sentence: String, feedback: [String: Any], language: String) -> Bool {
        switch language {
        case "fr":
            return detectRegisterConflictFrench(sentence: sentence, feedback: feedback)
        case "en":
            // English formal/informal register isn't a tú/vous-style binary morphology switch —
            // out of scope for this heuristic; the model's own register commentary stands.
            return false
        default:
            return detectRegisterConflictSpanish(sentence: sentence, feedback: feedback)
        }
    }

    private static func detectRegisterConflictSpanish(sentence: String, feedback: [String: Any]) -> Bool {
        let sent = normalizeForCompare(sentence)
        let corr = normalizeForCompare(feedback["correction"] as? String ?? "")
        let formalMarkers = ["usted", "senor", "senora", "don ", "dona "]
        let sentFormal = formalMarkers.contains(where: { sent.contains($0) })
            || sent.contains(" esta") || sent.hasSuffix("esta")
        let sentInformal = sent.contains(" estas")
            || sent.range(of: #"\b(tu|vos)\b"#, options: .regularExpression) != nil
        let reg = normalizeForCompare(feedback["register"] as? String ?? "")
        let claimsFormal = reg.contains("formal") && !reg.contains("informal")
        let corrInformal = corr.contains("estas")
        let corrFormal = corr.contains("usted") || corr.contains(" esta usted")

        if sentFormal && !sentInformal && corrInformal && !corrFormal { return true }
        if claimsFormal && corrInformal && !corrFormal { return true }
        return false
    }

    private static func detectRegisterConflictFrench(sentence: String, feedback: [String: Any]) -> Bool {
        let sent = normalizeForCompare(sentence)
        let corr = normalizeForCompare(feedback["correction"] as? String ?? "")
        let sentFormal = sent.range(of: #"\b(vous|madame|monsieur)\b"#, options: .regularExpression) != nil
        let sentInformal = sent.range(of: #"\b(tu|toi|ton|ta|tes)\b"#, options: .regularExpression) != nil
        let reg = normalizeForCompare(feedback["register"] as? String ?? "")
        let claimsFormal = reg.contains("formal") && !reg.contains("informal")
        let corrInformal = corr.range(of: #"\btu\b"#, options: .regularExpression) != nil
        let corrFormal = corr.contains("vous")

        if sentFormal && !sentInformal && corrInformal && !corrFormal { return true }
        if claimsFormal && corrInformal && !corrFormal { return true }
        return false
    }

    // MARK: - Known-error regex repairs — delegates to CoachRulesEngine, which loads the full
    // shared/coach-rules/{es,fr}.json packs (Phase 1 of the #30 consolidation plan). Previously
    // this hand-ported a ~5-rule ES / 2-rule FR subset directly; that duplication is gone.

    struct DetectedIssue {
        let id: String
        let grammarRule: String
        let issue: String
        let mentions: [String]
    }

    static func detectKnownIssues(sentence: String, language: String) -> [DetectedIssue] {
        CoachRulesEngine.detectIssues(sentence: sentence, language: language).map {
            DetectedIssue(id: $0.id, grammarRule: $0.grammarRule, issue: $0.issue, mentions: $0.mentions)
        }
    }

    static func applyKnownRepairs(sentence: String, language: String) -> String {
        CoachRulesEngine.applyRepairs(sentence: sentence, language: language)
    }

    /// Additively merge ground-truth known-error repairs into cloud feedback: keeps the model's
    /// own explanation/tip when present, but appends any issues the model missed, forces a
    /// deterministic `correction` when the model's is missing/weak/still wrong, and never
    /// silently accepts a "Excellent" verdict on a sentence with a known error pattern.
    static func mergeKnownErrors(sentence: String, level: String, language: String, feedback: inout [String: Any]) {
        let issues = detectKnownIssues(sentence: sentence, language: language)
        guard !issues.isEmpty else { return }

        let correction = applyKnownRepairs(sentence: sentence, language: language)
        let sentNorm = normalizeForCompare(sentence)
        // Raw (not normalized) comparison — some repairs are punctuation/diacritic-only
        // (French typography spacing, accents), which `normalizeForCompare` would otherwise hide.
        let changed = correction != sentence

        let explanation = feedback["explanation"] as? String ?? ""
        let missed = issues.filter { issue in
            !issue.mentions.contains { explanation.localizedCaseInsensitiveContains($0) }
        }

        feedback["status"] = "Needs Improvement"

        if !missed.isEmpty {
            let bullets = missed.map { "• \($0.issue)" }.joined(separator: "\n")
            let header = missed.count == issues.count ? "Issues in your sentence:" : "Also fix:"
            let prior = explanation.trimmingCharacters(in: .whitespacesAndNewlines)
            feedback["explanation"] = prior.isEmpty
                ? "\(header)\n\(bullets)"
                : "\(prior)\n\n\(header)\n\(bullets)"
        }

        let existingCorrection = (feedback["correction"] as? String ?? "")
            .trimmingCharacters(in: .whitespacesAndNewlines)
        let existingCorrectionStillWrong = !existingCorrection.isEmpty
            && !detectKnownIssues(sentence: existingCorrection, language: language).isEmpty
        let correctionWeak = existingCorrection.isEmpty
            || normalizeForCompare(existingCorrection) == sentNorm
            || existingCorrectionStillWrong
        if changed, correctionWeak {
            feedback["correction"] = correction
        }

        let grammarRule = (feedback["grammar_rule"] as? String ?? "").trimmingCharacters(in: .whitespacesAndNewlines)
        if grammarRule.count < 20 {
            feedback["grammar_rule"] = issues.map(\.grammarRule).joined(separator: "; ")
        }

        if changed, !["C1", "C2"].contains(level.uppercased()) {
            for key in ["next_level_alt", "target_level_alt"] {
                let alt = feedback[key] as? String
                let weak = alt == nil
                    || normalizeForCompare(alt ?? "") == sentNorm
                    || isUnrelatedRewrite(sentence: sentence, alt: alt)
                if weak {
                    feedback[key] = correction
                }
            }
        }

        var ruleIds = (feedback["_coach_rules"] as? [String]) ?? []
        ruleIds.append(contentsOf: issues.map(\.id))
        feedback["_coach_rules"] = ruleIds
    }

    // MARK: - Orchestration

    /// Full cloud-path sanitizer: CEFR plausibility, verbatim-alt stripping, known-error merge,
    /// hallucination stripping, and register-conflict repair. Additive — never throws away a
    /// correct cloud answer, only strengthens/corrects unreliable pieces.
    static func sanitize(sentence: String, level: String, language: String, feedback: inout [String: Any]) {
        if feedback["_coach_repaired"] as? Bool == true {
            feedback.removeValue(forKey: "assessed_level")
        } else if let lvl = normalizeAssessedLevel(
            feedback["assessed_level"] as? String
                ?? feedback["assessedLevel"] as? String
                ?? feedback["sentence_level"] as? String
        ) {
            if assessedLevelPlausible(sentence: sentence, level: lvl, language: language) {
                feedback["assessed_level"] = lvl
            } else {
                feedback.removeValue(forKey: "assessed_level")
            }
        } else {
            feedback.removeValue(forKey: "assessed_level")
        }
        feedback.removeValue(forKey: "assessedLevel")
        feedback.removeValue(forKey: "sentence_level")

        let sentNorm = normalizeForCompare(sentence)
        if let next = feedback["next_level_alt"] as? String, normalizeForCompare(next) == sentNorm {
            feedback.removeValue(forKey: "next_level_alt")
        }
        if let target = feedback["target_level_alt"] as? String, normalizeForCompare(target) == sentNorm {
            feedback.removeValue(forKey: "target_level_alt")
        }

        guard language == "es" || language == "fr" || language == "en" else { return }

        mergeKnownErrors(sentence: sentence, level: level, language: language, feedback: &feedback)

        let halluc = findHallucinatedTerms(sentence: sentence, texts: [
            feedback["grammar_rule"] as? String ?? "",
            feedback["explanation"] as? String ?? "",
            feedback["tip"] as? String ?? "",
        ])
        if !halluc.isEmpty {
            feedback["_coach_warning"] =
                "Removed unreliable references not in your sentence: \(halluc.prefix(3).joined(separator: ", "))"
            for key in ["grammar_rule", "explanation", "tip"] {
                guard var val = feedback[key] as? String else { continue }
                for term in halluc {
                    val = val.replacingOccurrences(of: term, with: "…")
                }
                feedback[key] = val
            }
        }

        if detectRegisterConflict(sentence: sentence, feedback: feedback, language: language) {
            feedback["status"] = "Needs Improvement"
            let prior = feedback["explanation"] as? String ?? ""
            let note = language == "fr"
                ? "Register mismatch: formal «vous» should not become informal «tu»."
                : "Register mismatch: formal «está» should not become informal «estás»."
            feedback["explanation"] = (prior + " " + note).trimmingCharacters(in: .whitespaces)
            feedback.removeValue(forKey: "correction")
        }
    }
}
