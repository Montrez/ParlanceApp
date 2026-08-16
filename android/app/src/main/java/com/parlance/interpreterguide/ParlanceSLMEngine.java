package com.parlance.interpreterguide;

import android.content.Context;
import android.content.pm.ApplicationInfo;
import android.content.res.AssetManager;
import android.util.Log;

import org.json.JSONException;
import org.json.JSONObject;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import com.google.android.play.core.assetpacks.AssetPackLocation;
import com.google.android.play.core.assetpacks.AssetPackManager;
import com.google.android.play.core.assetpacks.AssetPackManagerFactory;
import com.google.android.play.core.assetpacks.model.AssetPackStatus;

import net.ladenthin.llama.LlamaModel;
import net.ladenthin.llama.parameters.InferenceParameters;
import net.ladenthin.llama.parameters.ModelParameters;

/**
 * Android counterpart to {@code ParlanceSLMEngine.swift}. Prompts match
 * {@code ParlanceSLMFeedbackValidator} on iOS. JSON shape and languages
 * are the same. Weights are GGUF exports of the HuggingFace merges iOS
 * already ships as MLX. Thin or truncated model JSON is repaired here,
 * then the shared web sanitizer writes sentence-citing copy.
 */
public class ParlanceSLMEngine {

    private static final String TAG = "ParlanceSLM";
    private static final List<String> SUPPORTED = Arrays.asList("es", "fr", "en");
    private static final int MAX_TOKENS = 768;

    public interface AvailabilityListener {
        void onAvailabilityChanged();
    }

    private final Context context;
    private final Context assetsContext;
    private LlamaModel model;
    private String loadedLanguage;
    private AvailabilityListener availabilityListener;
    private volatile boolean installing;

    public ParlanceSLMEngine(Context context) {
        this.context = context.getApplicationContext();
        // Activity AssetManager sees install-time Play packs. Application
        // context often does not, which is why Play builds showed Groq and
        // "re-archive" while Studio debug (base-module assets) worked.
        this.assetsContext = context;
        requestPack();
        new Thread(this::warmup, "parlance-slm-warmup").start();
    }

    public boolean isInstalling() {
        return installing;
    }

    public void setAvailabilityListener(AvailabilityListener listener) {
        this.availabilityListener = listener;
        if (listener != null) {
            listener.onAvailabilityChanged();
        }
    }

    public boolean isAvailable() {
        for (String lang : SUPPORTED) {
            if (isAvailable(lang)) return true;
        }
        return false;
    }

    public List<String> availableLanguages() {
        List<String> found = new ArrayList<>();
        for (String lang : SUPPORTED) {
            if (isAvailable(lang)) found.add(lang);
        }
        return found;
    }

    public synchronized void unload() {
        if (model != null) {
            try {
                model.close();
            } catch (Exception e) {
                Log.w(TAG, "unload failed", e);
            }
            model = null;
            loadedLanguage = null;
        }
    }

    public synchronized JSONObject analyze(String sentence, String language, String ragContext)
            throws Exception {
        if (!SUPPORTED.contains(language)) {
            throw new IllegalArgumentException(
                    "Parlance Coach is not available for this journal language.");
        }
        File weights = resolveModelFile(language);
        if (weights == null) {
            throw new IllegalStateException(
                    "Parlance Coach is still installing on this phone. "
                            + "Keep the app open, or update from Play internal testing.");
        }
        ensureLoaded(language, weights);

        String system = systemPrompt(language, ragContext == null ? "" : ragContext);
        String user = userPrompt(language, sentence);
        String prompt = chatPrompt(system, user);

        InferenceParameters infer = new InferenceParameters(prompt)
                .withTemperature(0f)
                .withNPredict(MAX_TOKENS);
        String raw = model.complete(infer);
        try {
            return parseFeedback(raw);
        } catch (Exception e) {
            Log.w(TAG, "Coach JSON unusable, using fallback", e);
            return fallbackFeedback();
        }
    }

    private void ensureLoaded(String language, File weights) {
        if (model != null && language.equals(loadedLanguage)) {
            return;
        }
        unload();
        ModelParameters params = new ModelParameters().setModel(weights.getAbsolutePath());
        model = new LlamaModel(params);
        loadedLanguage = language;
    }

    private File resolveModelFile(String language) {
        return resolveModelFile(language, true);
    }

