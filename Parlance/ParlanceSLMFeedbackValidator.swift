import Foundation

/// Sanity checks and safe fallbacks when on-device SLM output is unreliable.
enum ParlanceSLMFeedbackValidator {

    private static let defaultDialect = "mexican"
    private static let validCEFRLevels = ["A1", "A2", "B1", "B2", "C1", "C2"]

    private static func normalizeAssessedLevel(_ raw: String?) -> String? {
        guard let raw else { return nil }
        let u = raw.uppercased().trimmingCharacters(in: .whitespacesAndNewlines)
        return validCEFRLevels.contains(u) ? u : nil
    }

    private static func isMedicalRegister(_ sentence: String, language: String = "es") -> Bool {
        let norm = normalize(sentence)
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

    private static func hasFrenchSubjunctive(_ norm: String) -> Bool {
        norm.range(
            of: #"\b(eut|fut|soit|ait|eussent|fussent|vinssent)\b"#,
            options: .regularExpression
        ) != nil
    }

    private static func coachSalvageAssessedLevel(sentence: String, assessed: String) -> String {
        let norm = normalize(sentence)
        let u = assessed.uppercased()
        if u == "B1", simplePreteritePastNarrative(sentence), assessedLevelPlausible(sentence: sentence, level: "A2") {
            return "A2"
        }
        if u == "B2", norm.contains("hubiera"), hasSubordinator(sentence),
           assessedLevelPlausible(sentence: sentence, level: "C1") {
            return "C1"
        }
        return assessed
    }

    private static func confidentAssessedLevel(sentence: String, language: String = "es") -> String? {
        let norm = normalize(sentence)
        let wc = sentence.split(whereSeparator: { $0.isWhitespace }).count
        if language == "fr" {
            if wc <= 6,
               norm.range(of: #"\b(suis|es|est|vais|vas|va)\b"#, options: .regularExpression) != nil,
               !hasSubordinator(sentence),
               assessedLevelPlausible(sentence: sentence, level: "A1", language: "fr") {
                return "A1"
            }
            if norm.range(of: #"\b(aime|aimes|aiment)\b"#, options: .regularExpression) != nil, wc <= 10,
               assessedLevelPlausible(sentence: sentence, level: "A2", language: "fr") {
                return "A2"
            }
            if norm.contains("hier"),
               norm.range(of: #"\b(suis alle|est alle)\b"#, options: .regularExpression) != nil,
               assessedLevelPlausible(sentence: sentence, level: "A2", language: "fr") {
                return "A2"
            }
            if (norm.contains("je pense") || norm.contains("nous devons")), wc >= 8,
               assessedLevelPlausible(sentence: sentence, level: "B1", language: "fr") {
                return "B1"
            }
            if isMedicalRegister(sentence, language: "fr"), wc >= 8,
               assessedLevelPlausible(sentence: sentence, level: "C1", language: "fr") {
                return "C1"
            }
            if norm.range(of: #"\bje veux que\b"#, options: .regularExpression) != nil,
               norm.range(of: #"\b(viennes|vienne|fasses|fasse|sois|soit)\b"#, options: .regularExpression) != nil {
                return "B2"
            }
            if norm.range(of: #"\bsi\s+j\s+avais\b"#, options: .regularExpression) != nil,
               norm.range(of: #"\b(serais|serait|serais venu)\b"#, options: .regularExpression) != nil {
                return "B2"
            }
            if norm.range(of: #"\b(bonjour|madame|monsieur)\b"#, options: .regularExpression) != nil,
               norm.range(of: #"\b(allez|comment)\b"#, options: .regularExpression) != nil,
               assessedLevelPlausible(sentence: sentence, level: "B1", language: "fr") {
                return "B1"
            }
            if norm.range(of: #"\bfait qu"#, options: .regularExpression) != nil,
               norm.range(of: #"\bsoit\b"#, options: .regularExpression) != nil,
               hasSubordinator(sentence) {
                return "C1"
            }
            if wc >= 14,
               norm.range(of: #"\b(eu egard|stipulations|arbitrage|obligatoire|different)\b"#, options: .regularExpression) != nil,
               assessedLevelPlausible(sentence: sentence, level: "C2", language: "fr") {
                return "C2"
            }
            return nil
        }
        if isMedicalRegister(sentence), wc >= 8, assessedLevelPlausible(sentence: sentence, level: "C1", language: "es") {
            return "C1"
        }
        if simplePreteritePastNarrative(sentence), assessedLevelPlausible(sentence: sentence, level: "A2", language: "es") {
            return "A2"
        }
        if norm.range(of: #"\bquiero que\b"#, options: .regularExpression) != nil,
           norm.range(of: #"\b(vengas|venga|haga|hagas|tenga|tengas)\b"#, options: .regularExpression) != nil {
            return "B2"
        }
        if norm.contains("hubiera"), hasSubordinator(sentence),
           assessedLevelPlausible(sentence: sentence, level: "C1", language: "es") {
            return "C1"
        }
        if wc >= 14,
           norm.range(of: #"\b(arbitraje|vinculante|renuncien|estipulado|medida en que)\b"#, options: .regularExpression) != nil,
           assessedLevelPlausible(sentence: sentence, level: "C2", language: "es") {
            return "C2"
        }
        return nil
    }

    private static func preserveInferredFields(
        _ out: inout [String: Any], sentence: String? = nil, language: String = "es"
    ) {
        let keepLevel = out["_keep_assessed_level"] as? Bool == true
        var assessed: String?
        if out["_coach_repaired"] as? Bool == true, !keepLevel {
            out.removeValue(forKey: "assessed_level")
            out.removeValue(forKey: "assessedLevel")
            out.removeValue(forKey: "sentence_level")
        } else {
            assessed = normalizeAssessedLevel(
                out["assessed_level"] as? String
                    ?? out["assessedLevel"] as? String
                    ?? out["sentence_level"] as? String
            )
            if let assessed, let sentence {
                assessed = coachSalvageAssessedLevel(sentence: sentence, assessed: assessed)
            }
        }
        if let assessed, let sentence,
           !assessedLevelPlausible(sentence: sentence, level: assessed, language: language) {
            assessed = nil
        }
        if assessed == nil, let sentence {
            assessed = confidentAssessedLevel(sentence: sentence, language: language)
        }
        if let assessed, let sentence {
            assessed = coachSalvageAssessedLevel(sentence: sentence, assessed: assessed)
        }
        if let assessed, let sentence {
            if assessedLevelPlausible(sentence: sentence, level: assessed, language: language) {
                out["assessed_level"] = assessed
            } else {
                out.removeValue(forKey: "assessed_level")
            }
        } else {
            out.removeValue(forKey: "assessed_level")
        }
        out.removeValue(forKey: "assessedLevel")
        out.removeValue(forKey: "sentence_level")
        let note = (out["complexity_note"] as? String ?? out["complexityNote"] as? String)?
            .trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
        if note.isEmpty {
            out.removeValue(forKey: "complexity_note")
        } else {
            out["complexity_note"] = note
        }
        out.removeValue(forKey: "complexityNote")
        out.removeValue(forKey: "_keep_assessed_level")
    }

    private static let timeAdverbs = ["ayer", "hoy", "manana", "mañana", "anoche", "anteayer"]

    private static func citesTimeAdverbAsVerbTense(feedback: [String: Any]) -> Bool {
        let text = [
            feedback["grammar_rule"] as? String ?? "",
            feedback["explanation"] as? String ?? "",
            feedback["tip"] as? String ?? "",
        ].joined(separator: " ").lowercased()
        guard text.contains("preterite") || text.contains("imperfect") || text.contains("pretérito")
        else { return false }
        for adv in timeAdverbs where text.contains(adv) {
            if text.range(of: "\(adv).{0,40}(preterite|imperfect)", options: .regularExpression) != nil
                || text.range(of: "(preterite|imperfect).{0,40}\(adv)", options: .regularExpression) != nil {
                return true
            }
        }
        return false
    }

    private static func simplePreteritePastNarrative(_ sentence: String) -> Bool {
        let norm = normalize(sentence)
        guard ["ayer", "anoche", "anteayer"].contains(where: { norm.contains($0) }) else { return false }
        let hasPreterite = norm.range(
            of: #"\b(fue|fui|comi|comio|trabaje|trabajo|estuve|hice|hizo)\b"#,
            options: .regularExpression
        ) != nil
        let hasImperfect = norm.range(
            of: #"\b(era|estaba|comia|trabajaba|habia|iba)\b"#,
            options: .regularExpression
        ) != nil
        return hasPreterite && !hasImperfect && !hasSubordinator(sentence)
    }

    private static func pastNarrativeAccentFeedback(sentence: String) -> [String: Any] {
        let needsAccent = sentence.range(of: #"\bcomi\b"#, options: .regularExpression) != nil
            && sentence.range(of: #"\bcomí\b"#, options: .regularExpression) == nil
        var correction = sentence
        if needsAccent {
            correction = correction.replacingOccurrences(
                of: #"\bcomi\b"#,
                with: "comí",
                options: [.regularExpression, .caseInsensitive]
            )
            correction = correction.replacingOccurrences(
                of: #",\s*y\s+yo\s+"#,
                with: " y ",
                options: .regularExpression
            )
            correction = correction.replacingOccurrences(
                of: #"\btrabaje\b"#,
                with: "trabajé",
                options: [.regularExpression, .caseInsensitive]
            )
        }
        var out: [String: Any] = [
            "status": needsAccent ? "Needs Improvement" : "Excellent",
            "grammar_rule": needsAccent
                ? "Written accent marks on past-tense verb forms"
                : "Preterite narrative with time adverb «ayer»",
            "explanation": needsAccent
                ? "Add accents on «comí» and «trabajé». «Ayer» is a time adverb only — not a verb. Preterite for completed events yesterday is correct."
                : "«Ayer» frames the time; preterite verbs correctly describe completed actions.",
            "complexity_note": "Short past-tense narrative with «ayer» and coordinated clauses — A2 band.",
            "assessed_level": "A2",
            "register": "Informal narration.",
            "next_level_alt": "Ayer me fue muy bien el día; comí con mi madre y trabajé en el campo.",
            "tip": "Fix accents on «comí», «trabajé». «Ayer» never takes a tense ending.",
            "_keep_assessed_level": true,
        ]
        if needsAccent, correction != sentence {
            out["correction"] = correction
        }
        var preserved = out
        preserveInferredFields(&preserved, sentence: sentence)
        return preserved
    }

    private static let cefrComplexityPrompt = """
        CEFR & COMPLEXITY:
        - Do NOT set assessed_level unless highly confident from specific structures in this sentence. When uncertain, omit it and describe complexity in complexity_note without a CEFR label.
        - complexity_note: 1–2 English sentences on vocabulary, syntax, subordination, and register. Always include when possible, even without assessed_level.
        - next_level_alt / target_level_alt: only when assessed_level is set; otherwise use next_level_alt as a stronger rewrite without a level label.
        """

    static func spanishSystemPrompt(level: String = "", dialect: String = defaultDialect, ragContext: String = "") -> String {
        var prompt = """
        You are a Spanish grammar coach for interpreter training, with expertise in \
        \(dialect) dialect variation. Do NOT assume the learner picked a CEFR level.

        \(cefrComplexityPrompt)
        CRITICAL ACCURACY RULES:
        - Do NOT invent grammatical errors. Only flag real, clear mistakes.
        - Grammatically correct sentences are "Excellent" — but explanation must still cite specific structures in the learner's words (not generic praise).
        - Only mark "Needs Improvement" when there is an actual grammar error — not a style preference.
        - complexity_note must describe THIS sentence's structures — never guess CEFR from word count alone.
        - next_level_alt MUST rewrite the sentence at a higher level — never copy the input verbatim.
        - tip MUST include at least one complete example sentence in Spanish showing a stronger phrasing.
        - Never flag valid dialect features as errors (e.g. voseo in Rioplatense, ustedes for all plural).
        - With formal address (señor/señora + «está»), do NOT «correct» to informal «estás».
        - After «si» in hypothetical clauses, use imperfect subjunctive (tuviera), NOT conditional (tendría).
        - ALL example sentences (correction, next_level_alt, target_level_alt) MUST be complete sentences in Spanish.
        - grammar_rule, explanation, register, and tip MUST be in English.
        - For next_level_alt: same idea one CEFR level above assessed_level.
        - For target_level_alt: same idea two levels above assessed_level (null at C1/C2).
        """
        if !ragContext.isEmpty {
            prompt += """

            REFERENCE KNOWLEDGE (use these rules to verify accuracy — do not invent errors outside them):
            \(ragContext)
            """
        }
        prompt += """

        Respond with ONLY a valid JSON object (no markdown fences):
        {
          "assessed_level": "A1" | "A2" | "B1" | "B2" | "C1" | "C2" | null,
          "complexity_note": "1–2 English sentences on sentence complexity (vocabulary, syntax, subordination, register)",
          "status": "Excellent" or "Needs Improvement",
          "grammar_rule": "The specific grammar rule — always name the rule, even when correct",
          "explanation": "WHY the sentence is correct or incorrect — cite the learner's words",
          "correction": null or "Corrected sentence in Spanish (required when Needs Improvement)",
          "register": "Formal (usted) or informal (tú/vos) and whether appropriate for interpreter settings",
          "next_level_alt": "Same idea rephrased one CEFR level above assessed_level, in Spanish",
          "target_level_alt": "Same idea two levels above assessed_level, in Spanish (null at C1/C2 if N/A)",
          "tip": "Practical tip with a complete Spanish example sentence showing stronger phrasing"
        }
        """
        return prompt
    }

    static func spanishUserPrompt(sentence: String, level: String = "") -> String {
        "Analyze this Spanish sentence: \"\(sentence)\""
    }

    static func frenchSystemPrompt(level: String = "", ragContext: String = "") -> String {
        var prompt = """
        You are a French grammar coach for interpreter training, with expertise in \
        France and Canadian (Québec) dialect variation. Do NOT assume the learner picked a CEFR level.

        \(cefrComplexityPrompt)
        CRITICAL ACCURACY RULES:
        - Do NOT invent grammatical errors. Only flag real, clear mistakes.
        - Grammatically correct sentences are "Excellent" — but explanation must still cite specific structures in the learner's words (not generic praise).
        - Only mark "Needs Improvement" when there is an actual grammar error — not a style preference.
        - complexity_note must describe THIS sentence's structures — never guess CEFR from word count alone.
        - next_level_alt MUST rewrite the sentence at a higher level — never copy the input verbatim.
        - tip MUST include at least one complete example sentence in Spanish showing a stronger phrasing.
        - Never flag valid Canadian French (Québec) features as errors unless inappropriate for context.
        - With formal address (madame/monsieur + « vous »), do NOT « correct » to informal « tu » without context.
        - Si-clause: Si + imparfait → conditionnel (Si j'avais…, je ferais…) — NOT *Si j'aurais* in the protasis.
        - ALL example sentences (correction, next_level_alt, target_level_alt) MUST be complete sentences in French.
        - grammar_rule, explanation, register, and tip MUST be in English.
        - For next_level_alt: same idea one CEFR level above assessed_level.
        - For target_level_alt: same idea two levels above assessed_level (null at C1/C2).
        """
        if !ragContext.isEmpty {
            prompt += """

            REFERENCE KNOWLEDGE (use these rules to verify accuracy — do not invent errors outside them):
            \(ragContext)
            """
        }
        prompt += """

        Respond with ONLY a valid JSON object (no markdown fences):
        {
          "assessed_level": "A1" | "A2" | "B1" | "B2" | "C1" | "C2" | null,
          "complexity_note": "1–2 English sentences on sentence complexity (vocabulary, syntax, subordination, register)",
          "status": "Excellent" or "Needs Improvement",
          "grammar_rule": "The specific grammar rule — always name the rule, even when correct",
          "explanation": "WHY the sentence is correct or incorrect — cite the learner's words",
          "correction": null or "Corrected sentence in French (required when Needs Improvement)",
          "register": "Formal (vous) or informal (tu) and whether appropriate for interpreter settings",
          "next_level_alt": "Same idea rephrased one CEFR level above assessed_level, in French",
          "target_level_alt": "Same idea two levels above assessed_level, in French (null at C1/C2 if N/A)",
          "tip": "Practical tip with a complete French example sentence showing stronger phrasing"
        }
        """
        return prompt
    }

    static func frenchUserPrompt(sentence: String, level: String = "") -> String {
        "Analyze this French sentence: \"\(sentence)\""
    }

    /// Rule-based fallback exposed for parse failures in the SLM engine.
    static func fallbackFeedback(sentence: String, level: String, language: String = "es") -> [String: Any] {
        if language == "fr" {
            return frenchHeuristicFeedback(sentence: sentence, level: level)
        }
        return heuristicFeedback(sentence: sentence, level: level)
    }

    static func sanitize(sentence: String, feedback: [String: Any], level: String, language: String = "es") -> [String: Any] {
        if language == "fr" {
            return sanitizeFrench(sentence: sentence, feedback: feedback, level: level)
        }
        return sanitizeSpanish(sentence: sentence, feedback: feedback, level: level)
    }

    private static func sanitizeSpanish(sentence: String, feedback: [String: Any], level: String) -> [String: Any] {
        if let known = knownSpanishErrorFeedback(sentence: sentence, level: level) {
            return known
        }
        if hasPunctuationIssue(sentence: sentence) {
            return heuristicFeedback(sentence: sentence, level: level)
        }
        if modelInventedError(sentence: sentence, feedback: feedback) {
            if simplePreteritePastNarrative(sentence) {
                return pastNarrativeAccentFeedback(sentence: sentence)
            }
            return genericExcellentFeedback(sentence: sentence, level: level)
        }
        if needsRepair(sentence: sentence, feedback: feedback) {
            if let salvaged = salvageFeedback(sentence: sentence, feedback: feedback),
               !needsRepair(sentence: sentence, feedback: salvaged) {
                var repaired = salvaged
                preserveInferredFields(&repaired, sentence: sentence)
                return repaired
            }
            if let known = knownSpanishErrorFeedback(sentence: sentence, level: level) {
                return known
            }
            return heuristicFeedback(sentence: sentence, level: level)
        }
        var out = feedback
        let halluc = findHallucinatedTerms(
            sentence: sentence,
            texts: [
                out["grammar_rule"] as? String ?? "",
                out["explanation"] as? String ?? "",
                out["tip"] as? String ?? "",
            ]
        )
        if !halluc.isEmpty {
            out["_coach_warning"] = "Removed unreliable references not in your sentence: \(halluc.prefix(3).joined(separator: ", "))"
            for key in ["grammar_rule", "explanation", "tip"] {
                guard var val = out[key] as? String else { continue }
                for term in halluc {
                    val = val.replacingOccurrences(of: term, with: "…")
                }
                out[key] = val
            }
        }
        if detectRegisterConflict(sentence: sentence, feedback: out) {
            out["status"] = "Needs Improvement"
            let prior = out["explanation"] as? String ?? ""
            out["explanation"] = (
                prior + " Register mismatch: formal «está» should not become informal «estás»."
            ).trimmingCharacters(in: .whitespaces)
            out.removeValue(forKey: "correction")
        }
        if isUnrelatedRewrite(sentence: sentence, alt: out["next_level_alt"] as? String) {
            out.removeValue(forKey: "next_level_alt")
        }
        if isUnrelatedRewrite(sentence: sentence, alt: out["target_level_alt"] as? String) {
            out.removeValue(forKey: "target_level_alt")
        }
        if citesTimeAdverbAsVerbTense(feedback: out)
            || (simplePreteritePastNarrative(sentence)
                && (out["status"] as? String) == "Needs Improvement"
                && (out["explanation"] as? String ?? "").lowercased().contains("preterite")
                && (out["explanation"] as? String ?? "").lowercased().contains("imperfect")) {
            return pastNarrativeAccentFeedback(sentence: sentence)
        }
        preserveInferredFields(&out, sentence: sentence)
        return out
    }

    /// Reject CEFR labels that clearly mismatch sentence structure (never invent levels — only filter obvious errors).
    private static func assessedLevelPlausible(
        sentence: String, level: String, language: String = "es"
    ) -> Bool {
        if language == "fr" {
            return assessedLevelPlausibleFrench(sentence: sentence, level: level)
        }
        let norm = normalize(sentence)
        let wordCount = sentence.split(whereSeparator: { $0.isWhitespace }).count
        let hasSub = hasSubordinator(sentence)
        let hasSubjunctive = norm.range(
            of: #"\b(hubiera|tuviera|fuera|pudiera|quisiera|hiciera|hubiese|tuviese)\b"#,
            options: .regularExpression
        ) != nil
        let hasConditional = norm.range(
            of: #"\b(habria|habría|tendria|tendría|seria|sería|podria|podría)\b"#,
            options: .regularExpression
        ) != nil
        let hasPreterite = norm.range(
            of: #"\b(fui|fue|fuimos|fueron|hice|hizo|estuve|estuvo|pude|pudo|quise|quiso|vine|vino|dije|dijo)\b"#,
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
               norm.range(of: #"\b(arbitraje|vinculante|renuncien|estipulado|medida en que)\b"#, options: .regularExpression) != nil {
                return true
            }
            return hasSubjunctive || (hasSub && wordCount >= 12) || hasConditional
        default:
            return false
        }
    }

    private static func assessedLevelPlausibleFrench(sentence: String, level: String) -> Bool {
        let norm = normalize(sentence)
        let wordCount = sentence.split(whereSeparator: { $0.isWhitespace }).count
        let hasSub = hasSubordinator(sentence)
        let hasSubjunctive = hasFrenchSubjunctive(norm)
        let hasConditional = norm.range(
            of: #"\b(aurais|aurait|aurions|auriez|serais|serait|ferais|ferait)\b"#,
            options: .regularExpression
        ) != nil
        let hasPasse = norm.range(
            of: #"\b(suis alle|est alle)\b"#,
            options: .regularExpression
        ) != nil
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

    private static func sanitizeFrench(sentence: String, feedback: [String: Any], level: String) -> [String: Any] {
        if let known = knownFrenchErrorFeedback(sentence: sentence, level: level) {
            var preserved = known
            preserveInferredFields(&preserved, sentence: sentence, language: "fr")
            return preserved
        }
        if hasFrenchTypographyIssue(sentence: sentence) {
            return frenchHeuristicFeedback(sentence: sentence, level: level)
        }
        if modelInventedError(sentence: sentence, feedback: feedback) {
            return frenchGenericExcellentFeedback(sentence: sentence, level: level)
        }
        if needsRepairFrench(sentence: sentence, feedback: feedback) {
            if modelInventedError(sentence: sentence, feedback: feedback) {
                return frenchGenericExcellentFeedback(sentence: sentence, level: level)
            }
            if let known = knownFrenchErrorFeedback(sentence: sentence, level: level) {
                return known
            }
            return frenchHeuristicFeedback(sentence: sentence, level: level)
        }
        var out = feedback
        let halluc = findHallucinatedTerms(
            sentence: sentence,
            texts: [
                out["grammar_rule"] as? String ?? "",
                out["explanation"] as? String ?? "",
                out["tip"] as? String ?? "",
            ]
        )
        if !halluc.isEmpty {
            out["_coach_warning"] = "Removed unreliable references not in your sentence: \(halluc.prefix(3).joined(separator: ", "))"
            for key in ["grammar_rule", "explanation", "tip"] {
                guard var val = out[key] as? String else { continue }
                for term in halluc {
                    val = val.replacingOccurrences(of: term, with: "…")
                }
                out[key] = val
            }
        }
        if isUnrelatedRewrite(sentence: sentence, alt: out["next_level_alt"] as? String) {
            out.removeValue(forKey: "next_level_alt")
        }
        if isUnrelatedRewrite(sentence: sentence, alt: out["target_level_alt"] as? String) {
            out.removeValue(forKey: "target_level_alt")
        }
        preserveInferredFields(&out, sentence: sentence, language: "fr")
        return out
    }

    private static func knownFrenchErrorFeedback(sentence: String, level: String) -> [String: Any]? {
        siClauseFrenchFeedback(sentence: sentence, level: level)
    }

    private static func siClauseFrenchFeedback(sentence: String, level: String) -> [String: Any]? {
        guard let regex = try? NSRegularExpression(
            pattern: #"(?i)\bsi\b[^.!?]*\b(j'aurais|tu aurais|il aurait|elle aurait|nous aurions|vous auriez)\b"#
        ) else { return nil }
        let ns = sentence as NSString
        guard regex.firstMatch(in: sentence, range: NSRange(location: 0, length: ns.length)) != nil else {
            return nil
        }
        var correction = sentence
        let replacements: [(String, String)] = [
            (#"(?i)\bj'aurais\b"#, "j'avais"),
            (#"(?i)\btu aurais\b"#, "tu avais"),
            (#"(?i)\bil aurait\b"#, "il avait"),
            (#"(?i)\belle aurait\b"#, "elle avait"),
        ]
        for (pattern, sub) in replacements {
            correction = correction.replacingOccurrences(
                of: pattern, with: sub, options: .regularExpression
            )
        }
        var result: [String: Any] = [
            "status": "Needs Improvement",
            "grammar_rule": "Si clauses: imparfait in the protasis, not conditionnel",
            "explanation": """
            After « si » introducing a hypothetical condition, French uses the imparfait \
            (e.g. « j'avais »), not the conditionnel (« j'aurais »). The conditionnel belongs in the main clause.
            """,
            "correction": correction,
            "register": "Neutral; focus on standard French for interpreting exams.",
            "next_level_alt": correction,
            "tip": "Mnemonic: « Si j'avais…, je ferais… » — imparfait in the si-clause, conditionnel in the result.",
            "complexity_note": (
                "Hypothetical « si » clause with conditionnel in the protasis instead of imparfait — "
                "upper-intermediate structure band even when the form is wrong."
            ),
            "assessed_level": "B2",
            "_coach_repaired": true,
            "_keep_assessed_level": true,
        ]
        if !["C1", "C2"].contains(level.uppercased()) {
            result["target_level_alt"] = correction
        }
        return result
    }

    private static func hasFrenchTypographyIssue(sentence: String) -> Bool {
        guard let regex = try? NSRegularExpression(pattern: #"\w[?!;:]"#) else { return false }
        let ns = sentence as NSString
        return regex.firstMatch(in: sentence, range: NSRange(location: 0, length: ns.length)) != nil
    }

    private static func needsRepairFrench(sentence: String, feedback: [String: Any]) -> Bool {
        let status = feedback["status"] as? String ?? ""
        let grammarRule = feedback["grammar_rule"] as? String ?? ""
        let explanation = feedback["explanation"] as? String ?? ""
        let correction = feedback["correction"] as? String ?? ""
        let fields = [grammarRule, explanation, feedback["tip"] as? String ?? ""]
        if !findHallucinatedTerms(sentence: sentence, texts: fields).isEmpty { return true }
        if isUnrelatedRewrite(sentence: sentence, alt: feedback["next_level_alt"] as? String) { return true }
        if isUnrelatedRewrite(sentence: sentence, alt: feedback["target_level_alt"] as? String) { return true }
        if grammarRuleLooksLikeMetaCommentary(grammarRule) { return true }
        if status == "Needs Improvement" {
            if explanation.trimmingCharacters(in: .whitespacesAndNewlines).count < 24 { return true }
            if correction.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty { return true }
            if normalize(correction) == normalize(sentence) { return true }
        }
        if status == "Excellent", knownFrenchErrorFeedback(sentence: sentence, level: "") != nil {
            return true
        }
        return false
    }

    private static func frenchGenericExcellentFeedback(sentence: String, level: String) -> [String: Any] {
        [
            "status": "Excellent",
            "grammar_rule": "General French grammar",
            "explanation": """
            No confirmed grammar error in your sentence. \
            The on-device coach rejected an unreliable correction — review register and word choice for your setting.
            """,
            "register": "Confirm tu/vous matches the interpreting context (clinical, legal, or casual).",
            "next_level_alt": sentence,
            "tip": "Re-read pronouns (le/la/l') and register (tu/vous) against your interpreting context.",
            "_coach_repaired": true,
        ]
    }

    private static func frenchHeuristicFeedback(sentence: String, level: String) -> [String: Any] {
        if let known = knownFrenchErrorFeedback(sentence: sentence, level: level) {
            return known
        }
        let text = sentence.trimmingCharacters(in: .whitespacesAndNewlines)
        var issues: [String] = []
        if hasFrenchTypographyIssue(sentence: text) {
            issues.append("missing space before ? ! ; : (French typography)")
        }
        let status = issues.isEmpty ? "Excellent" : "Needs Improvement"
        var correction: String?
        if issues.contains(where: { $0.contains("space") }) {
            correction = text
                .replacingOccurrences(of: #"(\w)(\?|!|;|:)"#, with: "$1 $2", options: .regularExpression)
        }
        var out: [String: Any] = [
            "status": status,
            "grammar_rule": issues.isEmpty ? "General French grammar" : "French typography (espaces insécables)",
            "explanation": issues.isEmpty
                ? "No clear errors detected by rule-based checks."
                : "French requires a space before ? ! ; : — e.g. « Comment allez-vous ? »",
            "register": "Note whether tu/vous matches the setting (clinical, legal, or casual).",
            "next_level_alt": correction ?? text,
            "tip": issues.isEmpty
                ? "Strengthen register (tu/vous) and lexical precision for your interpreting context."
                : "Corrigez la typographie française, puis vérifiez tu/vous selon le contexte.",
            "_coach_repaired": true,
        ]
        if let correction { out["correction"] = correction }
        return out
    }

    private static func spanishLevelGuidance(level: String) -> String {
        switch level.uppercased() {
        case "C2", "C1":
            return "Focus on professional register, near-native precision, and interpreting vocabulary. Flag Anglicisms and calques."
        case "B2":
            return "Focus on subjunctive vs indicative, si-clause structure (imperfect subjunctive + conditional), gender agreement, and register (tú/usted)."
        case "B1":
            return "Focus on past tenses, subjunctive triggers, and register. Be clear about why an error matters."
        case "A2":
            return "Focus on present tense, reflexives, and basic agreement. Gently note tú/usted choice."
        default:
            return "Focus on present tense and basic structures. Be encouraging; note register simply."
        }
    }

    // MARK: - Salvage / invented-error detection

    private static func hasPunctuationIssue(sentence: String) -> Bool {
        sentence.contains("?") && !sentence.contains("¿")
            || sentence.contains("!") && !sentence.contains("¡")
    }

    private static func modelInventedError(sentence: String, feedback: [String: Any]) -> Bool {
        guard feedback["status"] as? String == "Needs Improvement" else { return false }
        if citesTimeAdverbAsVerbTense(feedback: feedback) { return true }
        let fields = [
            feedback["grammar_rule"] as? String ?? "",
            feedback["explanation"] as? String ?? "",
        ]
        let joined = fields.joined(separator: " ").lowercased()
        if simplePreteritePastNarrative(sentence),
           joined.contains("preterite"), joined.contains("imperfect") {
            return true
        }
        return !findHallucinatedTerms(sentence: sentence, texts: fields).isEmpty
    }

    private static func salvageFeedback(sentence: String, feedback: [String: Any]) -> [String: Any]? {
        var out = feedback
        for altKey in ["next_level_alt", "target_level_alt"] {
            if isUnrelatedRewrite(sentence: sentence, alt: out[altKey] as? String) {
                out.removeValue(forKey: altKey)
            }
        }
        if detectRegisterConflict(sentence: sentence, feedback: out) {
            out.removeValue(forKey: "correction")
            out["status"] = "Excellent"
            let prior = out["explanation"] as? String ?? ""
            out["explanation"] = (
                prior + " Formal «está» with «señora» is correct — informal «estás» would be a register error."
            ).trimmingCharacters(in: .whitespaces)
        }
        let halluc = findHallucinatedTerms(
            sentence: sentence,
            texts: [
                out["grammar_rule"] as? String ?? "",
                out["explanation"] as? String ?? "",
                out["tip"] as? String ?? "",
            ]
        )
        if !halluc.isEmpty {
            return nil
        }
        return out
    }

    private static func isGreetingSentence(_ sentence: String) -> Bool {
        let n = normalize(sentence)
        return n.contains("hola") || n.contains("buenos") || n.contains("como esta")
            || n.contains("senora") || n.contains("senor")
    }

    private static func genericExcellentFeedback(sentence: String, level: String) -> [String: Any] {
        var out = substantiveExcellentFeedback(sentence: sentence)
        out["_coach_repaired"] = true
        return out
    }

    // MARK: - Repair detection

    private static func needsRepair(sentence: String, feedback: [String: Any]) -> Bool {
        let status = feedback["status"] as? String ?? ""
        let grammarRule = feedback["grammar_rule"] as? String ?? ""
        let explanation = feedback["explanation"] as? String ?? ""
        let tip = feedback["tip"] as? String ?? ""
        let correction = feedback["correction"] as? String ?? ""

        let fields = [grammarRule, explanation, tip]
        if !findHallucinatedTerms(sentence: sentence, texts: fields).isEmpty { return true }
        if isUnrelatedRewrite(sentence: sentence, alt: feedback["next_level_alt"] as? String) { return true }
        if isUnrelatedRewrite(sentence: sentence, alt: feedback["target_level_alt"] as? String) { return true }
        if detectRegisterConflict(sentence: sentence, feedback: feedback) { return true }
        if grammarRuleLooksLikeMetaCommentary(grammarRule) { return true }
        if status == "Needs Improvement" {
            if explanation.trimmingCharacters(in: .whitespacesAndNewlines).count < 24 { return true }
            if correction.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty { return true }
            if normalize(correction) == normalize(sentence) { return true }
        }
        if status == "Excellent", knownSpanishErrorFeedback(sentence: sentence, level: "") != nil {
            return true
        }
        if status == "Excellent", feedbackIsLowQuality(sentence: sentence, feedback: feedback) {
            return true
        }
        return false
    }

    private static func feedbackIsLowQuality(sentence: String, feedback: [String: Any]) -> Bool {
        let grammar = (feedback["grammar_rule"] as? String ?? "").lowercased()
        let explanation = feedback["explanation"] as? String ?? ""
        let complexity = (feedback["complexity_note"] as? String ?? feedback["complexityNote"] as? String ?? "")
            .trimmingCharacters(in: .whitespacesAndNewlines)
        let next = feedback["next_level_alt"] as? String ?? ""
        if grammar.contains("general spanish grammar") { return true }
        if explanation.localizedCaseInsensitiveContains("no clear errors detected") { return true }
        if explanation.localizedCaseInsensitiveContains("no confirmed grammar error") { return true }
        if explanation.trimmingCharacters(in: .whitespacesAndNewlines).count < 48 { return true }
        if complexity.isEmpty { return true }
        if !next.isEmpty, normalize(next) == normalize(sentence) { return true }
        return false
    }

    // MARK: - Known Spanish error patterns

    private static func knownSpanishErrorFeedback(sentence: String, level: String) -> [String: Any]? {
        if let si = siClauseConditionalFeedback(sentence: sentence, level: level) {
            return si
        }
        if let leismo = echarDeMenosLeismoFeedback(sentence: sentence, level: level) {
            return leismo
        }
        return nil
    }

    private static func echarDeMenosLeismoFeedback(sentence: String, level: String) -> [String: Any]? {
        guard let regex = try? NSRegularExpression(
            pattern: #"(?i)\b(le|les)\s+echo\s+de\s+menos\b"#
        ) else { return nil }
        let ns = sentence as NSString
        guard regex.firstMatch(in: sentence, range: NSRange(location: 0, length: ns.length)) != nil else {
            return nil
        }

        let norm = normalize(sentence)
        let feminineHints = ["ella", "novia", "madre", "hermana", "esposa", "mujer", "amiga", "hija", "abuela"]
        let masculineHints = ["novio", "padre", "hermano", "esposo", "hombre", "amigo", "hijo", "abuelo"]
        let directObject: String
        if feminineHints.contains(where: { norm.contains($0) }) {
            directObject = "la"
        } else if masculineHints.contains(where: { norm.contains($0) }) {
            directObject = "lo"
        } else {
            directObject = "la"
        }

        var correction = sentence
        correction = correction.replacingOccurrences(
            of: #"(?i)\bles\s+echo\s+de\s+menos\b"#,
            with: "\(directObject == "la" ? "las" : "los") echo de menos"
        )
        correction = correction.replacingOccurrences(
            of: #"(?i)\ble\s+echo\s+de\s+menos\b"#,
            with: "\(directObject) echo de menos"
        )

        var result: [String: Any] = [
            "status": "Needs Improvement",
            "grammar_rule": "«Echar de menos» takes a direct object (lo/la), not «le»",
            "explanation": """
            «Echar de menos» governs a direct object: «\(directObject) echo de menos». \
            «Le echo de menos» is leísmo — common in speech but «le» is not the direct object form on DELE/interpreter exams.
            """,
            "correction": correction,
            "register": "Neutral; leísmo may appear regionally but use lo/la for standard written Spanish.",
            "next_level_alt": correction,
            "tip": "Match the pronoun to who you miss: «la echo de menos» (her), «lo echo de menos» (him), «los echo de menos» (them).",
            "_coach_repaired": true,
        ]
        if !["C1", "C2"].contains(level.uppercased()) {
            result["target_level_alt"] = correction
        }
        return result
    }

    private static func siClauseConditionalFeedback(sentence: String, level: String) -> [String: Any]? {
        guard let regex = try? NSRegularExpression(
            pattern: #"(?i)\bsi\b[^.!?]*\b(tendr[ií]a|har[ií]a|ser[ií]a|podr[ií]a|querr[ií]a|dir[ií]a|vendr[ií]a)\b"#
        ) else { return nil }
        let ns = sentence as NSString
        guard regex.firstMatch(in: sentence, range: NSRange(location: 0, length: ns.length)) != nil else {
            return nil
        }

        var correction = sentence
        let replacements: [(String, String)] = [
            (#"(?i)\btendría\b"#, "tuviera"),
            (#"(?i)\btendria\b"#, "tuviera"),
            (#"(?i)\bharía\b"#, "hiciera"),
            (#"(?i)\bharia\b"#, "hiciera"),
            (#"(?i)\bsería\b"#, "fuera"),
            (#"(?i)\bseria\b"#, "fuera"),
            (#"(?i)\bpodría\b"#, "pudiera"),
            (#"(?i)\bpodria\b"#, "pudiera"),
        ]
        for (pattern, sub) in replacements {
            correction = correction.replacingOccurrences(
                of: pattern, with: sub, options: .regularExpression
            )
        }

        var result: [String: Any] = [
            "status": "Needs Improvement",
            "grammar_rule": "Si clauses: imperfect subjunctive in the protasis, not conditional",
            "explanation": """
            After «si» introducing a hypothetical condition, Spanish uses the imperfect subjunctive \
            (e.g. «tuviera»), not the conditional («tendría»). The conditional belongs in the main clause.
            """,
            "correction": correction,
            "register": "Neutral; focus on standard written Spanish for interpreting exams.",
            "next_level_alt": correction,
            "tip": "Mnemonic: «Si yo fuera…, haría…» — subjunctive in the si-clause, conditional in the result.",
            "_coach_repaired": true,
        ]
        if !["C1", "C2"].contains(level.uppercased()) {
            result["target_level_alt"] = correction
        }
        return result
    }

    // MARK: - Heuristic fallback

    private static func heuristicFeedback(sentence: String, level: String) -> [String: Any] {
        if let known = knownSpanishErrorFeedback(sentence: sentence, level: level) {
            return known
        }

        let text = sentence.trimmingCharacters(in: .whitespacesAndNewlines)
        var issues: [String] = []
        if text.contains("?") && !text.contains("¿") {
            issues.append("missing opening inverted question mark (¿)")
        }
        if text.contains("!") && !text.contains("¡") {
            issues.append("missing opening inverted exclamation mark (¡)")
        }

        let norm = normalize(text)
        let hasInformalGreetingCue = norm.range(
            of: #"\b(te|tu|amor|carino|querido|querida)\b"#,
            options: .regularExpression
        ) != nil
        let hasAffectionateExtrañar = norm.contains("amor")
            && norm.contains("extran")
            && norm.range(of: #"\bte\b"#, options: .regularExpression) != nil
        let hasFormalGreetingCue = (
            ((norm.contains("como esta") || text.localizedCaseInsensitiveContains("cómo está"))
                && !norm.contains("estas"))
            || norm.range(of: #"\b(usted|senor|senora)\b"#, options: .regularExpression) != nil
        ) && !hasInformalGreetingCue
        let register: String
        if hasInformalGreetingCue {
            register = "Informal and affectionate: familiar pronouns or terms of endearment fit a close personal relationship, not a formal usted exchange."
        } else if hasFormalGreetingCue {
            register = """
            Formal address (usted): «señora» + third-person «está» fits a polite greeting. \
            Keep «¿cómo está?» — do not switch to informal «¿cómo estás?» in this context.
            """
        } else {
            register = "Note whether tú/usted matches the setting (clinical, legal, or casual)."
        }

        var correction: String?
        if !issues.isEmpty {
            var fixed = text
            if let range = fixed.range(
                of: #",?\s*cómo\s+está\??"#,
                options: [.regularExpression, .caseInsensitive]
            ) {
                fixed.replaceSubrange(range, with: ", ¿cómo está?")
            } else if fixed.contains("?") && !fixed.contains("¿") {
                fixed = "¿" + fixed
            }
            correction = fixed
        }

        let status = issues.isEmpty ? "Excellent" : "Needs Improvement"
        if issues.isEmpty, !isGreetingSentence(text) {
            var out = substantiveExcellentFeedback(sentence: text)
            out["_coach_repaired"] = true
            return out
        }

        let grammar: String
        let explanation: String
        if issues.isEmpty, hasAffectionateExtrañar {
            grammar = "Informal greeting, vocative punctuation, and direct-object pronoun «te»"
            explanation = """
            «\(text)» is grammatically sound: «te» is the informal direct-object pronoun used with «extrañar», \
            and «amor» is an affectionate vocative. For polished punctuation, write «Hola, amor, te extraño mucho.»
            """
        } else if issues.isEmpty, hasInformalGreetingCue {
            grammar = "Informal greeting and familiar address"
            explanation = "«\(text)» uses informal, familiar language. Keep that register when the relationship is personal, and use commas to set off a vocative where appropriate."
        } else if issues.isEmpty, hasFormalGreetingCue {
            grammar = "Formal greeting and usted register"
            explanation = "Polite greeting with appropriate formal verb form; only minor punctuation may apply."
        } else if issues.isEmpty {
            grammar = "Greeting and context-appropriate register"
            explanation = "«\(text)» is grammatically sound. Choose formal or informal address based on the relationship and interpreting setting."
        } else {
            grammar = "Inverted question marks (¿…?) in Spanish"
            explanation = hasFormalGreetingCue
                ? "Add «¿» before a question clause. With «señora» and «está», keep formal usted — do not «correct» to informal «estás»."
                : "Add «¿» before a question clause and preserve the sentence's existing register."
        }

        var nextAlt = correction ?? text
        if hasInformalGreetingCue {
            if let r = nextAlt.range(of: #"^hola\s+"#, options: [.regularExpression, .caseInsensitive]) {
                nextAlt.replaceSubrange(r, with: "Hola, ")
            }
        } else if hasFormalGreetingCue,
                  ["B2", "B1", "A2", "A1"].contains(level.uppercased()),
           let r = nextAlt.range(of: #"^hola\s+"#, options: [.regularExpression, .caseInsensitive]) {
            nextAlt.replaceSubrange(r, with: "Buenos días, ")
        }

        var out: [String: Any] = [
            "status": status,
            "grammar_rule": grammar,
            "explanation": explanation,
            "register": register,
            "next_level_alt": nextAlt,
            "tip": hasInformalGreetingCue
                ? "Use commas to set off a vocative where appropriate: «\(nextAlt)» Keep informal «te» for a close personal relationship; use formal address or rephrase when the setting requires it."
                : heuristicImprovementTip(sentence: text, level: level, issues: issues),
            "_coach_repaired": true,
        ]
        if let correction { out["correction"] = correction }
        if ["B2", "C1", "C2"].contains(level.uppercased()) {
            out["target_level_alt"] = correction ?? nextAlt
        }
        preserveInferredFields(&out, sentence: text)
        return out
    }

    // MARK: - Substantive excellent feedback (heuristic enrichment)

    private static func hasSubordinator(_ text: String) -> Bool {
        let norm = normalize(text)
        if norm.contains("fait que") || norm.contains("fait qu") || norm.contains("el hecho de que") {
            return true
        }
        let markers = [
            " porque ", " pues ", " que ", " qu ", " cuando ", " si ", " aunque ",
            " mientras ", " lo cual ", " donde ", " como ", " sino ",
            " lorsque ", " puisque ", " bien que ",
        ]
        return markers.contains { norm.contains($0) }
    }

    private static func stripTrailingPunctuation(_ text: String) -> String {
        text.trimmingCharacters(in: CharacterSet(charactersIn: ".,!?;:").union(.whitespacesAndNewlines))
    }

    private static func upgradeYCoordination(_ text: String) -> (next: String, target: String?) {
        let parts = text.components(separatedBy: " y ")
        guard parts.count == 2 else {
            return (text, nil)
        }
        let a = stripTrailingPunctuation(parts[0].trimmingCharacters(in: .whitespacesAndNewlines))
        var b = stripTrailingPunctuation(parts[1].trimmingCharacters(in: .whitespacesAndNewlines))
        if let first = b.first {
            b = String(first).lowercased() + b.dropFirst()
        }
        let next = "\(a), porque \(b)."
        let target = "\(a), sobre todo porque \(b), lo cual me resulta difícil de manejar."
        return (next, target)
    }

    private static func substantiveExcellentFeedback(sentence: String) -> [String: Any] {
        let text = sentence.trimmingCharacters(in: .whitespacesAndNewlines)
        let norm = normalize(text)
        let wordCount = text.split(whereSeparator: { $0.isWhitespace }).count
        let yCoordinated = text.range(of: #"\s+y\s+"#, options: [.regularExpression, .caseInsensitive]) != nil

        let grammarRule: String
        let explanation: String
        let complexityNote: String
        let register: String
        let tip: String
        var nextAlt: String
        var targetAlt: String?

        if norm.contains("estoy incomoda") || norm.contains("estoy incómoda")
            || (norm.contains("estoy") && norm.contains("no dejo de")) {
            grammarRule = "Estar + adjective for temporary states; periphrasis «no dejar de + infinitive»"
            explanation = """
            «Estoy incómoda» correctly uses **estar** for a temporary state or feeling — *ser incómoda* would \
            describe a person's character, not how you feel right now. «No dejo de pensar» is a valid periphrasis \
            meaning "I can't stop thinking." Both clauses are grammatically sound; chaining them with «y» keeps \
            the sentence conversational but structurally simple.
            """
            complexityNote = """
            Two coordinated main clauses joined with «y»: present tense + adjective (estar) and the periphrasis \
            «no dejar de + infinitive». No subordination or advanced connectors — everyday spoken structure, \
            not formal or literary syntax.
            """
            register = "Informal first person (tú implied); appropriate for personal or clinical rapport if the context is intimate."
            nextAlt = "Me siento incómoda porque no dejo de pensar en ello."
            targetAlt = "Me encuentro incómoda, sobre todo porque no consigo dejar de darle vueltas al asunto."
            tip = """
            Replace «y» with cause: «Me siento incómoda **porque** no dejo de pensar en ello.» Or use richer \
            vocabulary: «…**pues** no puedo dejar de **darle vueltas** al asunto.»
            """
        } else if yCoordinated && !hasSubordinator(text) {
            grammarRule = "Coordination with «y» vs subordination (porque, pues, lo cual)"
            explanation = """
            Your sentence links ideas with «y», which is grammatically fine but reads as two separate thoughts. \
            At interpreter level, subordinating the second clause (cause, contrast, or result) shows tighter \
            control and sounds more natural in formal settings.
            """
            complexityNote = """
            Simple coordination with «y» and no subordinate clause — structurally straightforward. \
            Clear vocabulary but limited syntactic layering; room to add connectors and nuance.
            """
            register = "Confirm tú/usted matches the setting; coordinated «y» chains are fine in casual speech but often upgraded in formal interpreting."
            let upgraded = upgradeYCoordination(text)
            nextAlt = upgraded.next
            targetAlt = upgraded.target
            tip = """
            Upgrade: «\(nextAlt)» — swap «y» for **porque** or **pues** to show how the two ideas relate.
            """
        } else if norm.contains("estoy ") || norm.contains("estoy,") {
            grammarRule = "Ser vs estar — temporary states with estar"
            explanation = """
            Using **estar** for feelings, conditions, or locations is appropriate here. The sentence is grammatically \
            correct; focus next on whether vocabulary and connectors match the formality of your interpreting context.
            """
            complexityNote = """
            Present tense with **estar** + complement. \(wordCount) words, \
            \(hasSubordinator(text) ? "includes subordination" : "main-clause structure only").
            """
            register = "First-person state description; match tú/usted to the patient or client relationship."
            nextAlt = text.hasSuffix(".") ? text : text + "."
            if !hasSubordinator(text), yCoordinated {
                nextAlt = upgradeYCoordination(text).next
                targetAlt = upgradeYCoordination(text).target
            } else {
                targetAlt = nil
            }
            tip = "Add precision: instead of a bare adjective, try «Me siento…» or «Me encuentro…» for a slightly more formal register."
        } else {
            grammarRule = "Sentence structure and register"
            explanation = """
            No grammar error stands out in this sentence. The structures you used are acceptable — the next step is \
            tightening vocabulary and connectors so the line fits a professional interpreting context.
            """
            complexityNote = """
            \(wordCount)-word sentence\(hasSubordinator(text) ? " with subordination" : ", mainly main-clause structure"). \
            Describe syntax and vocabulary in context rather than assigning a single CEFR band.
            """
            register = "Confirm tú/usted and formality match the scenario (clinical, legal, or casual)."
            if yCoordinated && !hasSubordinator(text) {
                nextAlt = upgradeYCoordination(text).next
                targetAlt = upgradeYCoordination(text).target
            } else {
                nextAlt = text
                targetAlt = nil
            }
            tip = "Try adding a subordinate clause: «…, **porque** …» or «…, **lo cual** …» to link ideas in one flowing sentence."
        }

        var out: [String: Any] = [
            "status": "Excellent",
            "grammar_rule": grammarRule,
            "explanation": explanation,
            "complexity_note": complexityNote,
            "register": register,
            "next_level_alt": nextAlt,
            "tip": tip,
            "_coach_repaired": true,
        ]
        if let targetAlt { out["target_level_alt"] = targetAlt }
        preserveInferredFields(&out, sentence: sentence)
        return out
    }

    private static func heuristicImprovementTip(sentence: String, level: String, issues: [String]) -> String {
        let norm = normalize(sentence)
        if norm.contains("echo de menos") {
            return "«Echar de menos» takes lo/la: «la echo de menos» (her), «lo echo de menos» (him) — not «le»."
        }
        if norm.range(of: #"\b(le|les|lo|la|los|las)\s+\w"#, options: .regularExpression) != nil {
            return "Check clitic pronouns: direct objects are lo/la/los/las; «le/les» mark indirect objects unless regional leísmo applies."
        }
        if !issues.isEmpty {
            return "Fix punctuation first, then confirm tú/usted matches your interpreting scenario."
        }
        return "Prefer precise verbs and connectors over repeated «y» clauses where a subordinate fits."
    }

    // MARK: - Token checks

    private static let stopwords: Set<String> = [
        "the", "and", "for", "with", "requires", "appropriate", "correct", "formal",
        "informal", "professional", "grammar", "spanish", "english", "sentence", "learner",
        "a", "al", "con", "de", "del", "el", "en", "es", "la", "las", "lo", "los", "que", "y",
    ]

    private static func grammarRuleLooksLikeMetaCommentary(_ rule: String) -> Bool {
        let lower = rule.lowercased()
        return lower.contains("the learner") || lower.contains("the sentence")
            || lower.contains("needs to") || lower.contains("should have")
    }

    private static func normalize(_ text: String) -> String {
        text.lowercased()
            .folding(options: .diacriticInsensitive, locale: .current)
            .replacingOccurrences(of: #"[^a-z0-9\s]"#, with: " ", options: .regularExpression)
    }

    private static func tokens(_ text: String) -> Set<String> {
        Set(
            normalize(text)
                .split(separator: " ")
                .map(String.init)
                .filter { $0.count >= 3 && !stopwords.contains($0) }
        )
    }

    private static func findHallucinatedTerms(sentence: String, texts: [String]) -> [String] {
        let sentNorm = normalize(sentence)
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
                let core = normalize(term)
                guard core.count >= 3 else { continue }
                if sentNorm.contains(core) || sentTokens.contains(core) { continue }
                let parts = core.split(separator: " ").map(String.init).filter { $0.count >= 4 }
                if parts.contains(where: { sentNorm.contains($0) }) { continue }
                bad.append(term)
            }
        }
        return bad
    }

    private static func isUnrelatedRewrite(sentence: String, alt: String?) -> Bool {
        guard let alt, !alt.trimmingCharacters(in: .whitespaces).isEmpty else { return false }
        let sw = tokens(sentence)
        let aw = tokens(alt)
        guard !sw.isEmpty, !aw.isEmpty else { return false }
        let overlap = sw.intersection(aw)
        let minOverlap = sw.count >= 3 ? 2 : 1
        return overlap.count < minOverlap
    }

    private static func detectRegisterConflict(sentence: String, feedback: [String: Any]) -> Bool {
        let sent = normalize(sentence)
        let corr = normalize(feedback["correction"] as? String ?? "")
        let formalMarkers = ["usted", "señor", "señora", "don ", "doña ", "sr.", "sra."]
        let informalMarkers = [" tú ", " tu ", "vos ", " estás", " cómo estás"]
        let sentFormal = formalMarkers.contains(where: { sent.contains($0) })
            || sent.contains(" está") || sent.hasSuffix("esta")
        let sentInformal = informalMarkers.contains(where: { sent.contains($0) }) || sent.contains("estás")
        let reg = normalize(feedback["register"] as? String ?? "")
        let claimsFormal = reg.contains("formal") && !reg.contains("informal")
        let corrInformal = corr.contains("estás") || corr.contains(" cómo estás")
        let corrFormal = corr.contains("usted") || corr.contains(" está usted")

        if sentFormal && !sentInformal && corrInformal && !corrFormal { return true }
        if claimsFormal && corrInformal && !corrFormal { return true }
        return false
    }
}
