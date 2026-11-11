package com.research.oculartracker.sensing

import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.os.BatteryManager
import android.provider.Settings
import com.research.oculartracker.data.db.entity.ContextSampleEntity
import com.research.oculartracker.data.repository.MonitoringRepository
import kotlin.math.sqrt

/** Sample device context using the latest available sensor readings. */
class ContextSensorManager(private val context: Context) : SensorEventListener {

    private val sensorManager = context.getSystemService(Context.SENSOR_SERVICE) as SensorManager
    private val lightSensor = sensorManager.getDefaultSensor(Sensor.TYPE_LIGHT)
    private val accelSensor = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)
    private val gyroSensor = sensorManager.getDefaultSensor(Sensor.TYPE_GYROSCOPE)

    @Volatile private var lastLux: Float? = null
    @Volatile private var lastAccelMagnitude: Float? = null
    @Volatile private var lastGyroMagnitude: Float? = null

    fun start() {
        lightSensor?.let { sensorManager.registerListener(this, it, SensorManager.SENSOR_DELAY_NORMAL) }
        accelSensor?.let { sensorManager.registerListener(this, it, SensorManager.SENSOR_DELAY_NORMAL) }
        gyroSensor?.let { sensorManager.registerListener(this, it, SensorManager.SENSOR_DELAY_NORMAL) }
    }

    fun stop() {
        sensorManager.unregisterListener(this)
    }

    override fun onSensorChanged(event: SensorEvent) {
        when (event.sensor.type) {
            Sensor.TYPE_LIGHT -> lastLux = event.values[0]
            Sensor.TYPE_ACCELEROMETER -> lastAccelMagnitude = magnitude(event.values)
            Sensor.TYPE_GYROSCOPE -> lastGyroMagnitude = magnitude(event.values)
        }
    }

    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}

    private fun magnitude(v: FloatArray): Float =
        sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])

    private fun currentBatteryLevel(): Float? {
        val filter = IntentFilter(Intent.ACTION_BATTERY_CHANGED)
        val batteryStatus = context.registerReceiver(null, filter) ?: return null
        val level = batteryStatus.getIntExtra(BatteryManager.EXTRA_LEVEL, -1)
        val scale = batteryStatus.getIntExtra(BatteryManager.EXTRA_SCALE, -1)
        if (level < 0 || scale <= 0) return null
        return level / scale.toFloat()
    }

    private fun currentScreenBrightness(): Int? = try {
        Settings.System.getInt(context.contentResolver, Settings.System.SCREEN_BRIGHTNESS)
    } catch (e: Settings.SettingNotFoundException) {
        null
    }

    suspend fun sampleNow(participantId: String) {
        val sample = ContextSampleEntity(
            participantId = participantId,
            timestampMs = System.currentTimeMillis(),
            ambientLightLux = lastLux,
            screenBrightness = currentScreenBrightness(),
            deviceOrientation = null,
            accelerometerMagnitude = lastAccelMagnitude,
            gyroscopeMagnitude = lastGyroMagnitude,
            batteryLevel = currentBatteryLevel(),
            deviceTemperatureC = null,
        )
        MonitoringRepository.get(context).logContextSample(sample)
    }
}
