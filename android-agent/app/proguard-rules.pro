# ProGuard-regels voor EmuFlow Agent

# Bewaar Kotlin metadata (nodig voor Moshi reflection)
-keep class kotlin.Metadata { *; }

# Moshi — bewaar alle data classes
-keep class com.emuflow.agent.** { *; }
-keepclassmembers class com.emuflow.agent.** {
    @com.squareup.moshi.Json *;
}

# Retrofit — bewaar service-interfaces
-keep,allowobfuscation,allowshrinking interface retrofit2.Call
-keep,allowobfuscation,allowshrinking class retrofit2.Response
-keep,allowobfuscation,allowshrinking class kotlin.coroutines.Continuation

# OkHttp
-dontwarn okhttp3.**
-dontwarn okio.**
-keep class okhttp3.** { *; }

# Shizuku
-keep class rikka.shizuku.** { *; }

# Bewaar enums volledig
-keepclassmembers enum * {
    public static **[] values();
    public static ** valueOf(java.lang.String);
}
