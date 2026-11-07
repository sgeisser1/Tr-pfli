/*
 * fluidi – CC2340: BLE-Anbindung (TI BLE5-Stack, BLEAppUtil-Framework, FreeRTOS) fuer core/fl_app.c.
 *
 * Ausfuehrungsmodell: Der gesamte Kern laeuft im Kontext des BLEAppUtil-Tasks (einziger Aufrufer). Ereignisse
 * (Verbindung, GATT-Schreiben, Advertising, Taster, Zeitgeber) werden per BLEAppUtil_invokeFunction bzw. als
 * BLEAppUtil-Ereignisse in diesen Kontext gebracht. Danach plant fl_app_process() den naechsten Weckzeitpunkt.
 * Grundlage: SDK examples/rtos/LP_EM_CC2340R5/ble/basic_ble (app_main.c, app_peripheral.c, simple_gatt_profile.c).
 *
 * GATT nach PROTOCOL.md Kap. 3: Dienst 0f740001-..., RX 0f740002-... (Write/WriteNoRsp), TX 0f740003-... (Notify).
 */
#include <string.h>
#include "ti_ble_config.h"
#include "ti/ble/app_util/framework/bleapputil_api.h"
#include "ti/ble/stack_util/icall/app/icall_ble_api.h"
#include "fl_app.h"
#include "fl_port.h"
#include "fl_platform.h"

/* ---------------- GATT-Dienst ---------------- */
/* 128-bit-UUIDs little-endian: Basis 0f74xxxx-f9fb-4a4d-9c3b-347f1f1affd5 */
#define FL_UUID128(x) 0xd5, 0xff, 0x1a, 0x1f, 0x7f, 0x34, 0x3b, 0x9c, 0x4d, 0x4a, 0xfb, 0xf9, (x) & 0xFF, ((x) >> 8) & 0xFF, 0x74, 0x0f
static const uint8 flSvcUUID[ATT_UUID_SIZE] = {FL_UUID128(0x0001)};
static const uint8 flRxUUID[ATT_UUID_SIZE]  = {FL_UUID128(0x0002)};
static const uint8 flTxUUID[ATT_UUID_SIZE]  = {FL_UUID128(0x0003)};

static const gattAttrType_t flService = {ATT_UUID_SIZE, flSvcUUID};
static uint8 flRxProps = GATT_PROP_WRITE | GATT_PROP_WRITE_NO_RSP;
static uint8 flTxProps = GATT_PROP_NOTIFY;
static uint8 flRxVal[1], flTxVal[1];
static gattCharCfg_t *flTxCfg;

static gattAttribute_t flAttrTbl[] = {
    GATT_BT_ATT(primaryServiceUUID, GATT_PERMIT_READ, (uint8 *)&flService),
    GATT_BT_ATT(characterUUID, GATT_PERMIT_READ, &flRxProps),
    GATT_ATT(flRxUUID, GATT_PERMIT_WRITE, flRxVal),
    GATT_BT_ATT(characterUUID, GATT_PERMIT_READ, &flTxProps),
    GATT_ATT(flTxUUID, 0, flTxVal),
    GATT_BT_ATT(clientCharCfgUUID, GATT_PERMIT_READ | GATT_PERMIT_WRITE, (uint8 *)&flTxCfg),
};
#define FL_ATTR_TX_VALUE 4

static uint16_t s_conn = LINKDB_CONNHANDLE_INVALID;
static uint16_t s_mtu = 23;

typedef struct { uint16_t len; uint8_t data[247]; } fl_rx_msg_t;

static void rx_in_ctx(char *p)
{
    fl_rx_msg_t *m = (fl_rx_msg_t *)p;
    fl_app_on_rx(m->data, m->len);
    fl_platform_reschedule();
}

static bStatus_t fl_read_cb(uint16_t conn, gattAttribute_t *a, uint8_t *v, uint16_t *len, uint16_t off, uint16_t max,
                            uint8_t method)
{
    (void)conn; (void)a; (void)v; (void)off; (void)max; (void)method;
    *len = 0;
    return ATT_ERR_READ_NOT_PERMITTED;
}

