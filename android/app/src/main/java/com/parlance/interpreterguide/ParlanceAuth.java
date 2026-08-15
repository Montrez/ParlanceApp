package com.parlance.interpreterguide;

import android.app.Activity;
import android.os.Bundle;
import android.os.CancellationSignal;
import android.util.Log;

import androidx.annotation.NonNull;
import androidx.core.content.ContextCompat;
import androidx.credentials.Credential;
import androidx.credentials.CredentialManager;
import androidx.credentials.CredentialManagerCallback;
import androidx.credentials.CustomCredential;
import androidx.credentials.GetCredentialRequest;
import androidx.credentials.GetCredentialResponse;
import androidx.credentials.exceptions.GetCredentialCancellationException;
import androidx.credentials.exceptions.GetCredentialException;
import androidx.credentials.exceptions.NoCredentialException;

import com.google.android.libraries.identity.googleid.GetSignInWithGoogleOption;
import com.google.android.libraries.identity.googleid.GoogleIdTokenCredential;
import com.google.firebase.FirebaseApp;
import com.google.firebase.auth.AuthCredential;
import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.auth.FirebaseUser;
import com.google.firebase.auth.GoogleAuthProvider;
import com.google.firebase.auth.OAuthProvider;
import com.google.firebase.auth.UserInfo;
import com.google.firebase.functions.FirebaseFunctions;

import org.json.JSONException;
import org.json.JSONObject;

import java.util.Arrays;
import java.util.Collections;
import java.util.HashSet;
import java.util.Set;

/**
 * Android counterpart to {@code Parlance/AuthManager.swift}. Same operations,
 * same reported state shape, so the shared web layer treats both hosts alike.
 *
 * <p>Sign-in is native rather than a Firebase web popup because Google refuses
 * OAuth from embedded WebViews, which is what a Capacitor app is.
 */
public class ParlanceAuth {

    /** Result callback: {@code null} error means success. */
    public interface AuthCallback {
        void onResult(String error);
    }

    /** Matches the string journal.js checks to stay silent on user cancellation. */
    public static final String CANCELLED = "cancelled";

    private static final String TAG = "ParlanceAuth";
    private static final String GOOGLE_PROVIDER = "google.com";
    private static final String APPLE_PROVIDER = "apple.com";

    private final Activity activity;

    public ParlanceAuth(Activity activity) {
        this.activity = activity;
    }

    // MARK: - State

    /** Mirrors {@code AuthManager.authInjectionJSON()} on iOS. */
    public String authStateJson() {
        JSONObject state = new JSONObject();
        try {
            FirebaseUser user = currentUser();
            state.put("signedIn", user != null);
            state.put("email", user == null || user.getEmail() == null ? "" : user.getEmail());
            state.put("uid", user == null ? "" : user.getUid());
            state.put("displayName",
                    user == null || user.getDisplayName() == null ? "" : user.getDisplayName());
        } catch (JSONException e) {
            Log.e(TAG, "Failed to build auth state", e);
        }
        return state.toString();
    }

    private boolean isFirebaseReady() {
        return !FirebaseApp.getApps(activity).isEmpty();
    }

    private FirebaseUser currentUser() {
        if (!isFirebaseReady()) {
            return null;
        }
        return FirebaseAuth.getInstance().getCurrentUser();
    }

    private Set<String> providerIds(FirebaseUser user) {
        Set<String> ids = new HashSet<>();
        for (UserInfo info : user.getProviderData()) {
            ids.add(info.getProviderId());
        }
        return ids;
    }

    // MARK: - Sign in

    public void signInWithGoogle(AuthCallback callback) {
        if (!isFirebaseReady()) {
            callback.onResult("Firebase is not configured in this build.");
            return;
        }
        requestGoogleIdToken(new TokenCallback() {
            @Override
            public void onToken(String idToken) {
                AuthCredential credential = GoogleAuthProvider.getCredential(idToken, null);
                FirebaseAuth.getInstance()
                        .signInWithCredential(credential)
                        .addOnSuccessListener(result -> callback.onResult(null))
                        .addOnFailureListener(error -> callback.onResult(describe(error)));
            }

            @Override
            public void onError(String error) {
                callback.onResult(error);
            }
        });
    }

    public void signInWithApple(AuthCallback callback) {
        if (!isFirebaseReady()) {
            callback.onResult("Firebase is not configured in this build.");
            return;
        }
        FirebaseAuth auth = FirebaseAuth.getInstance();
        OAuthProvider provider = appleProvider();

        // A sign-in interrupted by process death resumes here rather than
        // starting a second web flow the user never asked for.
        if (auth.getPendingAuthResult() != null) {
            auth.getPendingAuthResult()
                    .addOnSuccessListener(result -> callback.onResult(null))
                    .addOnFailureListener(error -> callback.onResult(describe(error)));
            return;
        }

        auth.startActivityForSignInWithProvider(activity, provider)
                .addOnSuccessListener(result -> callback.onResult(null))
                .addOnFailureListener(error -> callback.onResult(describe(error)));
    }

    private OAuthProvider appleProvider() {
        OAuthProvider.Builder builder = OAuthProvider.newBuilder(APPLE_PROVIDER);
        builder.setScopes(Arrays.asList("email", "name"));
        return builder.build();
    }

    // MARK: - Sign out

    public void signOut() {
        if (!isFirebaseReady()) {
            return;
        }
        FirebaseAuth.getInstance().signOut();
    }

    // MARK: - Account deletion

