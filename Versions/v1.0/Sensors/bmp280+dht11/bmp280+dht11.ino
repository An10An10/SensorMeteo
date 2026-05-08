#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <Wire.h>
#include <Adafruit_BMP280.h>
#include <DHT.h>

Adafruit_BMP280 bmp; 

WIFI_SSID = "WIFI_SSID"
WIFI_PASS = "IFI_PASS"
ID = "1"

DHT dht(2, DHT11);
void setup() {
  Serial.begin(115200);
  bmp.begin(0x76);
  dht.begin();
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) delay(500);
}

void loop() {
  float t = bmp.readTemperature(); 
  float p = (bmp.readPressure() / 100.0F) * 0.750062;
  float h = dht.readHumidity();

  if (isnan(t)) t = dht.readTemperature();
  if (isnan(t)) t = -1.0;
  if (isnan(h)) h = -1.0;
  if (p <= 0) p = -1.0;

  if (WiFi.status() == WL_CONNECTED) {
    WiFiClient client;
    HTTPClient http;
    http.begin(client, "http://leoplng.ru:25580/update");
    http.addHeader("id", ID);
    String postData = String(t) + "," + String(h) + "," + String(p);
    http.POST(postData);
    http.end();
  }
  delay(60000);
}
