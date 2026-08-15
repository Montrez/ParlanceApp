import Foundation

/// Swift port of the shared coach-rules engine (`training/coach_rules.py`,
/// `Parlance/web/coach-rules-engine.js`). Loads the full ES/FR rule packs
/// (`shared/coach-rules/{es,fr}.json`) — bundled in the app via the already-shipped
/// `coach-rules-{es,fr}.js` resources — instead of hand-porting a small regex subset.
///
/// Phase 1 of issue #30's consolidation plan (see `docs/coach-heuristic-consolidation.md`):
/// this is the single Swift source of truth for detect/repair grammar rules. CEFR
/// plausibility, hallucination detection, and register conflict stay in
/// `FeedbackSanitizer`/`ParlanceSLMFeedbackValidator` per that doc's recommendation.
enum CoachRulesEngine {

    struct RuleIssue {
        let id: String
        let grammarRule: String
        let issue: String
        let mentions: [String]
    }

    private struct RulePack: Decodable {
        let grammarRuleDefault: String?
        let feminineNouns: [String]?
        let rules: [Rule]

        enum CodingKeys: String, CodingKey {
            case grammarRuleDefault = "grammar_rule_default"
            case feminineNouns = "feminine_nouns"
            case rules
        }
    }

    private struct Rule: Decodable {
        let id: String
        let priority: Int?
        let detect: Detect
        let repair: [Repair]?
        let issue: String?
        let mention: [String]?
        let grammarRule: String?

        enum CodingKeys: String, CodingKey {
            case id, priority, detect, repair, issue, mention
            case grammarRule = "grammar_rule"
        }

        struct Detect: Decodable {
            let pattern: String?
            let flags: String?
            let unless: String?
            let unlessPattern: String?
            let requirePattern: String?

            enum CodingKeys: String, CodingKey {
                case pattern, flags, unless
                case unlessPattern = "unless_pattern"
                case requirePattern = "require_pattern"
            }
        }

        struct Repair: Decodable {
            let pattern: String
            let replace: String
            let flags: String?
            let once: Bool?
        }
    }

    // MARK: - Pack loading (extract JSON payload from the already-bundled sync'd JS resource,
    // so there is exactly one bundled copy of the rules — no separate Xcode resource wiring).

    // Guarded by cacheLock, not by actor isolation — accessed from whatever thread calls
    // detectIssues/applyRepairs (cloud analyzer callbacks aren't guaranteed to be @MainActor).
    private static nonisolated(unsafe) var cache: [String: RulePack] = [:]
    private static let cacheLock = NSLock()

    private static let supportedKeys: Set<String> = ["es", "fr", "en"]

    private static func loadPack(language: String) -> RulePack? {
        let key = supportedKeys.contains(language) ? language : "es"
        cacheLock.lock()
        defer { cacheLock.unlock() }
        if let cached = cache[key] { return cached }
        guard let pack = readPack(key: key) else { return nil }
        cache[key] = pack
        return pack
    }

    private static func readPack(key: String) -> RulePack? {
        guard let url = Bundle.main.url(forResource: "coach-rules-\(key)", withExtension: "js"),
              let js = try? String(contentsOf: url, encoding: .utf8),
              let jsonText = extractJSONObject(from: js),
              let data = jsonText.data(using: .utf8) else {
            return nil
        }
        return try? JSONDecoder().decode(RulePack.self, from: data)
    }

    /// Finds the `{ ... }` JSON object assigned to `root.ParlanceCoachRules{ES,FR} = {...}`
    /// in the synced JS wrapper, using balanced-brace scanning (string-literal aware) rather
    /// than naive first/last brace matching, since the JSON itself contains nested braces.
    private static func extractJSONObject(from js: String) -> String? {
        guard let eqRange = js.range(of: "= {") else { return nil }
        let start = js.index(before: eqRange.upperBound)
        var depth = 0
        var inString = false
        var escaped = false
        var idx = start
        let end = js.endIndex
        while idx < end {
            let c = js[idx]
            if inString {
                if escaped {
                    escaped = false
                } else if c == "\\" {
                    escaped = true
                } else if c == "\"" {
                    inString = false
                }
            } else if c == "\"" {
                inString = true
            } else if c == "{" {
                depth += 1
            } else if c == "}" {
                depth -= 1
                if depth == 0 {
                    return String(js[start...idx])
                }
            }
            idx = js.index(after: idx)
        }
        return nil
    }

    // MARK: - Matching

    private static func regexOptions(_ flags: String?) -> NSRegularExpression.Options {
        (flags ?? "i").contains("i") ? [.caseInsensitive] : []
    }

    private static func ruleMatches(_ text: String, _ rule: Rule) -> Bool {
        let detect = rule.detect
        let opts = regexOptions(detect.flags)
        let full = NSRange(location: 0, length: (text as NSString).length)

        if let unless = detect.unless, !unless.isEmpty, text.contains(unless) {
            return false
        }
        if let unlessPattern = detect.unlessPattern,
           let re = try? NSRegularExpression(pattern: unlessPattern, options: opts),
           re.firstMatch(in: text, range: full) != nil {
            return false
        }
        if let requirePattern = detect.requirePattern {
            guard let re = try? NSRegularExpression(pattern: requirePattern, options: opts),
                  re.firstMatch(in: text, range: full) != nil else {
                return false
            }
        }
        guard let pattern = detect.pattern, !pattern.isEmpty,
              let re = try? NSRegularExpression(pattern: pattern, options: opts) else {
            return false
        }
        return re.firstMatch(in: text, range: full) != nil
    }

