#include <Arduino.h>

#include "esp_camera.h"
#include <WiFi.h>
#include "esp_http_server.h"

// === UZUPEŁNIJ DANE WIFI 2.4 GHz ===
static const char *WIFI_SSID = "DrogaMleczna";
static const char *WIFI_PASSWORD = "3o4$NczTFPJ6ty3C";

// ESP32-CAM (AI Thinker) pin map
#define PWDN_GPIO_NUM 32
#define RESET_GPIO_NUM -1
#define XCLK_GPIO_NUM 0
#define SIOD_GPIO_NUM 26
#define SIOC_GPIO_NUM 27

#define Y9_GPIO_NUM 35
#define Y8_GPIO_NUM 34
#define Y7_GPIO_NUM 39
#define Y6_GPIO_NUM 36
#define Y5_GPIO_NUM 21
#define Y4_GPIO_NUM 19
#define Y3_GPIO_NUM 18
#define Y2_GPIO_NUM 5
#define VSYNC_GPIO_NUM 25
#define HREF_GPIO_NUM 23
#define PCLK_GPIO_NUM 22

static httpd_handle_t s_httpd = nullptr;

static const char INDEX_HTML[] PROGMEM = R"HTML(
<!doctype html>
<html lang="pl">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>ESP32-CAM</title>
    <style>
      body { font-family: sans-serif; margin: 16px; }
      img { max-width: 100%; height: auto; }
      .row { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
      a { font-size: 16px; }
    </style>
  </head>
  <body>
    <h2>ESP32-CAM</h2>
    <div class="row">
      <a href="/jpg">Pobierz snapshot (/jpg)</a>
      <a href="/stream">Podgląd MJPEG (/stream)</a>
    </div>
    <p>Podgląd:</p>
    <img src="/stream" alt="stream" />
  </body>
</html>
)HTML";

static esp_err_t handle_index(httpd_req_t *req) {
  httpd_resp_set_type(req, "text/html; charset=utf-8");
  httpd_resp_set_hdr(req, "Cache-Control", "no-store");
  return httpd_resp_send(req, INDEX_HTML, HTTPD_RESP_USE_STRLEN);
}

static esp_err_t handle_jpg(httpd_req_t *req) {
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    httpd_resp_send_err(req, HTTPD_500_INTERNAL_SERVER_ERROR, "Camera capture failed");
    return ESP_FAIL;
  }

  httpd_resp_set_type(req, "image/jpeg");
  httpd_resp_set_hdr(req, "Cache-Control", "no-store");
  esp_err_t res = httpd_resp_send(req, reinterpret_cast<const char *>(fb->buf), fb->len);

  esp_camera_fb_return(fb);
  return res;
}

static esp_err_t handle_stream(httpd_req_t *req) {
  static const char *STREAM_CONTENT_TYPE = "multipart/x-mixed-replace;boundary=frame";
  static const char *BOUNDARY = "\r\n--frame\r\n";
  static const char *PART = "Content-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n";

  httpd_resp_set_type(req, STREAM_CONTENT_TYPE);
  httpd_resp_set_hdr(req, "Cache-Control", "no-store");

  while (true) {
    camera_fb_t *fb = esp_camera_fb_get();
    if (!fb) {
      // Spróbuj ponownie — zamiast natychmiast kończyć połączenie.
      delay(10);
      continue;
    }

    char part_buf[128];
    int part_len = snprintf(part_buf, sizeof(part_buf), PART, fb->len);

    esp_err_t res = httpd_resp_send_chunk(req, BOUNDARY, strlen(BOUNDARY));
    if (res == ESP_OK) {
      res = httpd_resp_send_chunk(req, part_buf, part_len);
    }
    if (res == ESP_OK) {
      res = httpd_resp_send_chunk(req, reinterpret_cast<const char *>(fb->buf), fb->len);
    }
    if (res == ESP_OK) {
      res = httpd_resp_send_chunk(req, "\r\n", 2);
    }

    esp_camera_fb_return(fb);

    if (res != ESP_OK) {
      break; // klient się rozłączył lub błąd sieci
    }

    // Regulacja FPS (mniej WDT / mniej obciążenia)
    delay(30);
  }

  // Zakończ chunked response
  httpd_resp_send_chunk(req, nullptr, 0);
  return ESP_OK;
}

