package com.streamnest.android;

import android.app.Activity;
import android.content.ContentValues;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.os.Environment;
import android.media.MediaExtractor;
import android.media.MediaFormat;
import android.media.MediaMuxer;
import android.media.MediaCodec;
import android.provider.MediaStore;
import android.view.Gravity;
import android.view.View;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.ScrollView;
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
    private ProgressBar progress;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        if (!Python.isStarted()) Python.start(new AndroidPlatform(this));
        showScreen();
    }

    private void showScreen() {
        ScrollView scroll = new ScrollView(this);
        scroll.setBackgroundColor(0xFF0B1020);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(24, 28, 24, 32);
        scroll.addView(root);

        LinearLayout appHeader = new LinearLayout(this);
        appHeader.setGravity(Gravity.CENTER_VERTICAL);
        TextView logo = text("S", 30, Color.WHITE);
        logo.setGravity(Gravity.CENTER);
        logo.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        logo.setBackground(round(0xFF7C6CFF, 20));
        appHeader.addView(logo, fixed(64, 64, 16));
        LinearLayout appCopy = column();
        TextView title = text("StreamNest", 24, Color.WHITE);
        title.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        appCopy.addView(title);
        appCopy.addView(text("Public media downloader", 14, 0xFF9AA8C5));
        appHeader.addView(appCopy, params(0, 0));
        root.addView(appHeader, params(0, 28));

        TextView heading = text("Download videos\nwithout the clutter.", 30, Color.WHITE);
        heading.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        root.addView(heading, params(0, 10));
        root.addView(text("Paste a public YouTube link and save a clean MP4 to your Downloads folder.", 15, 0xFFB7C1D9), params(0, 22));

        LinearLayout linkCard = card();
        TextView linkLabel = text("VIDEO LINK", 12, 0xFF9AA8C5);
        linkLabel.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        linkCard.addView(linkLabel, params(0, 4));
        urlInput = new EditText(this);
        urlInput.setHint("https://youtube.com/watch?v=…");
        urlInput.setSingleLine(true);
        urlInput.setTextColor(Color.WHITE);
        urlInput.setHintTextColor(0xFF6F7D9D);
        urlInput.setTextSize(16);
        urlInput.setBackgroundColor(Color.TRANSPARENT);
        urlInput.setPadding(0, 4, 0, 0);
        linkCard.addView(urlInput, params(0, 0));
        root.addView(linkCard, params(0, 14));

        LinearLayout qualityCard = card();
        TextView qualityLabel = text("DOWNLOAD QUALITY", 12, 0xFF9AA8C5);
        qualityLabel.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        qualityCard.addView(qualityLabel, params(0, 2));
        quality = new Spinner(this);
        quality.setAdapter(new ArrayAdapter<>(this, android.R.layout.simple_spinner_dropdown_item,
                new String[]{"Best available", "Up to 1080p", "Up to 720p", "Up to 480p"}));
        qualityCard.addView(quality, params(0, 0));
        root.addView(qualityCard, params(0, 18));

        download = new Button(this);
        download.setText("Download video");
        download.setTextColor(Color.WHITE);
        download.setTextSize(16);
        download.setAllCaps(false);
        download.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        download.setBackground(round(0xFF7C6CFF, 18));
        download.setOnClickListener(view -> startDownload());
        root.addView(download, params(0, 16));

        progress = new ProgressBar(this);
        progress.setIndeterminate(true);
        progress.setVisibility(View.GONE);
        root.addView(progress, centered(0, 12));

        status = text("Ready to download · Files are saved in Downloads", 14, 0xFF9AA8C5);
        status.setGravity(Gravity.CENTER);
        root.addView(status, params(0, 0));
        setContentView(scroll);
    }

    private void startDownload() {
        String url = urlInput.getText().toString().trim();
        if (!url.startsWith("https://www.youtube.com/") && !url.startsWith("https://youtu.be/")) {
            urlInput.setError("Enter a public YouTube URL.");
            return;
        }
        download.setEnabled(false);
        progress.setVisibility(View.VISIBLE);
        download.setText("Preparing download…");
        status.setText("Connecting to YouTube…");
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
                runOnUiThread(() -> status.setText("Found media. Downloading…"));
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
                    progress.setVisibility(View.GONE);
                    download.setText("Download another video");
                    download.setEnabled(true);
                });
            } catch (Exception error) {
                runOnUiThread(() -> {
                    String message = error.getMessage() == null ? "Download failed." : error.getMessage();
                    status.setText(message.replace("java.lang.Exception:", "").trim());
                    progress.setVisibility(View.GONE);
                    download.setText("Try again");
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
    private LinearLayout column() {
        LinearLayout view = new LinearLayout(this);
        view.setOrientation(LinearLayout.VERTICAL);
        view.setPadding(16, 0, 0, 0);
        return view;
    }
    private LinearLayout card() {
        LinearLayout view = column();
        view.setPadding(18, 14, 18, 12);
        view.setBackground(round(0xFF151F36, 18));
        return view;
    }
    private GradientDrawable round(int color, int radius) {
        GradientDrawable drawable = new GradientDrawable();
        drawable.setColor(color);
        drawable.setCornerRadius(radius);
        return drawable;
    }
    private TextView text(String value, int size, int color) {
        TextView view = new TextView(this); view.setText(value); view.setTextSize(size); view.setTextColor(color); return view;
    }
    private LinearLayout.LayoutParams params(int width, int bottom) {
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(width == 0 ? -1 : width, -2);
        p.bottomMargin = bottom; return p;
    }
    private LinearLayout.LayoutParams fixed(int width, int height, int right) {
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(width, height);
        p.rightMargin = right;
        return p;
    }
    private LinearLayout.LayoutParams centered(int width, int bottom) {
        LinearLayout.LayoutParams p = params(width, bottom);
        p.gravity = Gravity.CENTER_HORIZONTAL;
        return p;
    }
    @Override protected void onDestroy() { executor.shutdownNow(); super.onDestroy(); }
}