static bStatus_t fl_write_cb(uint16_t conn, gattAttribute_t *a, uint8_t *v, uint16_t len, uint16_t off, uint8_t method)
{
    if (a->type.len == ATT_BT_UUID_SIZE && BUILD_UINT16(a->type.uuid[0], a->type.uuid[1]) == GATT_CLIENT_CHAR_CFG_UUID)
        return GATTServApp_ProcessCCCWriteReq(conn, a, v, len, off, GATT_CLIENT_CFG_NOTIFY);
    if (a->type.len == ATT_UUID_SIZE && memcmp(a->type.uuid, flRxUUID, ATT_UUID_SIZE) == 0) {
        if (off != 0) return ATT_ERR_ATTR_NOT_LONG;
        if (len == 0 || len > 247) return ATT_ERR_INVALID_VALUE_SIZE;
        fl_rx_msg_t *m = (fl_rx_msg_t *)BLEAppUtil_malloc(sizeof(fl_rx_msg_t));
        if (!m) return ATT_ERR_INSUFFICIENT_RESOURCES;
        m->len = len;
        memcpy(m->data, v, len);
        BLEAppUtil_invokeFunction(rx_in_ctx, (char *)m);   /* Kern im BLEAppUtil-Kontext, Puffer wird freigegeben */
        return SUCCESS;
    }
    (void)method;
    return ATT_ERR_ATTR_NOT_FOUND;
}

static const gattServiceCBs_t flCBs = {fl_read_cb, fl_write_cb, NULL};

static bStatus_t fl_gatt_add(void)
{
    flTxCfg = (gattCharCfg_t *)ICall_malloc(sizeof(gattCharCfg_t) * MAX_NUM_BLE_CONNS);
    if (!flTxCfg) return bleMemAllocError;
    GATTServApp_InitCharCfg(LINKDB_CONNHANDLE_INVALID, flTxCfg);
    /* Sicherheitsstufe: keine Link-Layer-Sicherheit verlangt (PROTOCOL.md 3), Schutz liegt in den Frames */
    return GATTServApp_RegisterService(flAttrTbl, GATT_NUM_ATTRS(flAttrTbl), GATT_MAX_ENCRYPT_KEY_SIZE, &flCBs);
}

int fl_port_ble_send(const uint8_t *f, uint16_t len)
{
    attHandleValueNoti_t n;
    if (s_conn == LINKDB_CONNHANDLE_INVALID) return -1;
    if (!(GATTServApp_ReadCharCfg(s_conn, flTxCfg) & GATT_CLIENT_CFG_NOTIFY)) return -1;
    if (len > s_mtu - 3) return -1;
    n.pValue = (uint8 *)GATT_bm_alloc(s_conn, ATT_HANDLE_VALUE_NOTI, len, NULL);
    if (!n.pValue) return 1;                                   /* kein Puffer: spaeter erneut */
    n.handle = flAttrTbl[FL_ATTR_TX_VALUE].handle;
    n.len = len;
    memcpy(n.pValue, f, len);
    bStatus_t st = GATT_Notification(s_conn, &n, FALSE);
    if (st != SUCCESS) {
        GATT_bm_free((gattMsg_t *)&n, ATT_HANDLE_VALUE_NOTI);
        return (st == MSG_BUFFER_NOT_AVAIL || st == blePending || st == bleMemAllocError) ? 1 : -1;
    }
    return 0;
}

void fl_port_ble_disconnect(void)
{
    if (s_conn != LINKDB_CONNHANDLE_INVALID) BLEAppUtil_disconnect(s_conn);
}

uint16_t fl_port_ble_mtu(void) { return s_mtu; }

