package com.streamnest.android;

import android.app.Activity;
import android.os.Bundle;
import android.os.Environment;
import android.view.Gravity;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.Spinner;
import android.widget.TextView;

import com.arthenica.ffmpegkit.FFmpegKit;
import com.arthenica.ffmpegkit.ReturnCode;
import com.chaquo.python.PyObject;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedInputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public final class MainActivity extends Activity {
    private final ExecutorService executor = Executors.newSingleThreadExecutor();
    private EditText urlInput;
    private Spinner quality;
    private TextView status;
    private Button download;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        if (!Python.isStarted()) Python.start(new AndroidPlatform(this));
        showScreen();
    }

    private void showScreen() {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(36, 56, 36, 24);
        root.setBackgroundColor(0xFF0B1020);

        TextView title = text("StreamNest", 32, 0xFFFFFFFF);
        root.addView(title, params(0, 12));
        TextView subtitle = text("Download public YouTube videos directly on Android.", 16, 0xFFB7C1D9);
        root.addView(subtitle, params(0, 28));

        urlInput = new EditText(this);
        urlInput.setHint("Paste a YouTube URL");
        urlInput.setSingleLine(true);
        urlInput.setTextColor(0xFFFFFFFF);
        urlInput.setHintTextColor(0xFF7F8BA8);
        root.addView(urlInput, params(0, 14));

        quality = new Spinner(this);
        quality.setAdapter(new ArrayAdapter<>(this, android.R.layout.simple_spinner_dropdown_item,
                new String[]{"Best available", "Up to 1080p", "Up to 720p", "Up to 480p"}));
        root.addView(quality, params(0, 16));

        download = new Button(this);
        download.setText("Download");
        download.setOnClickListener(view -> startDownload());
        root.addView(download, params(0, 18));

        status = text("Files are saved to the Android Downloads folder.", 14, 0xFF9AA8C5);
        root.addView(status, params(0, 0));
        setContentView(root);
    }

    private void startDownload() {
        String url = urlInput.getText().toString().trim();
        if (!url.startsWith("https://www.youtube.com/") && !url.startsWith("https://youtu.be/")) {
            urlInput.setError("Enter a public YouTube URL.");
            return;
        }
        download.setEnabled(false);
        status.setText("Finding available formats…");
        String selected = quality.getSelectedItem().toString();
        String qualityKey = selected.startsWith("Up to 1080") ? "1080p"
                : selected.startsWith("Up to 720") ? "720p"
                : selected.startsWith("Up to 480") ? "480p" : "best";
        executor.execute(() -> {
            try {
                PyObject result = Python.getInstance().getModule("downloader")
                        .callAttr("resolve", url, qualityKey);
                JSONObject media = new JSONObject(result.toString());
                JSONArray streams = media.getJSONArray("streams");
                String title = safeName(media.getString("title"));
                File dir = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS);
                File work = new File(getCacheDir(), "streamnest");
                if (!work.exists() && !work.mkdirs()) throw new IllegalStateException("Cannot create temporary directory.");
                File output = new File(dir, title + ".mp4");
                File video = null;
                File audio = null;
                for (int i = 0; i < streams.length(); i++) {
                    JSONObject stream = streams.getJSONObject(i);
                    File target = new File(work, stream.getString("kind") + ".part");
                    downloadFile(stream.getString("url"), target);
                    if ("audio".equals(stream.getString("kind"))) audio = target; else video = target;
                }
                final File videoFile = video;
                final File audioFile = audio;
                runOnUiThread(() -> status.setText("Merging media…"));
                String command = audioFile == null
                        ? "-y -i " + quote(videoFile.getAbsolutePath()) + " -c copy " + quote(output.getAbsolutePath())
                        : "-y -i " + quote(videoFile.getAbsolutePath()) + " -i " + quote(audioFile.getAbsolutePath())
                        + " -c copy -movflags +faststart " + quote(output.getAbsolutePath());
                if (!ReturnCode.isSuccess(FFmpegKit.execute(command).getReturnCode())) {
                    throw new IllegalStateException("FFmpeg could not merge this media.");
                }
                runOnUiThread(() -> {
                    status.setText("Saved to Downloads/" + output.getName());
                    download.setEnabled(true);
                });
            } catch (Exception error) {
                runOnUiThread(() -> {
                    status.setText(error.getMessage() == null ? "Download failed." : error.getMessage());
                    download.setEnabled(true);
                });
            }
        });
    }

    private void downloadFile(String source, File target) throws Exception {
        HttpURLConnection connection = (HttpURLConnection) new URL(source).openConnection();
        connection.setRequestProperty("User-Agent", "StreamNest Android");
        connection.setConnectTimeout(30000);
        connection.setReadTimeout(30000);
        try (InputStream input = new BufferedInputStream(connection.getInputStream());
             FileOutputStream output = new FileOutputStream(target)) {
            byte[] buffer = new byte[1024 * 64];
            int count;
            while ((count = input.read(buffer)) != -1) output.write(buffer, 0, count);
        } finally {
            connection.disconnect();
        }
    }

    private String quote(String path) { return "'" + path.replace("'", "'\\''") + "'"; }
    private String safeName(String value) {
        String clean = value.replaceAll("[\\\\/:*?\"<>|]", "_").trim();
        return clean.isEmpty() ? "streamnest-download" : clean.substring(0, Math.min(clean.length(), 120));
    }
    private TextView text(String value, int size, int color) {
        TextView view = new TextView(this); view.setText(value); view.setTextSize(size); view.setTextColor(color); return view;
    }
    private LinearLayout.LayoutParams params(int width, int bottom) {
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(width == 0 ? -1 : width, -2);
        p.bottomMargin = bottom; return p;
    }
    @Override protected void onDestroy() { executor.shutdownNow(); super.onDestroy(); }
}
