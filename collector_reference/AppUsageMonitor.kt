package com.research.oculartracker.sensing

import android.app.AppOpsManager
import android.app.usage.UsageEvents
import android.app.usage.UsageStatsManager
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Process
import android.provider.Settings
import com.research.oculartracker.data.db.entity.PhoneEventEntity
import com.research.oculartracker.data.repository.MonitoringRepository
import com.research.oculartracker.util.PhoneEventType

/** Poll Android usage events and record foreground application changes. */
class AppUsageMonitor(private val context: Context) {

    private val usageStatsManager = context.getSystemService(Context.USAGE_STATS_SERVICE) as UsageStatsManager
    private var lastPolledAtMs: Long = System.currentTimeMillis() - 60_000

    fun hasUsagePermission(): Boolean {
        val appOps = context.getSystemService(Context.APP_OPS_SERVICE) as AppOpsManager
        val mode = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            appOps.unsafeCheckOpNoThrow(AppOpsManager.OPSTR_GET_USAGE_STATS, Process.myUid(), context.packageName)
        } else {
            @Suppress("DEPRECATION")
            appOps.checkOpNoThrow(AppOpsManager.OPSTR_GET_USAGE_STATS, Process.myUid(), context.packageName)
        }
        return mode == AppOpsManager.MODE_ALLOWED
    }

    fun openUsageAccessSettings() {
        val intent = Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS).apply {
            data = Uri.parse("package:${context.packageName}")
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        }
        context.startActivity(intent)
    }

    /** Record foreground/background events since the previous poll. */
    suspend fun pollAndLog(participantId: String) {
        if (!hasUsagePermission()) return
        val now = System.currentTimeMillis()
        val events = usageStatsManager.queryEvents(lastPolledAtMs, now)
        val repo = MonitoringRepository.get(context)
        val event = UsageEvents.Event()

        while (events.hasNextEvent()) {
            events.getNextEvent(event)
            val type = when (event.eventType) {
                UsageEvents.Event.MOVE_TO_FOREGROUND -> PhoneEventType.APP_FOREGROUND
                UsageEvents.Event.MOVE_TO_BACKGROUND -> PhoneEventType.APP_BACKGROUND
                else -> continue
            }
            // Exclude monitoring-app events.
            if (event.packageName == context.packageName) continue

            val category = AppCategoryMapper.categoryFor(context, event.packageName)
            repo.logPhoneEvent(
                PhoneEventEntity(
                    participantId = participantId,
                    timestampMs = event.timeStamp,
                    eventType = type.name,
                    packageName = event.packageName,
                    activityCategory = category,
                ),
            )
        }
        lastPolledAtMs = now
    }
}