/* ---------------- Advertising ---------------- */
static uint8_t s_adv_handle = 0xFF;
static uint8_t s_adv_buf[31];
static bool s_adv_on;
/* Wie GAPADV_PARAMS_LEGACY_SCANN_CONN (gap_advertiser.h; dort fehlt im SDK 9.23 ein Komma nach .sid) */
static GapAdv_params_t s_adv_params = {
    .eventProps = GAP_ADV_PROP_CONNECTABLE | GAP_ADV_PROP_SCANNABLE | GAP_ADV_PROP_LEGACY,
    .primIntMin = 44000, .primIntMax = 44000,            /* 27.5 s in 0.625 ms; wird von fl_port_adv_set gesetzt */
    .primChanMap = GAP_ADV_CHAN_ALL, .peerAddrType = PEER_ADDRTYPE_PUBLIC_OR_PUBLIC_ID,
    .peerAddr = {0xaa, 0xaa, 0xaa, 0xaa, 0xaa, 0xaa}, .filterPolicy = GAP_ADV_AL_POLICY_ANY_REQ,
    .txPower = 0, .primPhy = GAP_ADV_PRIM_PHY_1_MBPS, .secPhy = GAP_ADV_SEC_PHY_1_MBPS, .sid = 0, .zeroDelay = 0};
static int8_t s_tx_dbm;

int fl_port_adv_set(const uint8_t *d, uint8_t len, uint32_t interval_ms, bool connectable, bool enable)
{
    if (s_adv_handle == 0xFF) return -1;
    if (s_adv_on) { GapAdv_disable(s_adv_handle); s_adv_on = false; }
    if (!enable) return 0;
    uint16_t props = GAP_ADV_PROP_LEGACY | (connectable ? (GAP_ADV_PROP_CONNECTABLE | GAP_ADV_PROP_SCANNABLE) : 0);
    uint32_t iv = interval_ms * 1000u / 625u;                  /* Einheit 0.625 ms */
    GapAdv_setParam(s_adv_handle, GAP_ADV_PARAM_PROPS, &props);
    GapAdv_setParam(s_adv_handle, GAP_ADV_PARAM_PRIMARY_INTERVAL_MIN, &iv);
    GapAdv_setParam(s_adv_handle, GAP_ADV_PARAM_PRIMARY_INTERVAL_MAX, &iv);
    GapAdv_setParam(s_adv_handle, GAP_ADV_PARAM_TX_POWER, &s_tx_dbm);
    if (d && len <= sizeof s_adv_buf) {
        GapAdv_prepareLoadByHandle(s_adv_handle, GAP_ADV_FREE_OPTION_DONT_FREE);
        memcpy(s_adv_buf, d, len);
        GapAdv_loadByHandle(s_adv_handle, GAP_ADV_DATA_TYPE_ADV, len, s_adv_buf);
    }
    BLEAppUtil_AdvStart_t start = {.enableOptions = GAP_ADV_ENABLE_OPTIONS_USE_MAX, .durationOrMaxEvents = 0};
    if (BLEAppUtil_advStart(s_adv_handle, &start) != SUCCESS) return -1;
    s_adv_on = true;
    return 0;
}

void fl_port_tx_power(int8_t dbm) { s_tx_dbm = dbm; }   /* gilt ab dem naechsten fl_port_adv_set (REQ-RF-03) */

void fl_port_ble_addr(uint8_t a[6]) { memcpy(a, GAP_GetDevAddress(TRUE), 6); }

/* ---------------- Ereignisse ---------------- */
static void adv_evt(uint32 event, BLEAppUtil_msgHdr_t *p)
{
    (void)p;
    if (event == BLEAPPUTIL_ADV_END) fl_app_on_adv_event();
}

static void conn_evt(uint32 event, BLEAppUtil_msgHdr_t *p)
{
    if (event == BLEAPPUTIL_LINK_ESTABLISHED_EVENT) {
        gapEstLinkReqEvent_t *e = (gapEstLinkReqEvent_t *)p;
        if (e->hdr.status == SUCCESS) {
            s_conn = e->connectionHandle; s_mtu = 23; s_adv_on = false;
            fl_platform_conn_vbat_reset();
            fl_app_on_connect();
        }
    } else if (event == BLEAPPUTIL_LINK_TERMINATED_EVENT) {
        s_conn = LINKDB_CONNHANDLE_INVALID;
        fl_app_on_disconnect();
    }
    fl_platform_reschedule();
}