    private synchronized File resolveModelFile(String language, boolean copyAsset) {
        for (String name : modelFileNames(language)) {
            File found = resolveNamedModel(name, copyAsset);
            if (isUsableModel(found)) {
                return found;
            }
        }
        return null;
    }

    /** English shares the Spanish (then French) 0.5B GGUF until a dedicated export exists. */
    private static List<String> modelFileNames(String language) {
        if ("en".equals(language)) {
            return Arrays.asList("parlance-en.gguf", "parlance-es.gguf", "parlance-fr.gguf");
        }
        return Arrays.asList("parlance-" + language + ".gguf");
    }

    private File resolveNamedModel(String name, boolean copyAsset) {
        File onDisk = new File(new File(context.getFilesDir(), "models"), name);
        if (isUsableModel(onDisk)) {
            return onDisk;
        }
        File packed = playAssetPackFile(name);
        if (isUsableModel(packed)) {
            return packed;
        }
        AssetRef asset = findAsset(name);
        if (asset == null) {
            return null;
        }
        if (!copyAsset) {
            return onDisk;
        }
        try {
            copyAsset(asset, onDisk);
            return onDisk;
        } catch (IOException e) {
            Log.e(TAG, "Could not copy " + asset.path, e);
            return null;
        }
    }

    public boolean isAvailable(String language) {
        for (String name : modelFileNames(language)) {
            File onDisk = new File(new File(context.getFilesDir(), "models"), name);
            if (isUsableModel(onDisk)) return true;
            if (isUsableModel(playAssetPackFile(name))) return true;
            if (findAsset(name) != null) return true;
        }
        return false;
    }

    private static final class AssetRef {
        final AssetManager manager;
        final String path;

        AssetRef(AssetManager manager, String path) {
            this.manager = manager;
            this.path = path;
        }
    }

    /**
     * Install-time Play packs are merged into {@link AssetManager}, same as
     * debug {@code assets/models/}. Play Core {@code getPackLocation} is for
     * fast-follow / on-demand packs and returns null here.
     */
    private AssetRef findAsset(String name) {
        String[] candidates = { "models/" + name, name };
        for (AssetManager manager : assetManagers()) {
            for (String path : candidates) {
                if (assetExists(manager, path)) {
                    return new AssetRef(manager, path);
                }
            }
            String walked = walkForGguf(manager, name);
            if (walked != null) {
                return new AssetRef(manager, walked);
            }
        }
        return null;
    }

    private AssetManager[] assetManagers() {
        AssetManager activityAssets = assetsContext.getAssets();
        AssetManager appAssets = context.getAssets();
        if (activityAssets == appAssets) {
            return new AssetManager[] { activityAssets };
        }
        return new AssetManager[] { activityAssets, appAssets };
    }

    private static String walkForGguf(AssetManager manager, String name) {
        String[] roots = { "", "models" };
        for (String root : roots) {
            String[] kids;
            try {
                kids = manager.list(root);
            } catch (IOException e) {
                continue;
            }
            if (kids == null) continue;
            for (String kid : kids) {
                if (name.equals(kid)) {
                    return root.isEmpty() ? kid : root + "/" + kid;
                }
            }
        }
        return null;
    }

    private void warmup() {
        installing = true;
        notifyAvailability();
        logSplits();
        for (String lang : SUPPORTED) {
            File weights = resolveModelFile(lang, true);
            if (isUsableModel(weights)) {
                Log.i(TAG, "ready " + lang + " " + weights.length() + " bytes");
            } else {
                Log.w(TAG, "missing " + lang);
            }
        }
        installing = false;
        notifyAvailability();
    }

    private void notifyAvailability() {
        AvailabilityListener cb = availabilityListener;
        if (cb != null) cb.onAvailabilityChanged();
    }

    private void logSplits() {
        try {
            ApplicationInfo info = context.getApplicationInfo();
            Log.i(TAG, "sourceDir=" + info.sourceDir);
            if (info.splitSourceDirs == null) {
                Log.w(TAG, "no split APKs; Play may not have delivered parlance_models");
                return;
            }
            for (String split : info.splitSourceDirs) {
                Log.i(TAG, "split=" + split);
            }
        } catch (Throwable e) {
            Log.w(TAG, "split probe failed", e);
        }
    }

    private static boolean isUsableModel(File file) {
        return file != null && file.isFile() && file.length() > 1_000_000;
    }