    /**
     * Deletes the account: reauthenticate, wipe server records, then remove the
     * Firebase Auth user. Server data goes first because the callable needs a
     * live ID token, which deleting the user destroys.
     */
    public void deleteAccount(AuthCallback callback) {
        FirebaseUser user = currentUser();
        if (user == null) {
            callback.onResult("You are not signed in.");
            return;
        }

        Set<String> providers = providerIds(user);
        reauthenticate(user, providers, reauthError -> {
            if (reauthError != null) {
                callback.onResult(reauthError);
                return;
            }
            deleteServerData(serverError -> {
                if (serverError != null) {
                    callback.onResult(serverError);
                    return;
                }
                FirebaseUser fresh = currentUser();
                if (fresh == null) {
                    callback.onResult("You are not signed in.");
                    return;
                }
                fresh.delete()
                        .addOnSuccessListener(unused -> callback.onResult(null))
                        .addOnFailureListener(error -> callback.onResult(describe(error)));
            });
        });
    }

    private void reauthenticate(FirebaseUser user, Set<String> providers, AuthCallback callback) {
        if (providers.contains(GOOGLE_PROVIDER)) {
            requestGoogleIdToken(new TokenCallback() {
                @Override
                public void onToken(String idToken) {
                    AuthCredential credential = GoogleAuthProvider.getCredential(idToken, null);
                    user.reauthenticate(credential)
                            .addOnSuccessListener(unused -> callback.onResult(null))
                            .addOnFailureListener(error -> callback.onResult(describe(error)));
                }

                @Override
                public void onError(String error) {
                    callback.onResult(error);
                }
            });
            return;
        }

        if (providers.contains(APPLE_PROVIDER)) {
            user.startActivityForReauthenticateWithProvider(activity, appleProvider())
                    .addOnSuccessListener(result -> callback.onResult(null))
                    .addOnFailureListener(error -> callback.onResult(describe(error)));
            return;
        }

        callback.onResult(null);
    }

    /**
     * Wipes {@code users/{uid}} and its subcollections. Firestore rules block
     * client writes to those paths, so it runs through the same Admin SDK
     * callable the iOS app uses.
     */
    private void deleteServerData(AuthCallback callback) {
        FirebaseFunctions.getInstance()
                .getHttpsCallable("deleteAccountData")
                .call(Collections.emptyMap())
                .addOnSuccessListener(result -> callback.onResult(null))
                .addOnFailureListener(error -> {
                    Log.e(TAG, "deleteAccountData failed", error);
                    callback.onResult(
                            "Could not delete your Parlance data. Check your connection and try again.");
                });
    }

    // MARK: - Google credential plumbing

    private interface TokenCallback {
        void onToken(String idToken);

        void onError(String error);
    }

    /**
     * Asks Credential Manager for a Google ID token.
     *
     * <p>Uses the explicit "Sign in with Google" option rather than the bottom
     * sheet: the sheet suppresses itself after a couple of dismissals, which
     * would make a button the user just tapped appear to do nothing.
     */
    private void requestGoogleIdToken(TokenCallback callback) {
        String serverClientId = webClientId();
        if (serverClientId == null) {
            callback.onError("Google Sign-In is not configured in this build "
                    + "(missing google-services.json).");
            return;
        }

        GetSignInWithGoogleOption option =
                new GetSignInWithGoogleOption.Builder(serverClientId).build();
        GetCredentialRequest request =
                new GetCredentialRequest.Builder().addCredentialOption(option).build();

        CredentialManager.create(activity).getCredentialAsync(
                activity,
                request,
                new CancellationSignal(),
                ContextCompat.getMainExecutor(activity),
                new CredentialManagerCallback<GetCredentialResponse, GetCredentialException>() {
                    @Override
                    public void onResult(@NonNull GetCredentialResponse response) {
                        String idToken = extractGoogleIdToken(response);
                        if (idToken == null) {
                            callback.onError("Google Sign-In did not return an ID token.");
                            return;
                        }
                        callback.onToken(idToken);
                    }

                    @Override
                    public void onError(@NonNull GetCredentialException error) {
                        callback.onError(describeCredentialError(error));
                    }
                });
    }

    private String extractGoogleIdToken(GetCredentialResponse response) {
        Credential credential = response.getCredential();
        if (!(credential instanceof CustomCredential custom)) {
            return null;
        }
        if (!GoogleIdTokenCredential.TYPE_GOOGLE_ID_TOKEN_CREDENTIAL.equals(custom.getType())) {
            return null;
        }
        Bundle data = custom.getData();
        return GoogleIdTokenCredential.createFrom(data).getIdToken();
    }

    /**
     * Resolved by name instead of {@code R.string.default_web_client_id} so the
     * project still compiles without the gitignored google-services.json.
     */
    private String webClientId() {
        int resId = activity.getResources().getIdentifier(
                "default_web_client_id", "string", activity.getPackageName());
        if (resId == 0) {
            return null;
        }
        String value = activity.getString(resId);
        return value.isEmpty() ? null : value;
    }

    private static String describeCredentialError(GetCredentialException error) {
        if (error instanceof GetCredentialCancellationException) {
            return CANCELLED;
        }
        if (error instanceof NoCredentialException) {
            return "No Google account is available on this device. Add one in Android Settings, "
                    + "then try again.";
        }
        Log.e(TAG, "Credential Manager error", error);
        return describe(error);
    }

    private static String describe(Exception error) {
        String message = error.getLocalizedMessage();
        return message == null || message.isEmpty() ? error.toString() : message;
    }
}