static void gatt_evt(uint32 event, BLEAppUtil_msgHdr_t *p)
{
    if (event == BLEAPPUTIL_ATT_MTU_UPDATED_EVENT) {
        gattMsgEvent_t *g = (gattMsgEvent_t *)p;
        s_mtu = g->msg.mtuEvt.MTU;
    }
}

static void hci_evt(uint32 event, BLEAppUtil_msgHdr_t *p)
{
    (void)p;
    if (event == BLEAPPUTIL_HCI_NUM_OF_COMPLETED_PACKETS_EVENT_CODE) { fl_app_on_tx_ready(); fl_platform_reschedule(); }
}

static void conn_noti_evt(uint32 event, BLEAppUtil_msgHdr_t *p)
{
    (void)event; (void)p;
    fl_platform_conn_vbat_sample();           /* FW-5: Unterspannung in der Verbindung messen */
}

static BLEAppUtil_EventHandler_t hAdv = {BLEAPPUTIL_GAP_ADV_TYPE, adv_evt, BLEAPPUTIL_ADV_END};
static BLEAppUtil_EventHandler_t hConn = {BLEAPPUTIL_GAP_CONN_TYPE, conn_evt,
                                          BLEAPPUTIL_LINK_ESTABLISHED_EVENT | BLEAPPUTIL_LINK_TERMINATED_EVENT};
static BLEAppUtil_EventHandler_t hGatt = {BLEAPPUTIL_GATT_TYPE, gatt_evt, BLEAPPUTIL_ATT_MTU_UPDATED_EVENT};
static BLEAppUtil_EventHandler_t hHci = {BLEAPPUTIL_HCI_GAP_TYPE, hci_evt, BLEAPPUTIL_HCI_NUM_OF_COMPLETED_PACKETS_EVENT_CODE};
static BLEAppUtil_EventHandler_t hConnNoti = {BLEAPPUTIL_CONN_NOTI_TYPE, conn_noti_evt, BLEAPPUTIL_CONN_NOTI_CONN_EVENT_ALL};

/* ---------------- Start ---------------- */
BLEAppUtil_GeneralParams_t appMainParams = {
    .taskPriority = 1,
    .taskStackSize = 2048,                       /* Kern + Krypto (ECDH im Treiber) */
    .profileRole = (BLEAppUtil_Profile_Roles_e)(HOST_CONFIG),
    .addressMode = DEFAULT_ADDRESS_MODE,
    .deviceNameAtt = attDeviceName,
    .pDeviceRandomAddress = pRandomAddress,
};
BLEAppUtil_PeriCentParams_t appMainPeriCentParams = {
    .connParamUpdateDecision = DEFAULT_PARAM_UPDATE_REQ_DECISION,
    .gapBondParams = &gapBondParams,
};

static void crit_err(int32 code, void *info) { (void)code; (void)info; fl_platform_fatal(1); }

static void stack_ready(gapDeviceInitDoneEvent_t *d)
{
    (void)d;
    static uint8_t init_adv[31] = {2, 1, 6};
    BLEAppUtil_AdvInit_t ai = {.advDataLen = 3, .advData = init_adv, .scanRespDataLen = 0, .scanRespData = NULL,
                               .advParam = &s_adv_params};
    fl_gatt_add();
    BLEAppUtil_registerEventHandler(&hAdv);
    BLEAppUtil_registerEventHandler(&hConn);
    BLEAppUtil_registerEventHandler(&hGatt);
    BLEAppUtil_registerEventHandler(&hHci);
    BLEAppUtil_registerEventHandler(&hConnNoti);
    BLEAppUtil_registerConnNotifHandler(LINKDB_CONNHANDLE_ALL, GAP_CB_CONN_EVENT_ALL);
    BLEAppUtil_initAdvSet(&s_adv_handle, &ai);
    fl_platform_start_app();                     /* Kern starten (im BLEAppUtil-Kontext) */
}

void appMain(void)
{
    fl_platform_early_init();                     /* FW-6/FW-8: Pins in Ruhezustand, SWD/Pulls aus */
    BLEAppUtil_init(&crit_err, &stack_ready, &appMainParams, &appMainPeriCentParams);
}