    private void requestPack() {
        try {
            AssetPackManager manager = AssetPackManagerFactory.getInstance(context);
            manager.registerListener(state -> {
                if (!"parlance_models".equals(state.name())) return;
                int status = state.status();
                if (status == AssetPackStatus.COMPLETED) {
                    new Thread(this::warmup, "parlance-slm-pack").start();
                } else if (status == AssetPackStatus.FAILED) {
                    notifyAvailability();
                }
            });
            if (manager.getPackLocation("parlance_models") == null) {
                manager.fetch(java.util.Collections.singletonList("parlance_models"));
            }
        } catch (Throwable e) {
            Log.w(TAG, "asset pack probe failed", e);
        }
    }

    private File playAssetPackFile(String name) {
        try {
            AssetPackManager manager = AssetPackManagerFactory.getInstance(context);
            AssetPackLocation location = manager.getPackLocation("parlance_models");
            if (location == null || location.assetsPath() == null) {
                return null;
            }
            File direct = new File(location.assetsPath(), name);
            if (isUsableModel(direct)) return direct;
            File nested = new File(location.assetsPath(), "models/" + name);
            return isUsableModel(nested) ? nested : direct;
        } catch (Throwable e) {
            return null;
        }
    }

    private boolean assetExists(AssetManager manager, String name) {
        try (InputStream ignored = manager.open(name)) {
            return true;
        } catch (IOException e) {
            return false;
        }
    }

    private void copyAsset(AssetRef asset, File dest) throws IOException {
        File parent = dest.getParentFile();
        if (parent != null && !parent.exists() && !parent.mkdirs()) {
            throw new IOException("Could not create " + parent);
        }
        File tmp = new File(dest.getAbsolutePath() + ".part");
        try (InputStream in = asset.manager.open(asset.path);
             OutputStream out = new FileOutputStream(tmp)) {
            byte[] buf = new byte[64 * 1024];
            int n;
            while ((n = in.read(buf)) != -1) {
                out.write(buf, 0, n);
            }
        }
        if (!tmp.renameTo(dest)) {
            throw new IOException("Could not move " + tmp + " to " + dest);
        }
    }

    private static String chatPrompt(String system, String user) {
        return "<|im_start|>system\n" + system + "<|im_end|>\n"
                + "<|im_start|>user\n" + user + "<|im_end|>\n"
                + "<|im_start|>assistant\n";
    }

    private static String userPrompt(String language, String sentence) {
        if ("fr".equals(language)) {
            return "Analyze this French sentence: \"" + sentence + "\"";
        }
        if ("en".equals(language)) {
            return "Analyze this English sentence: \"" + sentence + "\"";
        }
        return "Analyze this Spanish sentence: \"" + sentence + "\"";
    }

    private static final String CEFR_COMPLEXITY_PROMPT =
            "CEFR & COMPLEXITY:\n"
                    + "- Do NOT set assessed_level unless highly confident from specific structures in this sentence. When uncertain, omit it and describe complexity in complexity_note without a CEFR label.\n"
                    + "- complexity_note: 1–2 English sentences on vocabulary, syntax, subordination, and register. Always include when possible, even without assessed_level.\n"
                    + "- next_level_alt / target_level_alt: only when assessed_level is set; otherwise use next_level_alt as a stronger rewrite without a level label.\n";

