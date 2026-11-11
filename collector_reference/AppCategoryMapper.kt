package com.research.oculartracker.sensing

import android.content.Context
import android.content.pm.ApplicationInfo
import android.content.pm.PackageManager
import android.os.Build

/** Assign a category using the known-package mapping, Android category, or OTHER. */
object AppCategoryMapper {

    // Known application categories.
    private val KNOWN_PACKAGES: Map<String, String> = mapOf(
        // MESSAGING
        "com.whatsapp" to "MESSAGING",
        "com.google.android.apps.messaging" to "MESSAGING",
        "com.facebook.orca" to "MESSAGING",
        "org.telegram.messenger" to "MESSAGING",
        "com.discord" to "MESSAGING",
        "com.microsoft.teams" to "MESSAGING",
        "com.slack" to "MESSAGING",
        // SOCIAL_FEED
        "com.instagram.android" to "SOCIAL_FEED",
        "com.facebook.katana" to "SOCIAL_FEED",
        "com.twitter.android" to "SOCIAL_FEED",
        "com.zhiliaoapp.musically" to "SOCIAL_FEED", // TikTok
        "com.reddit.frontpage" to "SOCIAL_FEED",
        "com.linkedin.android" to "SOCIAL_FEED",
        "com.snapchat.android" to "SOCIAL_FEED",
        // VIDEO
        "com.google.android.youtube" to "VIDEO",
        "com.netflix.mediaclient" to "VIDEO",
        "com.amazon.avod.thirdpartyclient" to "VIDEO",
        "com.disney.disneyplus" to "VIDEO",
        "tv.twitch.android.app" to "VIDEO",
        // READING_NEWS
        "flipboard.app" to "READING_NEWS",
        "com.google.android.apps.magazines" to "READING_NEWS",
        "com.medium.reader" to "READING_NEWS",
        // BROWSER_SEARCH
        "com.android.chrome" to "BROWSER_SEARCH",
        "org.mozilla.firefox" to "BROWSER_SEARCH",
        "com.microsoft.emmx" to "BROWSER_SEARCH",
        "com.google.android.googlequicksearchbox" to "BROWSER_SEARCH",
        "com.duckduckgo.mobile.android" to "BROWSER_SEARCH",
        // GAMING (a few common examples; games are numerous, ApplicationInfo.category fallback matters most here)
        "com.king.candycrushsaga" to "GAMING",
        "com.supercell.clashofclans" to "GAMING",
        "com.roblox.client" to "GAMING",
        "com.mojang.minecraftpe" to "GAMING",
        // PRODUCTIVITY
        "com.google.android.gm" to "PRODUCTIVITY",
        "com.google.android.apps.docs" to "PRODUCTIVITY",
        "com.microsoft.office.outlook" to "PRODUCTIVITY",
        "com.microsoft.office.word" to "PRODUCTIVITY",
        "notion.id" to "PRODUCTIVITY",
        "com.todoist" to "PRODUCTIVITY",
        "us.zoom.videomeetings" to "PRODUCTIVITY",
        // SHOPPING
        "com.amazon.mShop.android.shopping" to "SHOPPING",
        "com.ebay.mobile" to "SHOPPING",
        "com.shopify.mobile" to "SHOPPING",
        // MAP_NAVIGATION
        "com.google.android.apps.maps" to "MAP_NAVIGATION",
        "com.waze" to "MAP_NAVIGATION",
        "com.ubercab" to "MAP_NAVIGATION",
        "com.lyft.android" to "MAP_NAVIGATION",
        // MUSIC_AUDIO
        "com.spotify.music" to "MUSIC_AUDIO",
        "com.google.android.apps.youtube.music" to "MUSIC_AUDIO",
        "com.apple.android.music" to "MUSIC_AUDIO",
        "com.audible.application" to "MUSIC_AUDIO",
        "com.spotify.podcasts" to "MUSIC_AUDIO",
        // CAMERA_MEDIA
        "com.google.android.GoogleCamera" to "CAMERA_MEDIA",
        "com.google.android.apps.photos" to "CAMERA_MEDIA",
        "com.instagram.boomerang" to "CAMERA_MEDIA",
    )

    fun categoryFor(context: Context, packageName: String): String {
        KNOWN_PACKAGES[packageName]?.let { return it }

        return try {
            val info: ApplicationInfo = context.packageManager.getApplicationInfo(packageName, 0)
            fromAndroidCategory(info)
        } catch (e: PackageManager.NameNotFoundException) {
            "OTHER"
        }
    }

    private fun fromAndroidCategory(info: ApplicationInfo): String {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return "OTHER"
        // Applications without a mapped category use OTHER.
        return when (info.category) {
            ApplicationInfo.CATEGORY_GAME -> "GAMING"
            ApplicationInfo.CATEGORY_SOCIAL -> "SOCIAL_FEED"
            ApplicationInfo.CATEGORY_VIDEO -> "VIDEO"
            ApplicationInfo.CATEGORY_AUDIO -> "MUSIC_AUDIO"
            ApplicationInfo.CATEGORY_NEWS -> "READING_NEWS"
            ApplicationInfo.CATEGORY_MAPS -> "MAP_NAVIGATION"
            ApplicationInfo.CATEGORY_PRODUCTIVITY -> "PRODUCTIVITY"
            ApplicationInfo.CATEGORY_IMAGE -> "CAMERA_MEDIA"
            else -> "OTHER"
        }
    }
}
