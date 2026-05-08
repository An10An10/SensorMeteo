#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <DHT.h>

WIFI_SSID = "WIFI_SSID"
WIFI_PASS = "WIFI_PASS"

#define DHTPIN 2     // Пин D4
DHT dht(DHTPIN, DHT11);

void setup() {
  Serial.begin(115200);
  dht.begin();
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) delay(500);
}

void loop() {
  delay(2000);
  float t = dht.readTemperature();
  float h = dht.readHumidity();
  
  if (isnan(t)) t = -1.0;
  if (isnan(h)) h = -1.0;

  if (WiFi.status() == WL_CONNECTED) {
    WiFiClient client;
    HTTPClient http;
    http.begin(client, "http://leoplng.ru:25580/update");
    http.addHeader("id", "101");
    String postData = String(t) + "," + String(h) + ",-1.0";
    http.POST(postData);
    http.end();
  }
  delay(60000);
}
