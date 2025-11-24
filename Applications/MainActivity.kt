package com.example.msdksample
 
import androidx.appcompat.app.AppCompatActivity
import android.os.Bundle
 
class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
    }

    fun rotate360() {

    val aircraft = DJISDKManager.getInstance().product as? Aircraft ?: return
    val fc = aircraft.flightController ?: return

    // Vitesse de rotation en °/s (10 = lent et stable)
    val yawSpeed = 30f  
    val duration = (360 / yawSpeed) * 1000  // durée en ms

    val timer = Timer()
    timer.scheduleAtFixedRate(object : TimerTask() {
        override fun run() {
            val controlData = FlightControlData(
                0f,  // pitch
                0f,  // roll
                0f,  // throttle
                yawSpeed  // yaw rotation
            )
            fc.sendVirtualStickFlightControlData(controlData) { }
        }
    }, 0, 100)

    // arrêter après un tour
    Handler(Looper.getMainLooper()).postDelayed({
        timer.cancel()
    }, duration.toLong())
    }



    fun getCameraOrientation() {

    val aircraft = DJISDKManager.getInstance().product as? Aircraft
    val gimbal = aircraft?.gimbal ?: return

    gimbal.getState { gimbalState, error ->
        if (error == null && gimbalState != null) {

            val pitch = gimbalState.attitudeInDegrees.pitch
            val roll  = gimbalState.attitudeInDegrees.roll
            val yaw   = gimbalState.attitudeInDegrees.yaw

            runOnUiThread {
                Toast.makeText(
                    this,
                    "Camera: Pitch = $pitch°, Roll = $roll°, Yaw = $yaw°",
                    Toast.LENGTH_LONG
                ).show()
            }

        } else {
            Log.e("DJI", "Erreur gimbal: $error")
        }
    }
}
}