    private static String systemPrompt(String language, String ragContext) {
        String langName;
        StringBuilder prompt = new StringBuilder();
        if ("fr".equals(language)) {
            langName = "French";
            prompt.append("You are a French grammar coach for interpreter training, with expertise in ")
                    .append("France and Canadian (Québec) dialect variation. Do NOT assume the learner picked a CEFR level.\n\n")
                    .append(CEFR_COMPLEXITY_PROMPT)
                    .append("CRITICAL ACCURACY RULES:\n")
                    .append("- Do NOT invent grammatical errors. Only flag real, clear mistakes.\n")
                    .append("- Grammatically correct sentences are \"Excellent\" — but explanation must still cite specific structures in the learner's words (not generic praise).\n")
                    .append("- Only mark \"Needs Improvement\" when there is an actual grammar error — not a style preference.\n")
                    .append("- complexity_note must describe THIS sentence's structures — never guess CEFR from word count alone.\n")
                    .append("- next_level_alt MUST rewrite the sentence at a higher level — never copy the input verbatim.\n")
                    .append("- tip MUST include at least one complete example sentence in French showing a stronger phrasing.\n")
                    .append("- Never flag valid Canadian French (Québec) features as errors unless inappropriate for context.\n")
                    .append("- With formal address (madame/monsieur + « vous »), do NOT « correct » to informal « tu » without context.\n")
                    .append("- Si-clause: Si + imparfait → conditionnel (Si j'avais…, je ferais…) — NOT *Si j'aurais* in the protasis.\n")
                    .append("- ALL example sentences (correction, next_level_alt, target_level_alt) MUST be complete sentences in French.\n")
                    .append("- grammar_rule, explanation, register, and tip MUST be in English.\n")
                    .append("- For next_level_alt: same idea one CEFR level above assessed_level.\n")
                    .append("- For target_level_alt: same idea two levels above assessed_level (null at C1/C2).\n");
        } else if ("en".equals(language)) {
            langName = "English";
            prompt.append("You are an English grammar coach for interpreter training. Learners are often ")
                    .append("Spanish or French speakers writing English. Do NOT assume the learner picked a CEFR level.\n\n")
                    .append(CEFR_COMPLEXITY_PROMPT)
                    .append("CRITICAL ACCURACY RULES:\n")
                    .append("- Do NOT invent grammatical errors. Only flag real, clear mistakes.\n")
                    .append("- Grammatically correct sentences are \"Excellent\" — but explanation must still cite specific structures in the learner's words (not generic praise).\n")
                    .append("- Only mark \"Needs Improvement\" when there is an actual grammar error — not a style preference.\n")
                    .append("- complexity_note must describe THIS sentence's structures — never guess CEFR from word count alone.\n")
                    .append("- next_level_alt MUST rewrite the sentence at a higher level — never copy the input verbatim.\n")
                    .append("- tip MUST include at least one complete example sentence in English showing a stronger phrasing.\n")
                    .append("- Never flag valid English variety features as errors (UK/US/Indian/Caribbean/South African English, spelling colour/color, collective agreement).\n")
                    .append("- Do not \"correct\" a missing question mark or comma into a grammar error unless the sentence is otherwise unreadable.\n")
                    .append("- Watch for L1 calques: articles (a/an/the), do-support, if + would in the if-clause, prepositions, and subject-verb agreement.\n")
                    .append("- ALL example sentences (correction, next_level_alt, target_level_alt) MUST be complete sentences in English.\n")
                    .append("- grammar_rule, explanation, register, and tip MUST be in English.\n")
                    .append("- For next_level_alt: same idea one CEFR level above assessed_level.\n")
                    .append("- For target_level_alt: same idea two levels above assessed_level (null at C1/C2).\n");
        } else {
            langName = "Spanish";
            prompt.append("You are a Spanish grammar coach for interpreter training, with expertise in ")
                    .append("Latin American dialect variation. Do NOT assume the learner picked a CEFR level.\n\n")
                    .append(CEFR_COMPLEXITY_PROMPT)
                    .append("CRITICAL ACCURACY RULES:\n")
                    .append("- Do NOT invent grammatical errors. Only flag real, clear mistakes.\n")
                    .append("- Grammatically correct sentences are \"Excellent\" — but explanation must still cite specific structures in the learner's words (not generic praise).\n")
                    .append("- Only mark \"Needs Improvement\" when there is an actual grammar error — not a style preference.\n")
                    .append("- complexity_note must describe THIS sentence's structures — never guess CEFR from word count alone.\n")
                    .append("- next_level_alt MUST rewrite the sentence at a higher level — never copy the input verbatim.\n")
                    .append("- tip MUST include at least one complete example sentence in Spanish showing a stronger phrasing.\n")
                    .append("- Never flag valid dialect features as errors (e.g. voseo in Rioplatense, ustedes for all plural).\n")
                    .append("- With formal address (señor/señora + «está»), do NOT «correct» to informal «estás».\n")
                    .append("- After «si» in hypothetical clauses, use imperfect subjunctive (tuviera), NOT conditional (tendría).\n")
                    .append("- ALL example sentences (correction, next_level_alt, target_level_alt) MUST be complete sentences in Spanish.\n")
                    .append("- grammar_rule, explanation, register, and tip MUST be in English.\n")
                    .append("- For next_level_alt: same idea one CEFR level above assessed_level.\n")
                    .append("- For target_level_alt: same idea two levels above assessed_level (null at C1/C2).\n");
        }
        if (!ragContext.isEmpty()) {
            prompt.append("\nREFERENCE KNOWLEDGE (use these rules to verify accuracy — do not invent errors outside them):\n")
                    .append(ragContext).append('\n');
        }
        prompt.append("\nRespond with ONLY a valid JSON object (no markdown fences):\n")
                .append("{\n")
                .append("  \"assessed_level\": \"A1\" | \"A2\" | \"B1\" | \"B2\" | \"C1\" | \"C2\" | null,\n")
                .append("  \"complexity_note\": \"1–2 English sentences on sentence complexity (vocabulary, syntax, subordination, register)\",\n")
                .append("  \"status\": \"Excellent\" or \"Needs Improvement\",\n")
                .append("  \"grammar_rule\": \"The specific grammar rule — always name the rule, even when correct\",\n")
                .append("  \"explanation\": \"WHY the sentence is correct or incorrect — cite the learner's words\",\n")
                .append("  \"correction\": null or \"Corrected sentence in ").append(langName)
                .append(" (required when Needs Improvement)\",\n");
        if ("fr".equals(language)) {
            prompt.append("  \"register\": \"Formal (vous) or informal (tu) and whether appropriate for interpreter settings\",\n");
        } else if ("en".equals(language)) {
            prompt.append("  \"register\": \"Formal or informal and whether appropriate for interpreter settings\",\n");
        } else {
            prompt.append("  \"register\": \"Formal (usted) or informal (tú/vos) and whether appropriate for interpreter settings\",\n");
        }
        prompt.append("  \"next_level_alt\": \"Same idea rephrased one CEFR level above assessed_level, in ")
                .append(langName).append("\",\n")
                .append("  \"target_level_alt\": \"Same idea two levels above assessed_level, in ")
                .append(langName).append(" (null at C1/C2 if N/A)\",\n")
                .append("  \"tip\": \"Practical tip with a complete ").append(langName)
                .append(" example sentence showing stronger phrasing\"\n")
                .append("}\n");
        return prompt.toString();
    }

