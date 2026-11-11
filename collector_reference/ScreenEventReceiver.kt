package com.research.oculartracker.sensing

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import com.research.oculartracker.data.db.entity.PhoneEventEntity
import com.research.oculartracker.data.repository.MonitoringRepository
import com.research.oculartracker.util.PhoneEventType
import com.research.oculartracker.util.Prefs
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

/** Record screen and unlock events used in session analysis. */
class ScreenEventReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (!Prefs.isMonitoringEnabled(context)) return

        val eventType = when (intent.action) {
            Intent.ACTION_SCREEN_ON -> PhoneEventType.SCREEN_ON
            Intent.ACTION_SCREEN_OFF -> PhoneEventType.SCREEN_OFF
            Intent.ACTION_USER_PRESENT -> PhoneEventType.USER_PRESENT
            else -> return
        }

        val pendingResult = goAsync()
        CoroutineScope(Dispatchers.IO).launch {
            try {
                val participantId = MonitoringRepository.get(context).getParticipant()?.participantId
                if (participantId != null) {
                    MonitoringRepository.get(context).logPhoneEvent(
                        PhoneEventEntity(
                            participantId = participantId,
                            timestampMs = System.currentTimeMillis(),
                            eventType = eventType.name,
                            packageName = null,
                            activityCategory = null,
                        ),
                    )
                }
            } finally {
                pendingResult.finish()
            }
        }
    }
}
