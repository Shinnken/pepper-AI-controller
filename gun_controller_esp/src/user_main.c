#include "osapi.h"
#include "user_interface.h"
#include "espconn.h"
#include "mem.h"
#include "user_config.h"

static os_timer_t ptimer;
static struct espconn http_conn;
static esp_tcp http_tcp;

/******************************************************************************
 * FunctionName : user_rf_cal_sector_set
 * Description  : SDK just reversed 4 sectors, used for rf init data and paramters.
 *                We add this function to force users to set rf cal sector, since
 *                we don't know which sector is free in user's application.
 *                sector map for last several sectors : ABBBCDDD
 *                A : rf cal
 *                B : at parameters
 *                C : rf init data
 *                D : sdk parameters
 * Parameters   : none
 * Returns      : rf cal sector
*******************************************************************************/
uint32 ICACHE_FLASH_ATTR
user_rf_cal_sector_set(void)
{
    enum flash_size_map size_map = system_get_flash_size_map();
    uint32 rf_cal_sec = 0;

    switch (size_map) {
        case FLASH_SIZE_4M_MAP_256_256:
            rf_cal_sec = 128 - 5;
            break;

        case FLASH_SIZE_8M_MAP_512_512:
            rf_cal_sec = 256 - 5;
            break;

        case FLASH_SIZE_16M_MAP_512_512:
        case FLASH_SIZE_16M_MAP_1024_1024:
            rf_cal_sec = 512 - 5;
            break;

        case FLASH_SIZE_32M_MAP_512_512:
        case FLASH_SIZE_32M_MAP_1024_1024:
            rf_cal_sec = 1024 - 5;
            break;

        case FLASH_SIZE_64M_MAP_1024_1024:
            rf_cal_sec = 2048 - 5;
            break;
        case FLASH_SIZE_128M_MAP_1024_1024:
            rf_cal_sec = 4096 - 5;
            break;
        default:
            rf_cal_sec = 0;
            break;
    }
    return rf_cal_sec;
}

static os_timer_t fire_led_timer;
static uint8_t fire_blink_count = 0;

void trigger_off(void *arg)
{
    GPIO_OUTPUT_SET(NERF_TRIGGER_PIN, 0);  // Turn off trigger
    os_printf("Nerf gun trigger OFF\n");
    
    // Stop firing LED blinking and turn LED off
    os_timer_disarm(&fire_led_timer);
    GPIO_OUTPUT_SET(STATUS_LED_PIN, 1);  // Turn off LED (inverted logic)
    fire_blink_count = 0;
}

void fire_led_blink(void *arg)
{
    static uint8_t led_state = 0;
    
    if (fire_blink_count < 10) {  // Blink 5 times (10 state changes)
        if (led_state) {
            GPIO_OUTPUT_SET(STATUS_LED_PIN, 1);  // Turn off LED (inverted logic)
        } else {
            GPIO_OUTPUT_SET(STATUS_LED_PIN, 0);  // Turn on LED (inverted logic)
        }
        led_state ^= 1;
        fire_blink_count++;
        
        // Continue blinking every 50ms for fast blink effect
        os_timer_arm(&fire_led_timer, 50, 0);
    } else {
        // Finished blinking, turn LED off
        GPIO_OUTPUT_SET(STATUS_LED_PIN, 1);  // Turn off LED (inverted logic)
        fire_blink_count = 0;
    }
}

void fire_nerf_gun(void)
{
    os_printf("Firing nerf gun!\n");
    
    // Turn on trigger
    GPIO_OUTPUT_SET(NERF_TRIGGER_PIN, 1);
    
    // Start LED firing blink sequence
    fire_blink_count = 0;
    os_timer_disarm(&fire_led_timer);
    os_timer_setfn(&fire_led_timer, (os_timer_func_t *)fire_led_blink, NULL);
    os_timer_arm(&fire_led_timer, 50, 0);  // Start immediately
    
    // Set timer to turn off trigger after duration
    static os_timer_t trigger_timer;
    os_timer_disarm(&trigger_timer);
    os_timer_setfn(&trigger_timer, (os_timer_func_t *)trigger_off, NULL);
    os_timer_arm(&trigger_timer, NERF_TRIGGER_DURATION, 0);
}

void fire_nerf_gun_half(void)
{
    os_printf("Firing nerf gun (half duration)!\n");
    
    // Turn on trigger
    GPIO_OUTPUT_SET(NERF_TRIGGER_PIN, 1);
    
    // Start LED firing blink sequence (shorter for half fire)
    fire_blink_count = 0;
    os_timer_disarm(&fire_led_timer);
    os_timer_setfn(&fire_led_timer, (os_timer_func_t *)fire_led_blink, NULL);
    os_timer_arm(&fire_led_timer, 50, 0);  // Start immediately
    
    // Set timer to turn off trigger after HALF duration
    static os_timer_t trigger_timer_half;
    os_timer_disarm(&trigger_timer_half);
    os_timer_setfn(&trigger_timer_half, (os_timer_func_t *)trigger_off, NULL);
    os_timer_arm(&trigger_timer_half, NERF_TRIGGER_DURATION / 2, 0);
}