    /**
     * The 0.5B coach often emits almost-JSON: inner quotes in explanations,
     * trailing commas, or a cut-off object at max tokens. iOS sanitizes via
     * {@code ParlanceSLMFeedbackValidator}; Android must not throw that raw
     * {@code JSONException} into the Feedback panel.
     */
    static JSONObject parseFeedback(String raw) throws JSONException {
        String cleaned = raw == null ? "" : raw.replace("```json", "").replace("```", "").trim();
        int start = cleaned.indexOf('{');
        if (start < 0) {
            throw new JSONException("No JSON object in model output");
        }
        String slice = repairUnescapedQuotes(cleaned.substring(start));
        int end = findObjectEnd(slice, 0);
        if (end < 0) {
            slice = closeTruncated(slice);
        } else {
            slice = slice.substring(0, end + 1);
        }
        slice = slice.replaceAll(",\\s*}", "}").replaceAll(",\\s*]", "]");
        try {
            return normalizeFeedback(new JSONObject(slice));
        } catch (JSONException first) {
            JSONObject extracted = extractFeedbackFields(slice);
            if (extracted.length() > 0) {
                return normalizeFeedback(extracted);
            }
            throw first;
        }
    }

    /**
     * Empty fields so the shared web sanitizer can write sentence-citing copy.
     * Do not inject a generic "could not finish a full note" explanation here.
     */
    static JSONObject fallbackFeedback() {
        JSONObject out = new JSONObject();
        try {
            out.put("status", "Excellent");
            out.put("grammar_rule", "");
            out.put("explanation", "");
            out.put("_coach_incomplete", true);
        } catch (JSONException ignored) {
            // keys above are valid
        }
        return out;
    }

    private static JSONObject normalizeFeedback(JSONObject raw) throws JSONException {
        String status = raw.optString("status", "Excellent");
        if (!"Excellent".equals(status) && !"Needs Improvement".equals(status)) {
            status = "Excellent";
        }
        JSONObject out = new JSONObject();
        out.put("status", status);
        String rule = raw.optString("grammar_rule", raw.optString("grammarRule", ""));
        out.put("grammar_rule", rule);
        out.put("explanation", raw.optString("explanation", ""));
        String[] optional = {
            "correction", "register", "next_level_alt", "target_level_alt",
            "tip", "assessed_level", "complexity_note"
        };
        for (String key : optional) {
            String val = raw.optString(key, "");
            if (!val.isEmpty() && !"null".equals(val)) {
                out.put(key, val);
            }
        }
        return out;
    }

