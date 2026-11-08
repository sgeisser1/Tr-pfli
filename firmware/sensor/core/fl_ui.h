/*
 * fluidi – Bedienung: LED-Muster L1..L17, Farbregeln, periodische Anzeigen und Tasterauswertung
 * (PROTOCOL.md Kap. 10, D-010 LED-Farben, REQ-UI-01..07). Plattformneutral, zeitgesteuert ueber now_ms.
 */
#ifndef FL_UI_H
#define FL_UI_H
#include <stdint.h>
#include <stdbool.h>

/* Farben als Bitmaske R=1, G=2, B=4 (Gelb = Rot + Gruen, D-010) */
enum { FL_COL_OFF = 0, FL_COL_RED = 1, FL_COL_GREEN = 2, FL_COL_YELLOW = 3, FL_COL_BLUE = 4 };

typedef enum {
    FL_LED_NONE = 0,
    FL_LED_L1_SENT, FL_LED_L2_BUFFERED, FL_LED_L3_HEARTBEAT, FL_LED_L4_PAIRING, FL_LED_L5_SAS,
    FL_LED_L6_CONNECTED, FL_LED_L7_PAIR_FAIL, FL_LED_L8_WATER, FL_LED_L9_BATT_LOW, FL_LED_L10_ERROR,
    FL_LED_L10B_ERROR_BTN, FL_LED_L11_START_OK, FL_LED_L11_START_FAIL, FL_LED_L11_UNPAIRED,
    FL_LED_L12_3S, FL_LED_L13_ARMED_HOLD, FL_LED_L13_CONFIRM_WIN, FL_LED_L14_RESET, FL_LED_L15_UNPAIRED_BTN,
    FL_LED_L16_IDENTIFY, FL_LED_L17_OTA_OK, FL_LED_L17_OTA_REVERT, FL_LED_UV_BTN, FL_LED_UNPAIRED_2Y,
#if defined(FLUIDI_TESTFW) && FLUIDI_TESTFW
    FL_LED_TF_START,      /* Testfirmware: Startsignal Rot/Gruen abwechselnd 3 x (Anhang A, ANNAHME 100 ms) */
    FL_LED_TF_ACK,        /* Testfirmware: Tastersequenz erkannt, Testaktion folgt */
#endif
    FL_LED_COUNT
} fl_led_pattern_t;

/* FW-4 (PINMAP Rev B): LED nur in Pulsen <= 5 ms mit >= 5 ms Pause (Software-Takt, Standby dazwischen).
 * Schritte bis FL_LED_BLOCH_MS: gleiche Lichtmenge (Summe der Pulse = on_ms, Folge laenger, Pause danach kuerzer)
 * -> gleiche wahrgenommene Helligkeit (Zeitsummation des Auges, ANNAHME kritische Dauer >= 50 ms).
 * Laengere Schritte: gleiche Dauer, Tastgrad 50 %. */
#define FL_LED_PULSE_MS 5u
#define FL_LED_PAUSE_MS 5u
#define FL_LED_BLOCH_MS 50u

typedef struct {
    uint8_t  col;
    uint16_t on_ms;
    uint16_t off_ms;
} fl_led_step_t;

typedef struct {
    const fl_led_step_t *steps;
    uint8_t  n, idx;
    bool     on;             /* Schritt in der Leuchtphase (Pulsfolge laeuft) */
    bool     lit;            /* LED gerade an (Puls <= FL_LED_PULSE_MS, FW-4) */
    uint16_t off_eff;        /* Pause nach der Pulsfolge (um die Verlaengerung gekuerzt) */
    uint32_t span_end;       /* Ende der Pulsfolge des aktuellen Schritts */
    uint16_t repeats;        /* verbleibende Wiederholungen (0xFFFF = bis Stopp) */
    uint16_t gap_ms;         /* Pause zwischen Wiederholungen */
    uint32_t t_next;         /* naechster Schaltzeitpunkt */
    uint32_t t_end;          /* 0 = kein Zeitlimit */
    fl_led_step_t sas[5];    /* dynamische Farbfolge (L5) */
    fl_led_step_t buf[4];    /* Kopie des Musters mit spannungsabhaengigen Farben */
    fl_led_pattern_t active;
    uint8_t  out;            /* aktuell auszugebende Farbe */
    uint32_t on_ms_total;    /* Statistik led_ms (INFO) */
} fl_led_t;

void fl_led_init(fl_led_t *l);
/* Muster starten. vdd_mv = letzter Lastwert: Blau nur ab 2650 mV, sonst Ersatzfarbe (Kap. 10.1).
 * Rueckgabe false, wenn wegen Unterspannung (< 2400 mV, ausser FL_LED_UV_BTN) unterdrueckt. */
bool fl_led_play(fl_led_t *l, fl_led_pattern_t p, uint32_t now_ms, uint16_t vdd_mv, uint16_t duration_s);
void fl_led_play_sas(fl_led_t *l, const uint8_t digits[5], uint32_t now_ms, uint32_t max_ms);
void fl_led_stop(fl_led_t *l);
/* Fortschalten; liefert naechste Frist (0 = kein Muster aktiv). l->out ist die zu setzende Farbe. */
uint32_t fl_led_tick(fl_led_t *l, uint32_t now_ms);
bool fl_led_busy(const fl_led_t *l);
/* Mittlere LED-Ladung je Muster in uC (3-mA-Regel, Kap. 10.2) – fuer Ladungsschaetzung */
uint32_t fl_led_charge_uc(uint32_t on_ms);

/* Periodische Anzeige pro Minute (Vorrang Fehler > Batterie tief > Giessen; max. 1 je Minute, REQ-UI-03) */
typedef struct {
    bool error, batt_low, water;
    bool water_led_enabled;
    bool time_valid;
    uint16_t minute_of_day;            /* Lokalzeit */
    uint16_t win_start, win_end;       /* led_window */
    uint32_t minute_counter;           /* fortlaufende Minute seit Start */
} fl_periodic_in_t;
fl_led_pattern_t fl_led_periodic(const fl_periodic_in_t *in);

/* ------------- Taster (Kap. 10.3) ------------- */
typedef enum {
    FL_BTN_EV_NONE = 0, FL_BTN_EV_SHORT, FL_BTN_EV_LONG, FL_BTN_EV_VLONG_ARMED, FL_BTN_EV_FACTORY_RESET,
    FL_BTN_EV_REACHED_3S, FL_BTN_EV_REACHED_10S, FL_BTN_EV_STUCK, FL_BTN_EV_UNSTUCK, FL_BTN_EV_ARM_EXPIRED
} fl_btn_event_t;

typedef struct {
    bool pressed, stuck, armed;
    uint32_t t_press, t_arm_end;
    bool m3, m10;
} fl_btn_t;

#define FL_BTN_DEBOUNCE_MS   50u
#define FL_BTN_SHORT_MAX_MS  1500u
#define FL_BTN_LONG_MIN_MS   3000u
#define FL_BTN_LONG_MAX_MS   8000u
#define FL_BTN_VLONG_MIN_MS  10000u
#define FL_BTN_STUCK_MS      30000u
#define FL_BTN_CONFIRM_MS    5000u

void fl_btn_init(fl_btn_t *b);
fl_btn_event_t fl_btn_edge(fl_btn_t *b, bool pressed, uint32_t now_ms);
fl_btn_event_t fl_btn_tick(fl_btn_t *b, uint32_t now_ms);
uint32_t fl_btn_next_deadline(const fl_btn_t *b);   /* 0 = keine */

#endif