static void start_http_server() {
  httpd_config_t config = HTTPD_DEFAULT_CONFIG();
  config.server_port = 80;
  config.max_uri_handlers = 8;

  if (httpd_start(&s_httpd, &config) != ESP_OK) {
    Serial.println("[HTTP] Failed to start server");
    return;
  }

  httpd_uri_t uri_index = {
      .uri = "/",
      .method = HTTP_GET,
      .handler = handle_index,
      .user_ctx = nullptr,
  };

  httpd_uri_t uri_jpg = {
      .uri = "/jpg",
      .method = HTTP_GET,
      .handler = handle_jpg,
      .user_ctx = nullptr,
  };

  httpd_uri_t uri_stream = {
      .uri = "/stream",
      .method = HTTP_GET,
      .handler = handle_stream,
      .user_ctx = nullptr,
  };

  httpd_register_uri_handler(s_httpd, &uri_index);
  httpd_register_uri_handler(s_httpd, &uri_jpg);
  httpd_register_uri_handler(s_httpd, &uri_stream);
  Serial.println("[HTTP] Server started");
}

static bool init_camera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;
  config.pin_d0       = Y2_GPIO_NUM;
  config.pin_d1       = Y3_GPIO_NUM;
  config.pin_d2       = Y4_GPIO_NUM;
  config.pin_d3       = Y5_GPIO_NUM;
  config.pin_d4       = Y6_GPIO_NUM;
  config.pin_d5       = Y7_GPIO_NUM;
  config.pin_d6       = Y8_GPIO_NUM;
  config.pin_d7       = Y9_GPIO_NUM;
  config.pin_xclk     = XCLK_GPIO_NUM;
  config.pin_pclk     = PCLK_GPIO_NUM;
  config.pin_vsync    = VSYNC_GPIO_NUM;
  config.pin_href     = HREF_GPIO_NUM;

  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;

  config.pin_pwdn     = PWDN_GPIO_NUM;
  config.pin_reset    = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  if (psramFound()) {
    config.frame_size   = FRAMESIZE_HD;
    config.jpeg_quality = 12;
    config.fb_count     = 2;
    config.fb_location  = CAMERA_FB_IN_PSRAM;
    config.grab_mode    = CAMERA_GRAB_LATEST;
  } else {
    config.frame_size   = FRAMESIZE_QVGA;
    config.jpeg_quality = 14;
    config.fb_count     = 1;
    config.fb_location  = CAMERA_FB_IN_DRAM;
    config.grab_mode    = CAMERA_GRAB_WHEN_EMPTY;
  }

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("[CAM] Init failed 0x%x\n", err);
    return false;
  }

  sensor_t *s = esp_camera_sensor_get();
  if (s) {
    s->set_framesize(s, config.frame_size);
  }

  Serial.println("[CAM] Ready");
  return true;
}

static void connect_wifi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.printf("[WiFi] Connecting to %s", WIFI_SSID);

  uint32_t start_ms = millis();
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print('.');
    if (millis() - start_ms > 20000) {
      Serial.println("\n[WiFi] Connect timeout");
      break;
    }
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("\n[WiFi] Connected, IP: %s\n", WiFi.localIP().toString().c_str());
  }
}

void setup() {
  Serial.begin(115200);
  Serial.setDebugOutput(false);
  delay(200);

  if (String(WIFI_SSID) == "YOUR_WIFI_SSID") {
    Serial.println("[CFG] Ustaw WIFI_SSID/WIFI_PASSWORD w src/main.cpp");
  }

  connect_wifi();
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[WiFi] Brak polaczenia - HTTP nie wystartuje");
    return;
  }

  if (!init_camera()) {
    return;
  }

  start_http_server();
  Serial.println("[READY] Otworz w przegladarce: http://<IP>/");
}

void loop() {
  // httpd działa w tle; nic nie trzeba robić w loop().
  delay(1000);
}