    private static final String[] FEEDBACK_KEYS = {
        "assessed_level", "complexity_note", "status", "grammar_rule",
        "explanation", "correction", "register", "next_level_alt",
        "target_level_alt", "tip"
    };

    private static JSONObject extractFeedbackFields(String json) {
        JSONObject out = new JSONObject();
        for (String key : FEEDBACK_KEYS) {
            String needle = "\"" + key + "\"";
            int keyAt = json.indexOf(needle);
            if (keyAt < 0) continue;
            int colon = json.indexOf(':', keyAt + needle.length());
            if (colon < 0) continue;
            int i = colon + 1;
            while (i < json.length() && Character.isWhitespace(json.charAt(i))) i++;
            if (i >= json.length()) continue;
            if (json.startsWith("null", i)) continue;
            if (json.charAt(i) != '"') continue;
            int close = findStringEnd(json, i);
            if (close < 0) continue;
            try {
                out.put(key, json.substring(i + 1, close)
                        .replace("\\\"", "\"")
                        .replace("\\n", "\n"));
            } catch (JSONException ignored) {
                // skip unreadable field
            }
        }
        return out;
    }

    /** Escape a {@code "} that is inside a value, not the key/value delimiter. */
    static String repairUnescapedQuotes(String json) {
        StringBuilder out = new StringBuilder(json.length() + 16);
        boolean inString = false;
        boolean escape = false;
        for (int i = 0; i < json.length(); i++) {
            char ch = json.charAt(i);
            if (!inString) {
                out.append(ch);
                if (ch == '"') inString = true;
                continue;
            }
            if (escape) {
                out.append(ch);
                escape = false;
                continue;
            }
            if (ch == '\\') {
                out.append(ch);
                escape = true;
                continue;
            }
            if (ch == '"') {
                int j = i + 1;
                while (j < json.length() && Character.isWhitespace(json.charAt(j))) j++;
                char next = j < json.length() ? json.charAt(j) : 0;
                if (next == ':' || next == ',' || next == '}' || next == ']' || next == 0) {
                    out.append(ch);
                    inString = false;
                } else {
                    out.append('\\').append('"');
                }
                continue;
            }
            out.append(ch);
        }
        return out.toString();
    }

    private static int findObjectEnd(String s, int start) {
        boolean inString = false;
        boolean escape = false;
        int depth = 0;
        for (int i = start; i < s.length(); i++) {
            char ch = s.charAt(i);
            if (inString) {
                if (escape) {
                    escape = false;
                    continue;
                }
                if (ch == '\\') {
                    escape = true;
                    continue;
                }
                if (ch == '"') inString = false;
                continue;
            }
            if (ch == '"') {
                inString = true;
                continue;
            }
            if (ch == '{') depth++;
            else if (ch == '}') {
                depth--;
                if (depth == 0) return i;
            }
        }
        return -1;
    }

    private static int findStringEnd(String s, int openQuote) {
        boolean escape = false;
        for (int i = openQuote + 1; i < s.length(); i++) {
            char ch = s.charAt(i);
            if (escape) {
                escape = false;
                continue;
            }
            if (ch == '\\') {
                escape = true;
                continue;
            }
            if (ch == '"') return i;
        }
        return -1;
    }

    static String closeTruncated(String slice) {
        boolean inString = false;
        boolean escape = false;
        int brace = 0;
        for (int i = 0; i < slice.length(); i++) {
            char ch = slice.charAt(i);
            if (inString) {
                if (escape) {
                    escape = false;
                    continue;
                }
                if (ch == '\\') {
                    escape = true;
                    continue;
                }
                if (ch == '"') inString = false;
                continue;
            }
            if (ch == '"') inString = true;
            else if (ch == '{') brace++;
            else if (ch == '}') brace--;
        }
        StringBuilder sb = new StringBuilder(slice);
        if (inString) sb.append('"');
        int k = sb.length() - 1;
        while (k >= 0 && Character.isWhitespace(sb.charAt(k))) k--;
        if (k >= 0 && sb.charAt(k) == ',') sb.deleteCharAt(k);
        while (brace > 0) {
            sb.append('}');
            brace--;
        }
        return sb.toString();
    }
}
