package com.parlance.interpreterguide;

import android.content.Context;
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

import net.ladenthin.llama.LlamaModel;
import net.ladenthin.llama.parameters.InferenceParameters;
import net.ladenthin.llama.parameters.ModelParameters;

/**
 * Android counterpart to {@code ParlanceSLMEngine.swift}. Same prompts, same
 * JSON shape, same languages. Weights are GGUF exports of the HuggingFace
 * merges iOS already ships as MLX.
 */
public class ParlanceSLMEngine {

    private static final String TAG = "ParlanceSLM";
    private static final List<String> SUPPORTED = Arrays.asList("es", "fr");
    private static final int MAX_TOKENS = 768;

    private final Context context;
    private LlamaModel model;
    private String loadedLanguage;

    public ParlanceSLMEngine(Context context) {
        this.context = context.getApplicationContext();
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
                    "Parlance Coach model is not installed in this build. "
                            + "Run python3 training/export_parlance_gguf.py --lang "
                            + language + " and rebuild.");
        }
        ensureLoaded(language, weights);

        String system = systemPrompt(language, ragContext == null ? "" : ragContext);
        String user = userPrompt(language, sentence);
        String prompt = chatPrompt(system, user);

        InferenceParameters infer = new InferenceParameters(prompt)
                .withTemperature(0f)
                .withNPredict(MAX_TOKENS);
        String raw = model.complete(infer);
        return parseFeedback(raw);
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

    private File resolveModelFile(String language, boolean copyAsset) {
        String name = "parlance-" + language + ".gguf";
        File onDisk = new File(new File(context.getFilesDir(), "models"), name);
        if (isUsableModel(onDisk)) {
            return onDisk;
        }
        File packed = playAssetPackFile(name);
        if (isUsableModel(packed)) {
            return packed;
        }
        String assetName = "models/" + name;
        if (!assetExists(assetName)) {
            return null;
        }
        if (!copyAsset) {
            return onDisk;
        }
        try {
            copyAsset(assetName, onDisk);
            return onDisk;
        } catch (IOException e) {
            Log.e(TAG, "Could not copy " + assetName, e);
            return null;
        }
    }

    public boolean isAvailable(String language) {
        String name = "parlance-" + language + ".gguf";
        File onDisk = new File(new File(context.getFilesDir(), "models"), name);
        if (isUsableModel(onDisk)) return true;
        if (isUsableModel(playAssetPackFile(name))) return true;
        return assetExists("models/" + name);
    }

    private static boolean isUsableModel(File file) {
        return file != null && file.isFile() && file.length() > 1_000_000;
    }

    private File playAssetPackFile(String name) {
        try {
            AssetPackManager manager = AssetPackManagerFactory.getInstance(context);
            AssetPackLocation location = manager.getPackLocation("parlance_models");
            if (location == null || location.assetsPath() == null) {
                return null;
            }
            return new File(location.assetsPath(), name);
        } catch (Throwable e) {
            return null;
        }
    }

    private boolean assetExists(String name) {
        try (InputStream ignored = context.getAssets().open(name)) {
            return true;
        } catch (IOException e) {
            return false;
        }
    }

    private void copyAsset(String name, File dest) throws IOException {
        File parent = dest.getParentFile();
        if (parent != null && !parent.exists() && !parent.mkdirs()) {
            throw new IOException("Could not create " + parent);
        }
        File tmp = new File(dest.getAbsolutePath() + ".part");
        try (InputStream in = context.getAssets().open(name);
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
        return "Analyze this Spanish sentence: \"" + sentence + "\"";
    }

    private static String systemPrompt(String language, String ragContext) {
        String dialect = "fr".equals(language)
                ? "France and Canadian (Québec) dialect variation"
                : "Latin American dialect variation";
        String langName = "fr".equals(language) ? "French" : "Spanish";
        StringBuilder prompt = new StringBuilder();
        prompt.append("You are a ").append(langName)
                .append(" grammar coach for interpreter training, with expertise in ")
                .append(dialect)
                .append(". Do NOT assume the learner picked a CEFR level.\n\n")
                .append("CRITICAL ACCURACY RULES:\n")
                .append("- Do NOT invent grammatical errors. Only flag real, clear mistakes.\n")
                .append("- Grammatically correct sentences are \"Excellent\" — but explanation must still cite specific structures in the learner's words (not generic praise).\n")
                .append("- Only mark \"Needs Improvement\" when there is an actual grammar error — not a style preference.\n")
                .append("- complexity_note must describe THIS sentence's structures — never guess CEFR from word count alone.\n")
                .append("- next_level_alt MUST rewrite the sentence at a higher level — never copy the input verbatim.\n")
                .append("- tip MUST include at least one complete example sentence in ")
                .append(langName)
                .append(" showing a stronger phrasing.\n")
                .append("- ALL example sentences (correction, next_level_alt, target_level_alt) MUST be complete sentences in ")
                .append(langName).append(".\n")
                .append("- grammar_rule, explanation, register, and tip MUST be in English.\n");
        if (!ragContext.isEmpty()) {
            prompt.append("\nREFERENCE KNOWLEDGE (use these rules to verify accuracy — do not invent errors outside them):\n")
                    .append(ragContext).append('\n');
        }
        prompt.append("\nRespond with ONLY a valid JSON object (no markdown fences):\n")
                .append("{\n")
                .append("  \"assessed_level\": \"A1\" | \"A2\" | \"B1\" | \"B2\" | \"C1\" | \"C2\" | null,\n")
                .append("  \"complexity_note\": \"1–2 English sentences on sentence complexity\",\n")
                .append("  \"status\": \"Excellent\" or \"Needs Improvement\",\n")
                .append("  \"grammar_rule\": \"The specific grammar rule\",\n")
                .append("  \"explanation\": \"WHY the sentence is correct or incorrect\",\n")
                .append("  \"correction\": null or \"Corrected sentence\",\n")
                .append("  \"register\": \"Formal or informal and whether appropriate\",\n")
                .append("  \"next_level_alt\": \"Same idea one CEFR level above\",\n")
                .append("  \"target_level_alt\": \"Same idea two levels above, or null\",\n")
                .append("  \"tip\": \"Practical tip with a complete example sentence\"\n")
                .append("}\n");
        return prompt.toString();
    }

    static JSONObject parseFeedback(String raw) throws JSONException {
        String cleaned = raw == null ? "" : raw.replace("```json", "").replace("```", "").trim();
        int start = cleaned.indexOf('{');
        if (start < 0) {
            throw new JSONException("No JSON object in model output");
        }
        int depth = 0;
        int end = -1;
        for (int i = start; i < cleaned.length(); i++) {
            char ch = cleaned.charAt(i);
            if (ch == '{') depth++;
            if (ch == '}') {
                depth--;
                if (depth == 0) {
                    end = i;
                    break;
                }
            }
        }
        if (end < 0) {
            throw new JSONException("Unclosed JSON object in model output");
        }
        return new JSONObject(cleaned.substring(start, end + 1));
    }
}
