#include <WiFiNINA.h>
#include <PubSubClient.h>
#include <EduIntro.h>

#define DHT11_PIN A0
#define LED_PIN 3
#define CONTROLLER_ID "1" //unikalne ID przypiasane urzadzeniu, nadrukowane na obudowie

const char* ssid = "IotNetwork";
const char* password = "akkm1234";
const char* mqtt_server = "192.168.2.1";
const int mqtt_port = 1883;

const char* topic_read_temp = "controllers/" CONTROLLER_ID "/read-temp";
const char* topic_set_temp = "controllers/" CONTROLLER_ID "/set-temp";

const long REPORT_INTERVAL = 5000;
const long SERVER_TIMEOUT = 60000;

const int MIN_TEMP = 10;
const int HYSTERESIS = 1;

int target_temp = 0;
int current_temp = 0;
unsigned long lastReport = 0;
unsigned long lastServerMsg = 0;

WiFiClient wifiClient;
PubSubClient client(wifiClient);
DHT11 dht11(DHT11_PIN);

void callback(char* topic, byte* payload, unsigned int length) {
  String msg = "";
  for (unsigned int i = 0; i < length; i++) {
    msg += (char)payload[i];
  }

  //po odebraniu wiadomosci ustal zadana temperature i zresetuj watchdoga serwera
  lastServerMsg = millis();
  target_temp = msg.toInt();
  Serial.println(String(CONTROLLER_ID) + " target temp: " + target_temp);
}

void connectWiFi(){
  while (WiFi.status() != WL_CONNECTED) {
    int status = WiFi.begin(ssid, password);
    Serial.print("Connection Status: ");
    Serial.println(status); // 4 = WL_CONNECT_FAILED, 3 = WL_CONNECTED, 1 = WL_NO_SSID_AVAIL
    delay(1000);
  }
}

void connectMQTT() {
  while (!client.connected()) {
    Serial.print("Attempting to connect to mqtt broker at: ");
    Serial.print(mqtt_server);
    Serial.print(":");
    Serial.println(mqtt_port);
    if(client.connect(CONTROLLER_ID)) {
      client.subscribe(topic_set_temp);
    }
    delay(1000);
  }
  Serial.println("MQTT connected");
}

void setup() {
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  
  Serial.begin(9600);
  
  connectWiFi();
  
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
  connectMQTT();

  lastServerMsg = millis();
}

void loop() {

  if (WiFi.status() != WL_CONNECTED) {
    Serial.print("Wifi connection lost, attempting to reconnect");
    connectWiFi();
  }

  if (!client.loop()) {
    Serial.print("MQTT connection lost, attempting to reconnect");
    connectMQTT();
  }
  

  dht11.update();
  current_temp = dht11.readCelsius();
  unsigned long now = millis();

  // wyslij cykliczny raport ze zmierzona temperatura
  if (now - lastReport > REPORT_INTERVAL) {
    lastReport = now;
    Serial.println(String(CONTROLLER_ID) + " measured temp: " + current_temp);
    client.publish(topic_read_temp, String(current_temp).c_str());
  }

  // zmniejsz temperature do minimum, jesli nie bylo wiadomosci od serwera
  if (now - lastServerMsg > SERVER_TIMEOUT) {
    target_temp = MIN_TEMP;
  }

  // regulacja zadanej temperatury wraz z histereza
  if (current_temp >= target_temp) {
    analogWrite(LED_PIN, 0);
    Serial.println("Temp goal met, turning the heating off");
  } else if (current_temp <= (target_temp - HYSTERESIS)){
    analogWrite(LED_PIN, 255);
    Serial.println("Temp below set-temp, turning the heating on");
  }
}