void ICACHE_FLASH_ATTR http_recv_cb(void *arg, char *data, unsigned short length)
{
    struct espconn *conn = (struct espconn *)arg;
    
    os_printf("Received HTTP request: %s\n", data);
    
    char response[512];
    bool should_fire = false;
    
    // Check if this is a fire request
    if (os_strstr(data, "GET /fire_half") != NULL) {
        should_fire = true;
        fire_nerf_gun_half();
        os_sprintf(response, 
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: application/json\r\n"
            "Access-Control-Allow-Origin: *\r\n"
            "Connection: close\r\n"
            "\r\n"
            "{\"status\":\"fired_half\",\"message\":\"Nerf gun fired at half duration!\"}\r\n");
    } else if (os_strstr(data, "GET /fire") != NULL) {
        should_fire = true;
        fire_nerf_gun();
        os_sprintf(response, 
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: application/json\r\n"
            "Access-Control-Allow-Origin: *\r\n"
            "Connection: close\r\n"
            "\r\n"
            "{\"status\":\"fired\",\"message\":\"Nerf gun fired successfully!\"}\r\n");
    } else if (os_strstr(data, "GET /status") != NULL) {
        os_sprintf(response, 
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: application/json\r\n"
            "Access-Control-Allow-Origin: *\r\n"
            "Connection: close\r\n"
            "\r\n"
            "{\"status\":\"ready\",\"message\":\"Nerf gun is ready to fire\"}\r\n");
    } else {
        os_sprintf(response, 
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/html\r\n"
            "Access-Control-Allow-Origin: *\r\n"
            "Connection: close\r\n"
            "\r\n"
            "<html><body>"
            "<h1>ESP WiFi Nerf Gun Controller</h1>"
            "<p>Available endpoints:</p>"
            "<ul>"
            "<li><a href=\"/fire\">POST/GET /fire</a> - Fire the nerf gun</li>"
            "<li><a href=\"/fire_half\">POST/GET /fire_half</a> - Fire the nerf gun (half duration)</li>"
            "<li><a href=\"/status\">GET /status</a> - Check status</li>"
            "</ul>"
            "</body></html>\r\n");
    }
    
    espconn_send(conn, (uint8_t *)response, os_strlen(response));
}

void ICACHE_FLASH_ATTR http_sent_cb(void *arg)
{
    struct espconn *conn = (struct espconn *)arg;
    espconn_disconnect(conn);
}

void ICACHE_FLASH_ATTR http_discon_cb(void *arg)
{
    os_printf("HTTP client disconnected\n");
}

void ICACHE_FLASH_ATTR http_connect_cb(void *arg)
{
    struct espconn *conn = (struct espconn *)arg;
    
    os_printf("HTTP client connected from: %d.%d.%d.%d:%d\n", 
        conn->proto.tcp->remote_ip[0],
        conn->proto.tcp->remote_ip[1], 
        conn->proto.tcp->remote_ip[2],
        conn->proto.tcp->remote_ip[3],
        conn->proto.tcp->remote_port);
    
    espconn_regist_recvcb(conn, http_recv_cb);
    espconn_regist_sentcb(conn, http_sent_cb);
    espconn_regist_disconcb(conn, http_discon_cb);
}

void ICACHE_FLASH_ATTR wifi_event_cb(System_Event_t *evt)
{
    switch (evt->event) {
        case EVENT_STAMODE_CONNECTED:
            os_printf("Connected to WiFi\n");
            break;
            
        case EVENT_STAMODE_GOT_IP:
            os_printf("Got IP: %d.%d.%d.%d\n",
                IP2STR(&evt->event_info.got_ip.ip));
            
            // Start HTTP server
            http_conn.type = ESPCONN_TCP;
            http_conn.state = ESPCONN_NONE;
            http_tcp.local_port = HTTP_SERVER_PORT;
            http_conn.proto.tcp = &http_tcp;
            
            espconn_regist_connectcb(&http_conn, http_connect_cb);
            espconn_accept(&http_conn);
            
            os_printf("HTTP server started on port %d\n", HTTP_SERVER_PORT);
            break;
            
        case EVENT_STAMODE_DISCONNECTED:
            os_printf("Disconnected from WiFi\n");
            break;
            
        default:
            break;
    }
}

void blinky(void *arg)
{
	static uint8_t state = 0;

	if (state) {
		GPIO_OUTPUT_SET(2, 1);
	} else {
		GPIO_OUTPUT_SET(2, 0);
	}
	state ^= 1;
}

void ICACHE_FLASH_ATTR user_init(void)
{
    gpio_init();

    uart_init(115200, 115200);
    os_printf("SDK version:%s\n", system_get_sdk_version());
    os_printf("ESP WiFi Nerf Gun Controller starting...\n");

    // Configure nerf trigger pin
    PIN_FUNC_SELECT(PERIPHS_IO_MUX_MTDI_U, FUNC_GPIO12);  // GPIO12
    GPIO_OUTPUT_SET(NERF_TRIGGER_PIN, 0);  // Initially off
    
    // Configure LED pin (GPIO2)
    PIN_FUNC_SELECT(PERIPHS_IO_MUX_GPIO2_U, FUNC_GPIO2);

    // Set up WiFi
    wifi_set_opmode(STATION_MODE);
    
    struct station_config sta_config;
    os_memset(&sta_config, 0, sizeof(struct station_config));
    
    // TODO: Replace with your WiFi credentials
    os_sprintf((char*)sta_config.ssid, WIFI_SSID);
    os_sprintf((char*)sta_config.password, WIFI_PASSWORD);
    
    wifi_station_set_config(&sta_config);
    wifi_set_event_handler_cb(wifi_event_cb);
    wifi_station_connect();

    // Start status LED blinking
    os_timer_disarm(&ptimer);
    os_timer_setfn(&ptimer, (os_timer_func_t *)blinky, NULL);
    os_timer_arm(&ptimer, 1000, 1);  // Blink every second
    
    os_printf("ESP WiFi Nerf Gun Controller initialized\n");
}
