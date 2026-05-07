#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>

const char* ssid = "WIFI_SSID";
const char* password = "WIFI_PASS";
const char* serverUrl = "http://leoplng.ru:25580/update";
const char* sensorId = "1";

Adafruit_BME280 bme;

void setup() {
  Serial.begin(115200);
  // Инициализация BME280
  if (!bme.begin(0x76)) {
    Serial.println("BME280 не найден!");
    while (1);
  }
  
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) delay(500);
}

void loop() {
  float t = bme.readTemperature();
  float h = bme.readHumidity();
  float p = (bme.readPressure() / 100.0F) * 0.750062; //Переводим давление из гПа в мм рт. ст.

  if (WiFi.status() == WL_CONNECTED) {
    WiFiClient client;
    HTTPClient http;
    http.begin(client, serverUrl);
    http.addHeader("id", sensorId);
    http.addHeader("Content-Type", "text/plain");

    String postData = String(t) + "," + String(h) + "," + String(p);
    int httpCode = http.POST(postData);
    http.end();
  }
  delay(60000);
}
