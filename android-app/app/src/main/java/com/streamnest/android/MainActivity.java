package com.streamnest.android;

import android.app.Activity;
import android.app.DownloadManager;
import android.content.Context;
import android.net.Uri;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.webkit.DownloadListener;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import java.util.Locale;

public final class MainActivity extends Activity {
    private static final String PREFS = "streamnest";
    private static final String SERVER_URL = "server_url";
    private WebView webView;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        String savedUrl = getPreferences(Context.MODE_PRIVATE).getString(SERVER_URL, "");
        if (savedUrl.isEmpty()) {
            showSetup();
        } else {
            showBrowser(savedUrl);
        }
    }

    private void showSetup() {
        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        page.setPadding(48, 72, 48, 48);
        page.setGravity(Gravity.CENTER_VERTICAL);
        page.setBackgroundColor(0xFF0B1020);

        TextView title = text(getString(com.streamnest.android.R.string.server_title), 28, 0xFFFFFFFF);
        page.addView(title, matchWrap(0, 18));
        TextView description = text(getString(com.streamnest.android.R.string.server_description), 16, 0xFFB7C1D9);
        page.addView(description, matchWrap(0, 28));

        EditText input = new EditText(this);
        input.setHint(getString(com.streamnest.android.R.string.companion_url_hint));
        input.setSingleLine(true);
        input.setTextColor(0xFFFFFFFF);
        input.setHintTextColor(0xFF7F8BA8);
        input.setPadding(20, 12, 20, 12);
        page.addView(input, matchWrap(0, 14));

        Button connect = new Button(this);
        connect.setText(getString(com.streamnest.android.R.string.save_and_connect));
        connect.setOnClickListener(view -> {
            String url = normalize(input.getText().toString());
            if (url == null) {
                input.setError(getString(com.streamnest.android.R.string.invalid_url));
                return;
            }
            getPreferences(Context.MODE_PRIVATE).edit().putString(SERVER_URL, url).apply();
            showBrowser(url);
        });
        page.addView(connect, matchWrap(0, 24));

        TextView help = text(getString(com.streamnest.android.R.string.connection_help), 14, 0xFF9AA8C5);
        page.addView(help, matchWrap(0, 0));
        setContentView(page);
    }

    private void showBrowser(String url) {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);

        Button change = new Button(this);
        change.setText(getString(com.streamnest.android.R.string.change_server));
        change.setOnClickListener(view -> showSetup());
        root.addView(change, new LinearLayout.LayoutParams(-1, 52));

        webView = new WebView(this);
        webView.getSettings().setJavaScriptEnabled(true);
        webView.getSettings().setDomStorageEnabled(true);
        webView.setWebChromeClient(new WebChromeClient());
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                return false;
            }
        });
        webView.setDownloadListener((DownloadListener) (downloadUrl, userAgent, contentDisposition, mimeType, contentLength) -> {
            DownloadManager.Request request = new DownloadManager.Request(Uri.parse(downloadUrl));
            request.setTitle("StreamNest download");
            request.setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED);
            request.setMimeType(mimeType);
            ((DownloadManager) getSystemService(DOWNLOAD_SERVICE)).enqueue(request);
            Toast.makeText(this, "Download started", Toast.LENGTH_SHORT).show();
        });
        root.addView(webView, new LinearLayout.LayoutParams(-1, 0, 1));
        setContentView(root);
        webView.loadUrl(url);
    }

    private TextView text(String value, int size, int color) {
        TextView view = new TextView(this);
        view.setText(value);
        view.setTextSize(size);
        view.setTextColor(color);
        return view;
    }

    private LinearLayout.LayoutParams matchWrap(int width, int bottomMargin) {
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                width == 0 ? -1 : width, -2);
        params.bottomMargin = bottomMargin;
        return params;
    }

    private String normalize(String raw) {
        String url = raw.trim();
        String lower = url.toLowerCase(Locale.ROOT);
        if (!(lower.startsWith("http://") || lower.startsWith("https://"))) {
            return null;
        }
        if (url.contains(" ") || url.length() > 2048) {
            return null;
        }
        return url.replaceAll("/+$", "");
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }
}
