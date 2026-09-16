package com.streamnest.android;

import android.app.Activity;
import android.content.ContentValues;
import android.os.Bundle;
import android.os.Environment;
import android.media.MediaExtractor;
import android.media.MediaFormat;
import android.media.MediaMuxer;
import android.media.MediaCodec;
import android.provider.MediaStore;
import android.view.Gravity;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.Spinner;
import android.widget.TextView;

import com.chaquo.python.PyObject;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedInputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.FileInputStream;
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
                File work = new File(getCacheDir(), "streamnest");
                if (!work.exists() && !work.mkdirs()) throw new IllegalStateException("Cannot create temporary directory.");
                File output = new File(work, title + ".mp4");
                File video = null;
                File audio = null;
                for (int i = 0; i < streams.length(); i++) {
                    JSONObject stream = streams.getJSONObject(i);
                    File target = new File(work, stream.getString("kind") + ".part");
                    downloadFile(stream.getString("url"), target);
                    if ("audio".equals(stream.getString("kind"))) audio = target; else video = target;
                }
                runOnUiThread(() -> status.setText("Merging media…"));
                muxMedia(video, audio, output);
                String savedName = publishDownload(output, title + ".mp4");
                runOnUiThread(() -> {
                    status.setText("Saved to Downloads/" + savedName);
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

    private String publishDownload(File source, String name) throws Exception {
        if (android.os.Build.VERSION.SDK_INT >= 29) {
            ContentValues values = new ContentValues();
            values.put(MediaStore.Downloads.DISPLAY_NAME, name);
            values.put(MediaStore.Downloads.MIME_TYPE, "video/mp4");
            values.put(MediaStore.Downloads.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS);
            android.net.Uri uri = getContentResolver().insert(
                    MediaStore.Downloads.EXTERNAL_CONTENT_URI, values);
            if (uri == null) throw new IllegalStateException("Android could not create the Downloads file.");
            try (FileInputStream input = new FileInputStream(source);
                 java.io.OutputStream output = getContentResolver().openOutputStream(uri)) {
                if (output == null) throw new IllegalStateException("Android could not open the Downloads file.");
                byte[] buffer = new byte[1024 * 64];
                int count;
                while ((count = input.read(buffer)) != -1) output.write(buffer, 0, count);
            }
            return name;
        }
        File downloads = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS);
        File destination = new File(downloads, name);
        try (FileInputStream input = new FileInputStream(source);
             FileOutputStream output = new FileOutputStream(destination)) {
            byte[] buffer = new byte[1024 * 64];
            int count;
            while ((count = input.read(buffer)) != -1) output.write(buffer, 0, count);
        }
        return destination.getName();
    }

    private void muxMedia(File video, File audio, File output) throws Exception {
        MediaMuxer muxer = new MediaMuxer(output.getAbsolutePath(), MediaMuxer.OutputFormat.MUXER_OUTPUT_MPEG_4);
        try {
            int videoTrack = addTrack(muxer, video);
            int audioTrack = audio == null ? -1 : addTrack(muxer, audio);
            muxer.start();
            writeTrack(muxer, video, videoTrack);
            if (audio != null) writeTrack(muxer, audio, audioTrack);
        } finally {
            muxer.stop();
            muxer.release();
        }
    }

    private int addTrack(MediaMuxer muxer, File source) throws Exception {
        MediaExtractor extractor = new MediaExtractor();
        extractor.setDataSource(source.getAbsolutePath());
        for (int i = 0; i < extractor.getTrackCount(); i++) {
            MediaFormat format = extractor.getTrackFormat(i);
            String mime = format.getString(MediaFormat.KEY_MIME);
            if (mime != null && (mime.startsWith("video/") || mime.startsWith("audio/"))) {
                extractor.release();
                MediaExtractor probe = new MediaExtractor();
                probe.setDataSource(source.getAbsolutePath());
                probe.selectTrack(i);
                MediaFormat selected = probe.getTrackFormat(i);
                probe.release();
                return muxer.addTrack(selected);
            }
        }
        extractor.release();
        throw new IllegalStateException("Downloaded media has no compatible MP4 track.");
    }

    private void writeTrack(MediaMuxer muxer, File source, int outputTrack) throws Exception {
        MediaExtractor extractor = new MediaExtractor();
        extractor.setDataSource(source.getAbsolutePath());
        int selected = -1;
        for (int i = 0; i < extractor.getTrackCount(); i++) {
            String mime = extractor.getTrackFormat(i).getString(MediaFormat.KEY_MIME);
            if (mime != null && (mime.startsWith("video/") || mime.startsWith("audio/"))) {
                selected = i;
                break;
            }
        }
        if (selected < 0) throw new IllegalStateException("No compatible media track.");
        extractor.selectTrack(selected);
        java.nio.ByteBuffer buffer = java.nio.ByteBuffer.allocate(1024 * 1024);
        MediaCodec.BufferInfo info = new MediaCodec.BufferInfo();
        while (true) {
            int size = extractor.readSampleData(buffer, 0);
            if (size < 0) break;
            info.offset = 0;
            info.size = size;
            info.presentationTimeUs = extractor.getSampleTime();
            info.flags = extractor.getSampleFlags();
            muxer.writeSampleData(outputTrack, buffer, info);
            extractor.advance();
        }
        extractor.release();
    }

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
