#include <WiFiNINA.h>
#include <PubSubClient.h>
#include <EduIntro.h>

#define DHT11_PIN A0
#define LED_PIN 3
#define CONNECTION_LOST_TIMEOUT 10000

#define ROOM_ID 1

#define CLIENT_ID ("room"+ String(ROOM_ID))
#define LISTEN (CLIENT_ID+"/listen")
#define SEND (CLIENT_ID+"/send")
#define LISTEN_ALL String("ping")



const char* ssid = "IotNetwork";
const char* password = "akkm1234";

const char* mqtt_server = "192.168.2.1";

WiFiClient wifiClient;
PubSubClient client(wifiClient);
DHT11 dht11(DHT11_PIN);
int target_temp;
unsigned long lastPingTime = 0;


void setupWifi() {
  Serial.print("Attempting to connect to SSID: ");
  Serial.println(ssid);

  // Check if the WiFi module is actually working
  if (WiFi.status() == WL_NO_MODULE) {
    Serial.println("Communication with WiFi module failed!");
    while (true);
  }

  while (WiFi.status() != WL_CONNECTED) {
    int status = WiFi.begin(ssid, password);
    Serial.print("Connection Status: ");
    Serial.println(status); // 4 = WL_CONNECT_FAILED, 1 = WL_NO_SSID_AVAIL
    delay(2000);
  }
  
  Serial.println("Connected to WiFi!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
}

void send_message(String message) {
  client.publish(SEND.c_str(), message.c_str());
}

void callback(char* topic, byte* payload, unsigned int length) {
  String msg = "";
  for (unsigned int i = 0; i < length; i++) {
    msg += (char)payload[i];
  }

  if (msg == "ping") {
    lastPingTime = millis();  // zresetuj licznik ping
  } else {
    target_temp = msg.toInt();
    send_message("OK " + String(target_temp));
  }
}

void reconnectMQTT() {
  while (!client.connected()) {
    if(client.connect(CLIENT_ID.c_str())) {
      client.subscribe(LISTEN.c_str());
      client.subscribe(LISTEN_ALL.c_str());
    }
    delay(500); 
  }
}

int getTemp() {
  dht11.update();
  return dht11.readCelsius();
}

void setup() {
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH);
  Serial.begin(9600);
  
  setupWifi();
  
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}

void calibrate_heating() {
  if(getTemp() >= target_temp) {
     analogWrite(LED_PIN, 0);
  }
  else {
    analogWrite(LED_PIN, 255);
  }
}

void loop() {
  if (!client.connected()) {
    reconnectMQTT();
  }

  client.loop();
  Serial.println("ping " + CLIENT_ID + " " + String(getTemp()) + " " + String(target_temp));  
  send_message("ping " + CLIENT_ID + " " + String(getTemp()) + " " + String(target_temp) );

  if (millis() - lastPingTime > 10000) { 
    target_temp = 0;
  }

  calibrate_heating();
  delay(1000);
}


