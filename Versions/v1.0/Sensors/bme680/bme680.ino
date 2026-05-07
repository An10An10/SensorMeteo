#include <Wire.h>
#include <Adafruit_Sensor.h>
#include "Adafruit_BME680.h"
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>

// --- НАСТРОЙКИ ---
const char* ssid = "ИМЯ_WIFI";
const char* password = "ПАРОЛЬ_WIFI";
const char* serverUrl = "http://leoplng.ru:25580/update"; 
const char* sensorId = "1"; 

Adafruit_BME680 bme; 

void setup() {
  Serial.begin(115200);
  if (!bme.begin(0x77)) { // Или 0x76, если не работает
    Serial.println("Ошибка: BME680 не найден!");
    while (1);
  }

  bme.setTemperatureOversampling(BME680_OS_8X);
  bme.setHumidityOversampling(BME680_OS_2X);
  bme.setPressureOversampling(BME680_OS_4X);
  bme.setIIRFilterSize(BME680_FILTER_SIZE_3);
  bme.setGasHeater(0, 0);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi OK!");
}

void loop() {
  if (!bme.performReading()) {
    Serial.println("Ошибка чтения датчика!");
    return;
  }

  float t = bme.temperature;
  float h = bme.humidity;
  // Давление из Паскалей в мм рт. ст.
  float p = (bme.pressure / 100.0F) * 0.750062;

  if (WiFi.status() == WL_CONNECTED) {
    WiFiClient client;
    HTTPClient http;
    
    String postData = String(t) + "," + String(h) + "," + String(p);

    http.begin(client, serverUrl);
    http.addHeader("id", sensorId);
    http.addHeader("Content-Type", "text/plain");

    int httpCode = http.POST(postData);
    
    Serial.printf("Отправлено: %s. Ответ: %d\n", postData.c_str(), httpCode);
    http.end();
  }

  delay(60000);
}
