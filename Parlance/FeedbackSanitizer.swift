import Foundation

/// Cloud-path parity layer for `ExternalAnalyzer` (issue #31): hallucination detection,
/// known-error regex repairs, and register-conflict repair — the same class of checks the
/// on-device validator applies (`ParlanceSLMFeedbackValidator.swift`), kept in sync with the
/// shared rule pack (`shared/coach-rules/es.json`, `Parlance/web/coach-rules-engine.js`).
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
        language == "fr"
            ? assessedLevelPlausibleFrench(sentence: sentence, level: level)
            : assessedLevelPlausibleSpanish(sentence: sentence, level: level)
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
        language == "fr"
            ? detectRegisterConflictFrench(sentence: sentence, feedback: feedback)
            : detectRegisterConflictSpanish(sentence: sentence, feedback: feedback)
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

    // MARK: - Known-error regex repairs (ported from shared/coach-rules/es.json +
    // ParlanceSLMFeedbackValidator's known-error patterns; French si-clause + typography from the
    // on-device French heuristics)

    struct DetectedIssue {
        let id: String
        let grammarRule: String
        let issue: String
        let mentions: [String]
    }

    static func detectKnownIssues(sentence: String, language: String) -> [DetectedIssue] {
        language == "fr" ? detectFrenchIssues(sentence) : detectSpanishIssues(sentence)
    }

    static func applyKnownRepairs(sentence: String, language: String) -> String {
        language == "fr" ? applyFrenchRepairs(sentence) : applySpanishRepairs(sentence)
    }

    private static func detectSpanishIssues(_ sentence: String) -> [DetectedIssue] {
        var issues: [DetectedIssue] = []
        let norm = normalizeForCompare(sentence)

        if sentence.range(
            of: #"(?i)[Cc]ómo\s+es\s+usted\s+d[ií]a\s+(se[nñ]or|se[nñ]ora)\b"#,
            options: .regularExpression
        ) != nil {
            issues.append(DetectedIssue(
                id: "greeting_vocative_order",
                grammarRule: "Ser vs estar + word order in formal greetings",
                issue: "Use «¿Cómo está usted hoy, señor?» — estar (not ser) for wellbeing, with natural vocative order.",
                mentions: ["cómo está", "ser vs estar", "vocative"]
            ))
        } else if sentence.range(of: #"(?i)[Cc]ómo\s+es\b"#, options: .regularExpression) != nil,
                  norm.range(of: #"\b(usted|tu|senor|senora|dia)\b"#, options: .regularExpression) != nil,
                  norm.range(of: #"usted\s+dia\s+senor"#, options: .regularExpression) == nil {
            issues.append(DetectedIssue(
                id: "como_es_wellbeing",
                grammarRule: "Ser vs estar — «¿Cómo está?» for wellbeing",
                issue: "Asking after someone's state uses «¿Cómo está …?» (estar), not «Cómo es …» (ser).",
                mentions: ["cómo está", "ser vs estar", "wellbeing"]
            ))
        }

        if sentence.range(
            of: #"(?i)\b(a)\s+(ver|hacer|comprar|ir|llegar|terminar)\s+(un|una|el|la|al|a la)\b"#,
            options: .regularExpression
        ) != nil,
           sentence.range(
               of: #"(?i)\bpara\s+(ver|hacer|comprar|ir|llegar|terminar)\b"#,
               options: .regularExpression
           ) == nil {
            issues.append(DetectedIssue(
                id: "para_purpose_infinitive",
                grammarRule: "Por vs para — purpose before infinitive",
                issue: "Purpose before an infinitive uses «para» (e.g. «dinero para ver»), not bare «a».",
                mentions: ["para ver", "por vs para", "purpose"]
            ))
        }

        if sentence.range(
            of: #"(?i)\b(espero|quiero|deseo|necesito|ojal[aá])\s+que\b"#,
            options: .regularExpression
        ) != nil,
           sentence.range(
               of: #"(?i)\b(todos|todo|t[uú]|ell[oa]|nosotros|usted|ustedes)\s+(ir|ser|estar|tener|hacer|poder|venir|decir)\b"#,
               options: .regularExpression
           ) != nil,
           norm.range(
               of: #"\b(vaya|vayan|sea|sean|este|esten|tenga|tengan|haga|hagan|pueda|puedan|venga|vengan|diga|digan)\b"#,
               options: .regularExpression
           ) == nil {
            issues.append(DetectedIssue(
                id: "que_clause_infinitive_subjunctive",
                grammarRule: "Subjunctive after «espero que» / «quiero que» — not infinitive in the subordinate clause",
                issue: "After a subjunctive trigger («espero que», «quiero que»…), use subjunctive in the subordinate clause — not a bare infinitive («todos ir» → «todos vayan»).",
                mentions: ["subjunctive", "espero que", "vayan", "present subjunctive"]
            ))
        }

        if sentence.range(
            of: #"(?i)\bsi\b[^.!?]*\b(tendr[ií]a|har[ií]a|ser[ií]a|podr[ií]a|querr[ií]a|dir[ií]a|vendr[ií]a)\b"#,
            options: .regularExpression
        ) != nil {
            issues.append(DetectedIssue(
                id: "si_clause_conditional_protasis",
                grammarRule: "Si clauses: imperfect subjunctive in the protasis, not conditional",
                issue: "After «si» introducing a hypothetical condition, Spanish uses the imperfect subjunctive (e.g. «tuviera»), not the conditional («tendría»).",
                mentions: ["tuviera", "imperfect subjunctive", "si clause"]
            ))
        }

        if sentence.range(of: #"(?i)\b(le|les)\s+echo\s+de\s+menos\b"#, options: .regularExpression) != nil {
            issues.append(DetectedIssue(
                id: "leismo_echar_de_menos",
                grammarRule: "«Echar de menos» takes a direct object (lo/la), not «le»",
                issue: "«Echar de menos» governs a direct object pronoun (lo/la/los/las) — «le echo de menos» is leísmo.",
                mentions: ["la echo de menos", "lo echo de menos", "direct object", "leísmo"]
            ))
        }

        return issues
    }

    private static func applySpanishRepairs(_ sentence: String) -> String {
        var c = sentence
        c = c.replacingOccurrences(
            of: #"(?i)[Cc]ómo\s+es\s+usted\s+d[ií]a\s+(se[nñ]or|se[nñ]ora)\b"#,
            with: "¿Cómo está usted hoy, $1",
            options: .regularExpression
        )
        if c.range(of: #"(?i)[Cc]ómo\s+es\b"#, options: .regularExpression) != nil,
           !c.localizedCaseInsensitiveContains("cómo está") {
            c = c.replacingOccurrences(of: #"(?i)[Cc]ómo\s+es\b"#, with: "¿Cómo está", options: .regularExpression)
        }
        c = c.replacingOccurrences(
            of: #"(?i)\b(a)\s+(ver|hacer|comprar|ir|llegar|terminar)\s+(un|una|el|la|al|a la)\b"#,
            with: "para $2 $3",
            options: .regularExpression
        )
        let queReplacements: [(String, String)] = [
            (#"(?i)\btodos\s+ir\b"#, "todos vayan"), (#"(?i)\btodo\s+ir\b"#, "todo vaya"),
            (#"(?i)\btodos\s+ser\b"#, "todos sean"), (#"(?i)\btodo\s+ser\b"#, "todo sea"),
            (#"(?i)\btodos\s+estar\b"#, "todos estén"), (#"(?i)\btodo\s+estar\b"#, "todo esté"),
            (#"(?i)\btodos\s+tener\b"#, "todos tengan"), (#"(?i)\btodo\s+tener\b"#, "todo tenga"),
            (#"(?i)\btodos\s+hacer\b"#, "todos hagan"), (#"(?i)\btodo\s+hacer\b"#, "todo haga"),
        ]
        for (pattern, sub) in queReplacements {
            c = c.replacingOccurrences(of: pattern, with: sub, options: .regularExpression)
        }
        let siReplacements: [(String, String)] = [
            (#"(?i)\btendría\b"#, "tuviera"), (#"(?i)\btendria\b"#, "tuviera"),
            (#"(?i)\bharía\b"#, "hiciera"), (#"(?i)\bharia\b"#, "hiciera"),
            (#"(?i)\bsería\b"#, "fuera"), (#"(?i)\bseria\b"#, "fuera"),
            (#"(?i)\bpodría\b"#, "pudiera"), (#"(?i)\bpodria\b"#, "pudiera"),
        ]
        for (pattern, sub) in siReplacements {
            c = c.replacingOccurrences(of: pattern, with: sub, options: .regularExpression)
        }
        c = c.replacingOccurrences(
            of: #"(?i)\bles\s+echo\s+de\s+menos\b"#, with: "las echo de menos", options: .regularExpression
        )
        c = c.replacingOccurrences(
            of: #"(?i)\ble\s+echo\s+de\s+menos\b"#, with: "la echo de menos", options: .regularExpression
        )
        return c
    }

    private static func detectFrenchIssues(_ sentence: String) -> [DetectedIssue] {
        var issues: [DetectedIssue] = []
        if sentence.range(
            of: #"(?i)\bsi\b[^.!?]*\b(j'aurais|tu aurais|il aurait|elle aurait|nous aurions|vous auriez)\b"#,
            options: .regularExpression
        ) != nil {
            issues.append(DetectedIssue(
                id: "si_clause_conditional_protasis_fr",
                grammarRule: "Si clauses: imparfait in the protasis, not conditionnel",
                issue: "After « si » introducing a hypothetical condition, French uses the imparfait (« j'avais »), not the conditionnel (« j'aurais »).",
                mentions: ["j'avais", "imparfait", "si clause"]
            ))
        }
        if hasFrenchTypographyIssue(sentence) {
            issues.append(DetectedIssue(
                id: "french_typography_spacing",
                grammarRule: "French typography (espaces insécables)",
                issue: "French requires a space before ? ! ; : — e.g. « Comment allez-vous ? »",
                mentions: ["typography", "espace", "?"]
            ))
        }
        return issues
    }

    static func hasFrenchTypographyIssue(_ sentence: String) -> Bool {
        sentence.range(of: #"\w[?!;:]"#, options: .regularExpression) != nil
    }

    private static func applyFrenchRepairs(_ sentence: String) -> String {
        var c = sentence
        let replacements: [(String, String)] = [
            (#"(?i)\bj'aurais\b"#, "j'avais"), (#"(?i)\btu aurais\b"#, "tu avais"),
            (#"(?i)\bil aurait\b"#, "il avait"), (#"(?i)\belle aurait\b"#, "elle avait"),
        ]
        for (pattern, sub) in replacements {
            c = c.replacingOccurrences(of: pattern, with: sub, options: .regularExpression)
        }
        if hasFrenchTypographyIssue(c) {
            c = c.replacingOccurrences(of: #"(\w)([?!;:])"#, with: "$1 $2", options: .regularExpression)
        }
        return c
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

        guard language == "es" || language == "fr" else { return }

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
