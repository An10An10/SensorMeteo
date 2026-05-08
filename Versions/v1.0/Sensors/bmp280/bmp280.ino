#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <Wire.h>
#include <Adafruit_BMP280.h>

Adafruit_BMP280 bmp;

String WIFI_SSID = "WIFI_SSID";
String WIFI_PASS = "WIFI_PASS";
String ID = "1";

void setup() {
  Serial.begin(115200);
  if (!bmp.begin(0x76)) { Serial.println("BMP280 error"); } // или 0x77
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) delay(500);
}

void loop() {
  float t = bmp.readTemperature();
  float p = (bmp.readPressure() / 100.0F) * 0.750062;

  if (isnan(t)) t = -1.0;
  if (p <= 0) p = -1.0;

  if (WiFi.status() == WL_CONNECTED) {
    WiFiClient client;
    HTTPClient http;
    http.begin(client, "http://leoplng.ru:25580/update");
    http.addHeader("id", ID);
    String postData = String(t) + ",-1.0," + String(p);
    http.POST(postData);
    http.end();
  }
  delay(60000);
}