    // MARK: - Detect

    private static func normalize(_ text: String) -> String {
        text.lowercased()
            .folding(options: .diacriticInsensitive, locale: .current)
            .replacingOccurrences(of: #"[^\w\s]"#, with: " ", options: .regularExpression)
            .replacingOccurrences(of: #"\s+"#, with: " ", options: .regularExpression)
            .trimmingCharacters(in: .whitespacesAndNewlines)
    }

    static func detectIssues(sentence: String, language: String) -> [RuleIssue] {
        guard let pack = loadPack(language: language), !sentence.isEmpty else { return [] }
        var matched: [RuleIssue] = []
        var seen = Set<String>()
        let sorted = pack.rules.sorted { ($0.priority ?? 99) < ($1.priority ?? 99) }
        for rule in sorted where !seen.contains(rule.id) {
            guard ruleMatches(sentence, rule) else { continue }
            matched.append(RuleIssue(
                id: rule.id,
                grammarRule: rule.grammarRule ?? pack.grammarRuleDefault ?? "",
                issue: rule.issue ?? "",
                mentions: rule.mention ?? []
            ))
            seen.insert(rule.id)
        }

        // Mirrors detectFeminineTodoIssues() in coach-rules-engine.js: a cross-rule agreement
        // check that isn't a single regex rule, driven by the pack's feminine_nouns list
        // (Spanish-only — only es.json defines feminine_nouns).
        if language == "es", let nouns = pack.feminineNouns, !nouns.isEmpty,
           !seen.contains("todo_before_feminine_noun") {
            let norm = normalize(sentence)
            let alreadyCorrect = norm.contains("toda la aplicaci")
                || sentence.range(of: #"\btodo\s+la\s+aplicaci"#, options: [.regularExpression, .caseInsensitive]) != nil
                || sentence.range(of: #"\btodo\s+por\s+la\s+aplicaci"#, options: [.regularExpression, .caseInsensitive]) != nil
            let hasTodo = norm.range(of: #"\btodo\b"#, options: .regularExpression) != nil
            let hasFemNoun = nouns.contains { norm.contains(normalize($0)) }
            let hasToda = sentence.range(of: #"\btoda\b"#, options: [.regularExpression, .caseInsensitive]) != nil
            if !alreadyCorrect, hasTodo, hasFemNoun, !hasToda,
               sentence.range(of: "aplicaci", options: .caseInsensitive) != nil {
                matched.append(RuleIssue(
                    id: "todo_before_feminine_noun",
                    grammarRule: "Gender agreement (todo/toda + feminine noun)",
                    issue: "«Aplicación» is feminine — use «toda la aplicación», not «todo».",
                    mentions: ["toda la aplicación", "feminine todo/toda"]
                ))
            }
        }
        return matched
    }

    // MARK: - Repair

    /// Rule packs are shared with Python (`re.sub`, `\1 \2` backreferences) and JS
    /// (`String.replace`, `$1 $2`). Convert `\N` → `$N` so NSRegularExpression's `$1`
    /// template syntax matches the same "replace" string both other runtimes honor.
    private static func toTemplate(_ raw: String) -> String {
        var result = ""
        let chars = Array(raw)
        var i = 0
        while i < chars.count {
            if chars[i] == "\\", i + 1 < chars.count, chars[i + 1].isNumber {
                result.append("$")
                result.append(chars[i + 1])
                i += 2
            } else {
                result.append(chars[i])
                i += 1
            }
        }
        return result
    }

    static func applyRepairs(sentence: String, language: String) -> String {
        guard let pack = loadPack(language: language) else {
            return sentence.trimmingCharacters(in: .whitespacesAndNewlines)
        }
        var c = sentence.trimmingCharacters(in: .whitespacesAndNewlines)
        let sorted = pack.rules.sorted { ($0.priority ?? 99) < ($1.priority ?? 99) }
        for rule in sorted {
            guard ruleMatches(c, rule) else { continue }
            for step in rule.repair ?? [] {
                guard let re = try? NSRegularExpression(pattern: step.pattern, options: regexOptions(step.flags ?? "gi")) else {
                    continue
                }
                let template = toTemplate(step.replace)
                let range = NSRange(location: 0, length: (c as NSString).length)
                if step.once == true {
                    guard let match = re.firstMatch(in: c, range: range) else { continue }
                    let replacement = re.replacementString(for: match, in: c, offset: 0, template: template)
                    let mutable = NSMutableString(string: c)
                    mutable.replaceCharacters(in: match.range, with: replacement)
                    c = mutable as String
                } else {
                    c = re.stringByReplacingMatches(in: c, options: [], range: range, withTemplate: template)
                }
            }
        }
        return c.replacingOccurrences(of: #"\s+"#, with: " ", options: .regularExpression)
            .trimmingCharacters(in: .whitespacesAndNewlines)
    }

    static func analyze(sentence: String, language: String) -> (issues: [RuleIssue], correction: String?) {
        let issues = detectIssues(sentence: sentence, language: language)
        let correction = applyRepairs(sentence: sentence, language: language)
        let changed = correction != sentence.trimmingCharacters(in: .whitespacesAndNewlines)
        return (issues, changed ? correction : nil)
    }

    /// True when a rule pack is bundled and loadable for this language (es/fr/en).
    static func isSupported(language: String) -> Bool {
        loadPack(language: language) != nil
    }
}
