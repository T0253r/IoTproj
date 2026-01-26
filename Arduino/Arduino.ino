#include <WiFiNINA.h>
#include <PubSubClient.h>
#include <EduIntro.h>

#define DHT11_PIN 5
#define LED_PIN 3
#define CONTROLLER_ID "1" //unikalne ID przypiasane urzadzeniu, nadrukowane na obudowie

const char* ssid = "IotNetwork";
const char* password = "akkm1234";
const char* mqtt_server = "192.168.2.1";
const int mqtt_port = 1883;

const char* topic_curr_temp = "controllers/" CONTROLLER_ID "/curr-temp";
const char* topic_target_temp = "controllers/" CONTROLLER_ID "/target-temp";

const long REPORT_INTERVAL = 5000;
const long SERVER_TIMEOUT = 60000;
const unsigned long RECONNECT_INTERVAL = 2000;

const int MIN_TEMP = 10;
const int HYSTERESIS = 1;

int target_temp = MIN_TEMP;
int current_temp = 0;
unsigned long lastReport = 0;
unsigned long lastServerMsg = 0;
unsigned long lastConnAttempt = 0;

WiFiClient wifiClient;
PubSubClient client(wifiClient);
DHT11 dht11(DHT11_PIN);

void callback(char* topic, byte* payload, unsigned int length) {
  //Parsowanie wiadomosci i reset watchdoga serwera
  String msg = "";
  for (unsigned int i = 0; i < length; i++) {
    msg += (char)payload[i];
  }

  lastServerMsg = millis();
  target_temp = max(MIN_TEMP, msg.toInt());
  Serial.println("Received message with target temp");
  Serial.println(String(CONTROLLER_ID) + " target temp: " + target_temp);
}

void maintainConnections() {
  if (WiFi.status() != WL_CONNECTED) {
    if (millis() - lastConnAttempt > RECONNECT_INTERVAL) {
      Serial.println("Attempting to connect to Wifi");
      lastConnAttempt = millis();
      int status = WiFi.begin(ssid, password);
      Serial.print("Wifi status: ");
      Serial.println(status);
    }
    return;
  }

  if (!client.connected()) {
    if (millis() - lastConnAttempt > RECONNECT_INTERVAL) {
      Serial.println("Attempting to connect to mqtt broker");
      lastConnAttempt = millis();
      if (client.connect(CONTROLLER_ID)) {
        Serial.println("Connected to mqtt broker");
        client.subscribe(topic_target_temp);
      } else {
          Serial.print("Failed, rc=");
          Serial.println(client.state());
      }
    }
  } else {
    client.loop();
  }
}

void setup() {
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  Serial.begin(9600);
  Serial.println("Serial communication started");
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
  lastServerMsg = millis();
}

void loop() {

  maintainConnections();
  
  dht11.update();
  current_temp = dht11.readCelsius();
  unsigned long now = millis();

  // Raportowanie temperatury
  if (now - lastReport > REPORT_INTERVAL) {
    lastReport = now;
    Serial.println(String(CONTROLLER_ID) + " measured temp: " + current_temp);
    Serial.println("Attempting to publish measured temp");
    client.publish(topic_curr_temp, String(current_temp).c_str());
  }

  // Watchdog serwera
  if (now - lastServerMsg > SERVER_TIMEOUT) {
    Serial.println("Serwer inactive, reducing temp to min");
    target_temp = MIN_TEMP;
  }

  // Regulacja temperatury
  if (current_temp >= target_temp) {
    analogWrite(LED_PIN, 0);
  } else if (current_temp <= (target_temp - HYSTERESIS)){
    analogWrite(LED_PIN, 255);
  }
}


