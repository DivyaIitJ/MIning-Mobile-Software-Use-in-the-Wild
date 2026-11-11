package com.research.oculartracker.sensing

import android.app.Service
import android.content.Intent
import android.os.Build
import android.os.IBinder
import androidx.core.app.ServiceCompat
import androidx.work.ExistingWorkPolicy
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import com.research.oculartracker.notifications.NotificationHelper
import com.research.oculartracker.util.Constants
import com.research.oculartracker.util.Prefs
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

/** Foreground service for application polling and periodic context sampling. */
class MonitoringForegroundService : Service() {

    private val scope = CoroutineScope(Dispatchers.IO + Job())
    private lateinit var appUsageMonitor: AppUsageMonitor
    private lateinit var contextSensorManager: ContextSensorManager
    private var pollingJob: Job? = null

    override fun onCreate() {
        super.onCreate()
        appUsageMonitor = AppUsageMonitor(this)
        contextSensorManager = ContextSensorManager(this)
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        ServiceCompat.startForeground(
            this,
            Constants.NOTIF_ID_MONITORING,
            NotificationHelper.monitoringNotification(this),
            android.content.pm.ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC,
        )
        contextSensorManager.start()
        startPollingLoop()
        return START_STICKY
    }

    private fun startPollingLoop() {
        if (pollingJob?.isActive == true) return
        pollingJob = scope.launch {
            while (true) {
                val participantId = com.research.oculartracker.data.repository.MonitoringRepository
                    .get(this@MonitoringForegroundService).getParticipant()?.participantId
                if (participantId != null) {
                    runCatching { appUsageMonitor.pollAndLog(participantId) }
                    runCatching { contextSensorManager.sampleNow(participantId) }
                }
                delay(Constants.CONTEXT_SAMPLE_INTERVAL_MS)
            }
        }
    }

    override fun onTimeout(startId: Int, fgsType: Int) {
        // Request service recovery after Android's foreground-service timeout.
        super.onTimeout(startId, fgsType)
        WorkManager.getInstance(this).enqueueUniqueWork(
            MonitoringWatchdogWorker.WORK_NAME,
            ExistingWorkPolicy.REPLACE,
            OneTimeWorkRequestBuilder<MonitoringWatchdogWorker>().build(),
        )
        stopSelf(startId)
    }

    override fun onDestroy() {
        pollingJob?.cancel()
        contextSensorManager.stop()
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null
}
