plugins {
    id("com.android.application")
    id("com.chaquo.python")
}

android {
    namespace = "com.streamnest.android"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.streamnest.android"
        minSdk = 29
        targetSdk = 35
        versionCode = 1
        versionName = "1.0.0"
        ndk {
            abiFilters += listOf("arm64-v8a", "armeabi-v7a", "x86_64")
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro",
            )
        }

        chaquopy {
            defaultConfig {
                version = "3.11"
                pip {
                    install("yt-dlp")
                }
            }
        }

    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}
